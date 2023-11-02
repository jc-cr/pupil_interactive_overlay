from abstracts import VideoSource, VideoFrameTarget
import cv2

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

    def render_frame(self):
        frame = self.video_source.get_frame()
        target_x, target_y = self.video_frame_target.get_target()
        
        # Overlay the target on the frame at (target_x, target_y).
        # This is a placeholder. Actual rendering can be done with a library of choice.
        
        return frame