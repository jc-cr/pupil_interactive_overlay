from PyQt5.QtWidgets import QDesktopWidget, QLabel, QVBoxLayout
from PyQt5.QtWidgets import QWidget, QPushButton, QHBoxLayout, QMainWindow, QApplication, QMenu, QAction
from PyQt5.QtCore import Qt, QSize, QPoint, QTimer, QEvent
from PyQt5.QtWidgets import QSizePolicy
from PyQt5.QtGui import QIcon, QCursor, QPixmap, QImage
from PyQt5.QtCore import pyqtSignal
import os
# relative imports
from .abstracts import FrameUpdater



class VideoWindow(QWidget):

    mouse_clicked = pyqtSignal(int, int)

    def __init__(self, frame_updater: FrameUpdater):
        super(VideoWindow, self).__init__()

        self.draggable = True
        self.drag_position = QPoint()
        
        self.timer = QTimer()  # Initialize the timer
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)  # Update every 30 ms

        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)

        # Set Window size to appear as small rectagle in bottom right corner
        self.setFixedSize(400, 300)
        self.video_label = QLabel(self)
        self.video_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.video_label.setScaledContents(True)
        layout = QVBoxLayout()
        layout.addWidget(self.video_label)
        layout.setContentsMargins(0, 0, 0, 0)  # Ensure no margins
        self.setLayout(layout)
        self.setWindowToBottomRight()



        self.frame_updater = frame_updater

    def update_frame(self):
        try:
            frame = self.frame_updater.get_updated_frame()
            if frame is not None:
                height, width, channel = frame.shape
                bytes_per_line = 3 * width
                image = QImage(frame.data, width, height, bytes_per_line, QImage.Format_RGB888).rgbSwapped()
                self.video_label.setPixmap(QPixmap.fromImage(image))
        except Exception as e:
            print(f"An error occurred: {e}")
            raise e
        
    def mousePressEvent(self, event):
        """
        Single click to move the window, double click to emit a signal 
        """
        if event.button() == Qt.LeftButton:
            self.draggable = True
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            if event.type() == QEvent.MouseButtonDblClick:  # Check for double-click
                self.mouse_clicked.emit(event.x(), event.y())
            event.accept()


    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and self.draggable:
            self.move(event.globalPos() - self.drag_position)
            event.accept()

    def mouseReleaseEvent(self, event):
        self.draggable = False

    def setWindowToBottomRight(self):
        desktop = QDesktopWidget()
        screen = desktop.screenGeometry()
        width, height = self.geometry().width(), self.geometry().height()
        self.setGeometry(screen.width() - width, screen.height() - height, width, height)


class MainWindow(QMainWindow):
    def __init__(self, frame_updater: FrameUpdater):
        super(MainWindow, self).__init__()

        self.frame_updater = frame_updater
        self.video_window = VideoWindow(self.frame_updater)

        self.label = QLabel(self)
        layout = QVBoxLayout()
        layout.addWidget(self.label)

        self.setWindowFlags(
            Qt.WindowStaysOnTopHint |
            Qt.FramelessWindowHint 
        )

        self.bar_width = 400
        self.bar_height = 30

        self.dir_path = os.path.dirname(os.path.realpath(__file__))
        self.exitIconPath = os.path.join(self.dir_path, "assets/close_icon.png")

        self.initUI()
        self.updatePosition()

    def _initVideoWindowToggleButton(self, layout):
        self.toggle_button = QPushButton("Toggle Inspection Mode")
        self.toggle_button.setFixedSize(200, 20)  # Set the fixed size to 200x20
        self.toggle_button.setCheckable(True)  # Make it a toggle button
        self.toggle_button.clicked.connect(self.toggle_video_window)

        # Center-align the text
        self.toggle_button.setStyleSheet("text-align: center;")
        
        layout.addWidget(self.toggle_button, alignment=Qt.AlignCenter)


    def _initExitButton(self, layout):
        exit_button = QPushButton()
        if not os.path.exists(self.exitIconPath):
            raise FileNotFoundError(self.exitIconPath)        
        
        exit_button.setIcon(QIcon(self.exitIconPath))
        exit_button.setIconSize(QSize(20, 20))
        exit_button.clicked.connect(self.close)
        layout.addWidget(exit_button, alignment=Qt.AlignRight)

    def initUI(self):
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        layout = QHBoxLayout()
        try:
            self._initVideoWindowToggleButton(layout)
            self._initExitButton(layout)
            central_widget.setLayout(layout)
        except FileNotFoundError as e:
            print(f"Unable to find file: {e.args[0]}")
            exit(1)

    def toggle_video_window(self):
        is_checked = self.toggle_button.isChecked()
        if is_checked:
            # Update the button to look like it's pressed
            self.toggle_button.setStyleSheet("background-color: grey;")
            self.video_window.show()

        else:
            # Reset the button style
            self.toggle_button.setStyleSheet("")
            self.video_window.hide()

    def updatePosition(self):
        desktop = QDesktopWidget()
        screen_number = desktop.screenNumber(QCursor.pos())
        screen_geometry = desktop.availableGeometry(screen_number)
        screen_width = screen_geometry.width()
        x_center = (screen_width - self.bar_width) // 2
        self.setGeometry(x_center, 0, self.bar_width, self.bar_height)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.draggable = True
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and self.draggable:
            self.move(event.globalPos() - self.drag_position)
            event.accept()

    def mouseReleaseEvent(self, event):
        self.draggable = False

    def closeEvent(self, event):
        self.video_window.close()
        event.accept()