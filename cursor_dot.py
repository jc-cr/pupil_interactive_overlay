from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QPainter, QColor, QCursor
from PyQt5.QtCore import Qt, QTimer

class CursorDot(QWidget):
    def __init__(self):
        super(CursorDot, self).__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool | Qt.X11BypassWindowManagerHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)  # Add this line
        self.setAutoFillBackground(False)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.updatePosition)
        self.timer.start(16)  # Update every ~16ms

    def updatePosition(self):
        cursor_position = QCursor.pos()
        self.move(cursor_position - self.rect().center())

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(QColor(0, 0, 255, 127))  # Blue color with 50% opacity
        painter.drawEllipse(self.rect().center(), 10, 10)
