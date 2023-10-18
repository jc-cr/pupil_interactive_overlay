import sys
import atexit
from PyQt5.QtWidgets import QApplication
from overlay_gui import MainWindow
from pupil_core_interface import PupilCoreInterface

def cleanup():
    print("Cleaning up resources...")
    try:
        glasses.terminate()
    except Exception as e:
        print(f"An error occurred during cleanup: {e}")


if __name__ == '__main__':
    try: 
        app = QApplication(sys.argv)

        glasses = PupilCoreInterface()

        glasses.connect()
        glasses.start_capture()

        # Register the cleanup function to be called when the application exits
        atexit.register(cleanup)

        gui = MainWindow(glasses)
        gui.show()

        sys.exit(app.exec_())

    except Exception as e:
        print(f"An error occurred: {e}")
        exit(1)