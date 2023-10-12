"""
    Debugging: Render video stream and annote the fixation coordinates.
"""

import cv2
import os
from datetime import datetime
import zmq
from msgpack import unpackb, packb
import numpy as np
import signal
from subprocess import Popen
import psutil
from threading import Thread

# A flag to indicate if the thread should exit
exit_thread = False


def cleanup_resources(p, context, req, sub):
    try:
        # Close ZMQ sockets
        req.close()
        sub.close()
        context.term()
        
        # Terminate the child process started by Popen
        p.terminate()
        p.wait(timeout=5)
        
        # Optional: Check for child processes and terminate them
        parent = psutil.Process(p.pid)
        for child in parent.children(recursive=True):
            child.terminate()
        gone, alive = psutil.wait_procs(parent.children(), timeout=5)
        
        # Forcefully terminate if not dead
        for p in alive:
            p.kill()

    except Exception as e:
        print(f"An error occurred during cleanup: {e}")

def recv_from_sub():
    topic = sub.recv_string()
    payload = unpackb(sub.recv())
    extra_frames = []
    while sub.get(zmq.RCVMORE):
        extra_frames.append(sub.recv())
    if extra_frames:
        payload['__raw_data__'] = extra_frames
    return topic, payload

def notify(notification):
    topic = 'notify.' + notification['subject']
    payload = packb(notification, use_bin_type=True)
    req.send_string(topic, flags=zmq.SNDMORE)
    req.send(payload)
    return req.recv_string()

# Function to handle termination signals
def signal_handler(signum, frame):
    global exit_thread
    print("Signal received, terminating child process.")
    exit_thread = True
    cleanup_resources(p, context, req, sub)


signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)

# Function for frame capture in a separate thread
def frame_capture_loop():
    global recent_world
    global gaze_x, gaze_y
    global exit_thread  

    while not exit_thread:  
        topic, msg = recv_from_sub()
        if topic == 'frame.world':
            if 'height' in msg and 'width' in msg and '__raw_data__' in msg:
                total_size = msg['height'] * msg['width'] * 3
                if total_size == len(msg['__raw_data__'][0]):
                    recent_world = np.frombuffer(msg['__raw_data__'][0], dtype=np.uint8).reshape(msg['height'], msg['width'], 3)
        elif topic.startswith('pupil.'):
            if 'norm_pos' in msg:
                gaze_x, gaze_y = msg['norm_pos']

try:
    # Start the Pupil capture program
    p = Popen(["python3", "pupil/pupil_src/main.py", "capture", "--hide-ui"], preexec_fn=os.setsid)

    # Networking and other initializations
    context = zmq.Context()
    addr = '127.0.0.1'
    req_port = "50020"
    req = context.socket(zmq.REQ)
    req.connect(f"tcp://{addr}:{req_port}")
    req.send_string('SUB_PORT')
    sub_port = req.recv_string()

    # More initializations
    sub = context.socket(zmq.SUB)
    sub.connect(f"tcp://{addr}:{sub_port}")
    sub.setsockopt_string(zmq.SUBSCRIBE, 'frame.')
    sub.setsockopt_string(zmq.SUBSCRIBE, 'pupil.')

    recent_world = None
    gaze_x, gaze_y = 0, 0

    # Start the frame capture loop in its own thread
    capture_thread = Thread(target=frame_capture_loop)
    capture_thread.daemon = True
    capture_thread.start()

    while not exit_thread:
        if recent_world is not None:
            cv2.imshow('World Frame', recent_world)
        
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            exit_thread = True  # set the flag
            break
        
        elif key == ord('s') and recent_world is not None:  # NEW: Add timestamp and coordinates

            timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')

            saved_frame = recent_world.copy()

            saved_gaze_x, saved_gaze_y = int(gaze_x * saved_frame.shape[1]), int(gaze_y * saved_frame.shape[0])

            cv2.circle(saved_frame, (saved_gaze_x, saved_gaze_y), 10, (255, 0, 0), -1)

            cv2.putText(saved_frame, f"Timestamp: {timestamp}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

            cv2.putText(saved_frame, f"Coordinates: ({saved_gaze_x}, {saved_gaze_y})", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

            filename = f'saved_frame_with_gaze_{timestamp}.png'
            filepath = os.path.join('saved_frames', filename)
            cv2.imwrite(filepath, saved_frame)


except KeyboardInterrupt:
    exit_thread = True  # set the flag
    capture_thread.join(timeout=1)  # join the thread with timeout
    print("Ctrl+C pressed, terminating child process.")
    p.terminate()
    raise KeyboardInterrupt

except Exception as e:
    exit_thread = True  # set the flag
    capture_thread.join(timeout=1)  # join the thread with timeout
    print("Ctrl+C pressed, terminating child process.")
    p.terminate()
    raise e

finally:
    exit_thread = True  # set the flag
    capture_thread.join(timeout=1)  # join the thread with a timeout
    print("Program terminated, terminating child process.")
    cleanup_resources(p, context, req, sub)
    cv2.destroyAllWindows()
    
