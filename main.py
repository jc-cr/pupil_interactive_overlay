import sys
from PyQt5.QtWidgets import QApplication
from overlay import MainWindow

if __name__ == '__main__':
    app = QApplication(sys.argv)
    mywindow = MainWindow()
    mywindow.show()
    sys.exit(app.exec_())
