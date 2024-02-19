"""
This script demonstrates how to take a screenshot in a multi-monitor environment using PySide6.
"""

import sys
from typing import Optional

import cv2
from PIL import Image, ImageGrab
from PySide6.QtCore import QObject, QPoint, QRectF, Qt
from PySide6.QtGui import QColor, QImage, QPainter, QPen, QPixmap
from PySide6.QtWidgets import QApplication, QLabel, QLineEdit, QMainWindow, QMessageBox, QPushButton, QWidget


class SnippingWindow(QWidget):
    """
    A snipping widget that allows the user to select a region of image in the window to capture.
    """
    def __init__(self, image: Image.Image, on_complete, most_left_monitor: int, parent: Optional[QObject] = None):
        super(SnippingWindow, self).__init__()
        self.store_qimg = QImage(image.tobytes("raw", "RGB"), image.width, image.height, QImage.Format.Format_RGB888)
        self.image_width, self.image_height = image.size
        if parent:
            self.parent = parent  # type: ignore

        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint)  # stays on top
        self.setWindowFlags(Qt.WindowType.CustomizeWindowHint)  # borderless
        # set geometry to most left monitor (user defined)
        self.setGeometry(QApplication.screens()[most_left_monitor].geometry())
        self.setFixedWidth(self.image_width)  # set width to image
        self.setFixedHeight(self.image_height)  # set height to image

        self.begin = QPoint()
        self.end = QPoint()
        self.on_complete = on_complete
        self.is_snipping = False

    def start(self):
        self.is_snipping = True
        self.mask = QPixmap(self.size())  # type: ignore
        self.mask.fill(QColor(0, 0, 0, 0))

        self.setCursor(Qt.CursorShape.CrossCursor)
        self.show()

    def paintEvent(self, _event):
        if self.is_snipping:
            brush_color = (128, 128, 255, 150)
            lw = 0
            opacity = 0.3
        else:
            self.begin = QPoint()
            self.end = QPoint()
            brush_color = (0, 0, 0, 0)
            lw = 0
            opacity = 0

        # self.lbl_ss_taken.lower()
        self.setWindowOpacity(opacity)
        qp = QPainter(self)
        pixmap = QPixmap(self.store_qimg)  # put image on window
        qp.drawPixmap(0, 0, pixmap)
        qp.setPen(QPen(QColor('black'), lw))
        qp.setBrush(QColor(*brush_color))

        rect = QRectF(self.begin, self.end)
        qp.drawRect(rect)

    def mousePressEvent(self, event):
        self.begin = event.position()
        self.end = self.begin
        self.update()

    def mouseMoveEvent(self, event):
        self.end = event.position()
        self.update()

    def mouseReleaseEvent(self, _event):
        self.is_snipping = False
        x1 = min(self.begin.x(), self.end.x())
        y1 = min(self.begin.y(), self.end.y())
        x2 = max(self.begin.x(), self.end.x())
        y2 = max(self.begin.y(), self.end.y())

        self.repaint()
        QApplication.processEvents()
        screen = QApplication.primaryScreen()
        img = screen.grabWindow(self.winId(), int(x1), int(y1), int(x2 - x1), int(y2 - y1))
        img.save("temp.png")

        print("SS Taken | ", x1, y1, x2, y2)
        try:
            # img = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
            img = cv2.imread("temp.png")
        except Exception as e:
            print(e)
            img = None

        if self.on_complete is not None:
            self.on_complete(img)

        self.close()


class ScreenshotWindow(QMainWindow):
    """
    A main window that shows example usage to take a screenshot on each monitor.
    """
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Screenshot Window")

        self.button = QPushButton("Take Screenshot", self)
        self.button.clicked.connect(self.take_screenshot)
        self.button.setGeometry(50, 50, 200, 50)

        self.screenshot_windows = []

        x = QApplication.screens()
        print(x)
        for i in x:
            print(i.geometry())

        self.lbl_most_left_monitor = QLabel("Most Left Monitor:", self)
        self.lbl_most_left_monitor.setGeometry(50, 100, 200, 50)

        # store variable to keep track of most left monitor
        self.most_left_monitor = "0"  # user input

        self.entry_most_left_monitor = QLineEdit(self)
        self.entry_most_left_monitor.setGeometry(250, 100, 100, 50)
        self.entry_most_left_monitor.setText(str(self.most_left_monitor))
        self.entry_most_left_monitor.textChanged.connect(self.on_most_left_monitor_changed)

    def on_most_left_monitor_changed(self, text):
        self.most_left_monitor = text

    def take_screenshot(self):
        try:
            self.most_left_monitor = int(self.most_left_monitor)
        except ValueError:
            # invalid input show message
            QMessageBox.warning(self, "Invalid Input", "Most left monitor must be a number")
            return

        # take full screenshot
        full_ss = ImageGrab.grab(all_screens=True)

        mask_window = SnippingWindow(full_ss, self.on_screenshot_complete, self.most_left_monitor, self)
        mask_window.start()
        self.screenshot_windows.append(mask_window)

    def on_screenshot_complete(self, img):
        if img is not None:
            cv2.imshow("Screenshot", img)
        else:
            print("No image captured")

        # clean up
        for w in self.screenshot_windows:
            w.close()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ScreenshotWindow()
    window.setGeometry(100, 100, 400, 200)
    window.show()
    sys.exit(app.exec())
