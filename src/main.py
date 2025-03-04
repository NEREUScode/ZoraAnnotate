import sys
import os
from PyQt5.QtWidgets import QApplication, QSplashScreen, QMainWindow, QLabel, QVBoxLayout, QWidget, QDesktopWidget
from PyQt5.QtGui import QPixmap, QPainter
from PyQt5.QtCore import Qt, QTimer, QRect
from src.annotator_window import ImageAnnotator

# To address Linux errors, by removing the QT_QPA_PLATFORM_PLUGIN_PATH 
# environment variable on Linux systems, which allows the application 
# to use the system's Qt platform plugins instead of potentially conflicting ones
if sys.platform.startswith("linux"):
    os.environ.pop("QT_QPA_PLATFORM_PLUGIN_PATH", None)

class SplashScreen(QSplashScreen):
    def __init__(self, pixmap):
        super().__init__(pixmap)
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.setMask(pixmap.mask())

        self.pixmap = pixmap
        self.current_width = 0  # Start with no image showing
        self.setGeometry(0, 0, pixmap.width(), pixmap.height())

        # Center the splash screen on the screen
        screen = QDesktopWidget().screenGeometry()  # Get screen size
        x = (screen.width() - pixmap.width()) // 2  # Calculate x coordinate
        y = (screen.height() - pixmap.height()) // 2  # Calculate y coordinate
        self.move(x, y)  # Move the splash screen to the center

        # Timer to update the animation (every 30 ms)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_animation)
        self.timer.start(30)

    def update_animation(self):
        # Increment the width of the pixmap that is being displayed
        if self.current_width < self.pixmap.width():
            self.current_width += 10  # Increase this number for faster loading effect
            self.update()  # Request a repaint of the splash screen
        else:
            self.timer.stop()  # Stop the timer when the full image is displayed

    def paintEvent(self, event):
        painter = QPainter(self)
        # Draw the portion of the pixmap from left to right
        painter.drawPixmap(0, 0, self.pixmap, 0, 0, self.current_width, self.pixmap.height())

def main():
    app = QApplication(sys.argv)

    # Ensure the logo file path is correct using an absolute path
    script_dir = os.path.dirname(os.path.abspath(__file__))  # Get the script's directory
    logo_path = os.path.join(script_dir, "assets/logo.png")  # Join the script directory with the logo filename

    if not os.path.exists(logo_path):
        print(f"Error: Logo file '{logo_path}' not found.")
        sys.exit(1)

    # Load the splash screen image
    splash_pix = QPixmap(logo_path)
    if splash_pix.isNull():
        print(f"Error: Failed to load image '{logo_path}'.")
        sys.exit(1)

    # Create and show splash screen
    splash = SplashScreen(splash_pix)
    splash.show()

    # Set a timer to close the splash screen and open the main window after a delay (e.g., 3 seconds)
    timer = QTimer()
    timer.timeout.connect(lambda: (splash.close(), window.show()))  # Show main window after splash
    timer.start(3000)  # 3000 ms = 3 seconds

    # Create the main window (ImageAnnotator)
    window = ImageAnnotator()
    
    # Start the application's event loop
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
