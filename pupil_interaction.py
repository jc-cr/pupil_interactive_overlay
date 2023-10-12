import cv2
import zmq
from msgpack import unpackb, packb
import numpy as np

# Function to receive data from Pupil Core
def recv_from_sub():
    topic = sub.recv_string()
    payload = unpackb(sub.recv())  # Removed encoding='utf-8'
    extra_frames = []
    while sub.get(zmq.RCVMORE):
        extra_frames.append(sub.recv())
    if extra_frames:
        payload['__raw_data__'] = extra_frames
    return topic, payload

# Function to send notification to Pupil Core
def notify(notification):
    topic = 'notify.' + notification['subject']
    payload = packb(notification, use_bin_type=True)
    req.send_string(topic, flags=zmq.SNDMORE)
    req.send(payload)
    return req.recv_string()

# Initialize ZMQ for Pupil Core
context = zmq.Context()
addr = '127.0.0.1'
req_port = "50020"
req = context.socket(zmq.REQ)
req.connect(f"tcp://{addr}:{req_port}")
req.send_string('SUB_PORT')
sub_port = req.recv_string()

# Start frame publisher with format BGR
notify({'subject': 'start_plugin', 'name': 'Frame_Publisher', 'args': {'format': 'bgr'}})

# Initialize SUB socket for frames and gaze data
sub = context.socket(zmq.SUB)
sub.connect(f"tcp://{addr}:{sub_port}")
sub.setsockopt_string(zmq.SUBSCRIBE, 'frame.')
sub.setsockopt_string(zmq.SUBSCRIBE, 'pupil.')

# Initialize local variables
recent_world = None
gaze_x, gaze_y = 0, 0

while True:
    # Receive data from Pupil Core
    topic, msg = recv_from_sub()

    if topic == 'frame.world':
        if 'height' in msg and 'width' in msg and '__raw_data__' in msg:
            total_size = msg['height'] * msg['width'] * 3  # For a 3-channel image
            if total_size == len(msg['__raw_data__'][0]):
                recent_world = np.frombuffer(msg['__raw_data__'][0], dtype=np.uint8).reshape(msg['height'], msg['width'], 3)
                cv2.imshow('World Frame', recent_world)
            else:
                print(f"Size mismatch: Buffer size is {len(msg['__raw_data__'][0])}, but dimensions require {total_size}")

    elif topic.startswith('pupil.'):
        if 'norm_pos' in msg:
            gaze_x, gaze_y = msg['norm_pos']

    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        break
    elif key == ord('s') and recent_world is not None:
        saved_frame = recent_world.copy()
        saved_gaze_x, saved_gaze_y = int(gaze_x * saved_frame.shape[1]), int(gaze_y * saved_frame.shape[0])

        # Draw a blue dot at the gaze position
        cv2.circle(saved_frame, (saved_gaze_x, saved_gaze_y), 10, (255, 0, 0), -1)

        # Save and display the frame with gaze data
        cv2.imwrite('saved_frame_with_gaze.png', saved_frame)
        cv2.imshow('Saved Frame with Gaze', saved_frame)

# Release resources
cv2.destroyAllWindows()
