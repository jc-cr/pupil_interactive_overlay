import cv2
# Relative import
from .abstracts import VideoSource, VideoFrameTarget

class WebcamVideoSource(VideoSource):

    def __init__(self):
        self.cap = cv2.VideoCapture(0)  # 0 indicates default camera

    def connect(self):
        if not self.cap.isOpened():
            raise RuntimeError("Unable to open webcam.")

    def start_capture(self):
        # Since we're using OpenCV, starting the capture is just opening the video capture. 
        # This is essentially done in the constructor.
        pass

    def get_frame(self):
        ret, frame = self.cap.read()
        if ret:
            return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)  # Convert to RGB format
        return None

    def terminate(self):
        if self.cap:
            self.cap.release()


class MouseClickVideoFrameTarget(VideoFrameTarget):

    def __init__(self):
        self.x, self.y = 0, 0

    def get_target(self):
        return self.x, self.y

    def update_target(self, x, y):
        self.x, self.y = x, y


class DrawOnVideoFrame:

    def __init__(self, video_source: VideoSource, video_frame_target: VideoFrameTarget):
        self.video_source = video_source
        self.video_frame_target = video_frame_target

    def get_updated_frame(self):
        frame = self.video_source.get_frame()
        target_x, target_y = self.video_frame_target.get_target()
        
        # If the frame is not None, overlay the target on the frame at (target_x, target_y).
        if frame is not None:
            radius = 10  # Radius of the circle
            color = (0, 0, 255)  # Color of the circle (red in BGR format)
            thickness = 2  # Thickness of the circle outline. -1 fills the circle.

            cv2.circle(frame, (target_x, target_y), radius, color, thickness)

        
        return frame
