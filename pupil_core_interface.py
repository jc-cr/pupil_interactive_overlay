import zmq
import signal
from msgpack import unpackb
import numpy as np
from threading import Thread
from subprocess import Popen
import logging
import psutil
import os
import socket

class PupilCoreInterface:
    """
    This class provides an interface for the Pupil Capture program. It is responsible for starting the Pupil Capture program,
    connecting to its ZMQ sockets, and receiving the frame data. It exposes the following instance variables:
    - recent_world: The most recent frame of the world camera
    - gaze_x: The x-coordinate of the gaze point
    - gaze_y: The y-coordinate of the gaze point
    """
    def __init__(self):
        # Initialize logging
        logging.basicConfig(level=logging.INFO)

        # Update for dynamic paths
        self.dir_path = os.path.dirname(os.path.realpath(__file__))
        self.pupil_path = os.path.join(self.dir_path, "pupil", "pupil_src", "main.py")
        self.pupil_dir = os.path.dirname(self.pupil_path)

        #DEBUG: Print the paths
        logging.info(f"dir_path: {self.dir_path}")
        logging.info(f"pupil_path: {self.pupil_path}")
        logging.info(f"pupil_dir: {self.pupil_dir}")


        # Initialize other instance variables
        self.req_port = "50020"
        self.addr = '127.0.0.1'
        self.exit_thread = False
        self.recent_world = None
        self.gaze_x, self.gaze_y = 0, 0
        self.p = None
        self.capture_thread = None

        # Check for existing Pupil Core processes
        for proc in psutil.process_iter():
            try:
                if "pupil" in proc.name().lower():
                    logging.warning(f"Found an existing Pupil Core process: {proc.name()}, terminating it.")
                    proc.terminate()
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass

        # Check if the port is in use
        if self.check_port_in_use(self.req_port):
            raise RuntimeError(f"Port {self.req_port} is already in use. Cannot initialize PupilCoreInterface.")

    def check_port_in_use(self, port):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex(('localhost', int(port))) == 0

    def connect(self):
        try:
            # Initialize the ZMQ context and sockets
            self.context = zmq.Context()
            self.req = self.context.socket(zmq.REQ)
            self.sub = self.context.socket(zmq.SUB)

            if self.check_port_in_use(self.req_port):
                logging.error(f"Port {self.req_port} is already in use. Terminating.")
                self.terminate()
                return

            # Start the Pupil capture program
            self.p = Popen(["python3", self.pupil_path, "capture", "--hide-ui"], cwd=self.pupil_dir , preexec_fn=os.setsid)


            # Try connecting the REQ socket
            self.req.connect(f"tcp://{self.addr}:{self.req_port}")
            self.req.send_string('SUB_PORT')
            self.sub_port = self.req.recv_string()

            # Try connecting the SUB socket
            self.sub.connect(f"tcp://{self.addr}:{self.sub_port}")
            self.sub.setsockopt_string(zmq.SUBSCRIBE, 'frame.')
            self.sub.setsockopt_string(zmq.SUBSCRIBE, 'pupil.')

        except Exception as e:
            logging.error(f"Exception during connect: {e}")
            self.terminate()
            raise e

    def start_capture(self):
        '''
        Starts the frame capture thread         
        '''
        self.capture_thread = Thread(target=self._frame_capture_loop)
        self.capture_thread.daemon = True
        self.capture_thread.start()

    def _frame_capture_loop(self):
        while not self.exit_thread:
            if self.context is None:
                break  # Context is terminated, so exit the loop
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
        try:
            self.exit_thread = True

            if self.capture_thread and self.capture_thread.is_alive():
                self.capture_thread.join(timeout=1)

            if self.req:
                self.req.setsockopt(zmq.LINGER, 0)
                self.req.close()
                logging.info("REQ socket closed.")

            if self.sub:
                self.sub.setsockopt(zmq.LINGER, 0)
                self.sub.close()
                logging.info("SUB socket closed.")

            if self.context:
                self.context.term()
                logging.info("ZMQ context terminated.")
                self.context = None

            if self.p:
                os.killpg(os.getpgid(self.p.pid), signal.SIGKILL)  # Forcefully terminate the process group
                self.p.wait(timeout=5)  # Wait for the process to terminate
                logging.info(f"Terminated Pupil capture program with PID {self.p.pid}.")
                self.p = None

            logging.info("Successfully terminated all resources.")

        except Exception as e:
            logging.error(f"An exception occurred during termination: {e}")
            raise e
