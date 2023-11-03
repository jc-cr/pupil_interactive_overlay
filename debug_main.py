from utils import WebcamVideoSource, MouseClickVideoFrameTarget, DrawOnVideoFrame
from overlay_gui import MainWindow
from PyQt5.QtWidgets import QApplication
import sys

def main():
    app = QApplication(sys.argv)
    
    # Initialize video source and video frame target
    video_source = WebcamVideoSource()
    video_frame_target = MouseClickVideoFrameTarget()
    
    # Initialize the video frame drawer
    draw_on_video_frame = DrawOnVideoFrame(video_source, video_frame_target)
    
    # Initialize the main window
    main_window = MainWindow(draw_on_video_frame)
    main_window.show()

    def on_video_window_click(x, y):
        # Calculate scaling factors
        display_width, display_height = main_window.video_window.size().width(), main_window.video_window.size().height()
        original_width, original_height = video_source.get_frame().shape[1], video_source.get_frame().shape[0]
        
        scaling_factor_width = display_width / original_width
        scaling_factor_height = display_height / original_height

        # Adjust x and y coordinates
        adjusted_x = int(x / scaling_factor_width)
        adjusted_y = int(y / scaling_factor_height)

        # Update the video frame target
        video_frame_target.update_target(adjusted_x, adjusted_y)


    # Connect the VideoWindow's mouse_clicked signal to the update function
    main_window.video_window.mouse_clicked.connect(on_video_window_click)

    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
