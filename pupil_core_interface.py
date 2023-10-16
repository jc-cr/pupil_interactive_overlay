import zmq
from msgpack import unpackb
import numpy as np
from threading import Thread
from subprocess import Popen
import os

class PupilCoreInterface:
    def __init__(self):
        self.context = zmq.Context()
        self.req = self.context.socket(zmq.REQ)
        self.sub = self.context.socket(zmq.SUB)
        self.req_port = "50020"
        self.addr = '127.0.0.1'
        self.exit_thread = False
        self.recent_world = None
        self.gaze_x, self.gaze_y = 0, 0
        self.p = None  # Process for Pupil capture program
        self.capture_thread = None  # Initialize the capture thread as None

    def connect(self):
        # Start the Pupil capture program
        self.p = Popen(["python3", "pupil/pupil_src/main.py", "capture", "--hide-ui"], preexec_fn=os.setsid)
        
        self.req.connect(f"tcp://{self.addr}:{self.req_port}")
        self.req.send_string('SUB_PORT')
        self.sub_port = self.req.recv_string()
        self.sub.connect(f"tcp://{self.addr}:{self.sub_port}")
        self.sub.setsockopt_string(zmq.SUBSCRIBE, 'frame.')
        self.sub.setsockopt_string(zmq.SUBSCRIBE, 'pupil.')

    def start_capture(self):
        '''
        Starts the frame capture thread         
        '''
        self.capture_thread = Thread(target=self._frame_capture_loop)
        self.capture_thread.daemon = True
        self.capture_thread.start()

    def _frame_capture_loop(self):
        while not self.exit_thread:
            topic = self.sub.recv_string()
            payload = unpackb(self.sub.recv())
            extra_frames = []
            while self.sub.get(zmq.RCVMORE):
                extra_frames.append(self.sub.recv())
            if extra_frames:
                payload['__raw_data__'] = extra_frames

            if topic == 'frame.world':
                if 'height' in payload and 'width' in payload and '__raw_data__' in payload:
                    total_size = payload['height'] * payload['width'] * 3
                    if total_size == len(payload['__raw_data__'][0]):
                        self.recent_world = np.frombuffer(payload['__raw_data__'][0], dtype=np.uint8).reshape(payload['height'], payload['width'], 3)

   def terminate(self):
    '''
    Cleans up the resources used by the Pupil Core interface
    '''
    self.exit_thread = True  # Signal to the capture thread to exit
    
    # Wait for the capture thread to finish if it's active
    if self.capture_thread and self.capture_thread.is_alive():
        self.capture_thread.join(timeout=1)
    
    # Close the ZMQ sockets
    try:
        self.req.setsockopt(zmq.LINGER, 0)  # Do not wait for pending messages to be sent
        self.req.close()
        
        self.sub.setsockopt(zmq.LINGER, 0)
        self.sub.close()
    except Exception as e:
        print(f"Exception while closing ZMQ sockets: {e}")
    
    # Terminate the ZMQ context
    self.context.term()
    
    # Terminate the Pupil capture process
    if self.p:
        try:
            self.p.terminate()
            self.p.wait(timeout=5)
        except Exception as e:
            print(f"Exception while terminating Pupil capture process: {e}")
