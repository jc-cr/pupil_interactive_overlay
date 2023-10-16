import sys
import atexit
from PyQt5.QtWidgets import QApplication
from overlay_gui import MainWindow
from pupil_core_interface import PupilCoreInterface

def cleanup():
    print("Cleaning up resources...")
    glasses.terminate()

if __name__ == '__main__':
    app = QApplication(sys.argv)

    glasses = PupilCoreInterface()

    try:
        glasses.connect()
        glasses.start_capture()

        # Register the cleanup function to be called when the application exits
        atexit.register(cleanup)

        gui = MainWindow(glasses)
        gui.show()

        sys.exit(app.exec_())

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        print("Cleaning up resources...")
        cleanup()