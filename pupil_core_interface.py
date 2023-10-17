import zmq
import signal
from msgpack import unpackb
import msgpack
import numpy as np
from threading import Thread
from subprocess import Popen
import logging
import psutil
import os
import socket


class PupilCoreInterface:
    def __init__(self):
        # Initialize logging
        logging.basicConfig(level=logging.INFO)

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
            self.p = Popen(["python3", "pupil/pupil_src/main.py", "capture", "--hide-ui"], preexec_fn=os.setsid)

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

    def send_recv_notification(self, n):
        self.req.send_string(f"notify.{n['subject']}", flags=zmq.SNDMORE)
        self.req.send(msgpack.dumps(n))
        return self.req.recv_string()

    def terminate(self):
        try:
            self.exit_thread = True

            if self.capture_thread and self.capture_thread.is_alive():
                self.capture_thread.join(timeout=1)

            if self.req:
                try:
                    n = {'subject': 'service_process.should_stop'}
                    logging.info(self.send_recv_notification(n))
                except Exception as e:
                    logging.error(f"Failed to send termination notification: {e}")

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
                logging.info(f"Forcefully terminated Pupil capture program with PID {self.p.pid}.")
                self.p = None

            # Check for Zombie Pupil processes again and terminate them
            for proc in psutil.process_iter():
                try:
                    if "pupil" in proc.name().lower():
                        logging.warning(f"Found a zombie Pupil Core process: {proc.name()}, terminating it.")
                        proc.terminate()
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    pass

            logging.info("Successfully terminated all resources.")
        except Exception as e:
            logging.error(f"An exception occurred during termination: {e}")
            raise e