from PyQt5.QtWidgets import QWidget, QPushButton, QHBoxLayout, QMainWindow, QApplication, QMenu, QAction
from PyQt5.QtCore import Qt, QSize, QPoint
from PyQt5.QtGui import QIcon

class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()

        self.draggable = True
        self.drag_position = None

        self.setWindowFlags(
            Qt.WindowStaysOnTopHint |
            Qt.FramelessWindowHint |
            Qt.X11BypassWindowManagerHint
        )

        self.bar_width = 400
        self.bar_height = 30
        self.initUI()
        self.updatePosition()

    def initUI(self):
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        layout = QHBoxLayout()

        # Create a QMenu object for the dropdown
        self.menu = QMenu()
        action1 = QAction("Inspect", self)
        action2 = QAction("", self)
        self.menu.addAction(action1)
        self.menu.addAction(action2)

        menu_button = QPushButton()
        menu_button.setIcon(QIcon("assets/menu_icon.png"))
        menu_button.setIconSize(QSize(200, 20))
        menu_button.clicked.connect(self.showMenu)
        layout.addWidget(menu_button, alignment=Qt.AlignCenter)


        exit_button = QPushButton()
        exit_button.setIcon(QIcon("assets/close_icon.png"))
        exit_button.setIconSize(QSize(20, 20))
        exit_button.clicked.connect(self.close)
        layout.addWidget(exit_button, alignment=Qt.AlignRight)

        central_widget.setLayout(layout)

    def showMenu(self):
        button = self.sender()
        pos = button.mapToGlobal(QPoint(0, button.height()))
        self.menu.exec_(pos)


    def updatePosition(self):
        screen_geometry = QApplication.desktop().availableGeometry()
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
