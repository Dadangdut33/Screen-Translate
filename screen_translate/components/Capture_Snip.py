import threading
import tkinter as tk
import tkinter.ttk as ttk

from screen_translate.Globals import gClass, fJson, path_logo_icon
from screen_translate.Logging import logger
from screen_translate.components.MBox import Mbox
from screen_translate.utils.Capture import ocrFromCoords
from screen_translate.utils.Monitor import getScreenTotalGeometry

from PIL import Image, ImageTk


class SnipWindow:
    """Snip Window"""

    def __init__(self, master):
        gClass.csw = self  # type: ignore
        self.root = tk.Toplevel(master)
        self.root.title("STL Snipper")
        self.root.geometry("500x500")  # placeholder
        self.root.overrideredirect(True)  # borderless
        self.root.wm_attributes("-topmost", True)  # topmost
        self.root.wm_withdraw()

        # mask
        self.snip_mask = tk.Toplevel(self.root)
        self.snip_mask.wm_withdraw()  # Hide the window
        self.snip_mask.overrideredirect(True)  # Hide the top bar
        self.snip_mask.attributes("-transparent", "blue")  # Make it transparent with blue backgrounds
        self.snip_mask.geometry("500x500")  # placeholder

        # variables
        self.rect = None
        self.x = self.y = 0
        self.start_x = 0
        self.start_y = 0
        self.curX = 0
        self.curY = 0

        # image canvas
        self.screenshotCanvas = tk.Canvas(self.root, highlightthickness=0, cursor="cross")
        self.screenshotCanvas.pack(fill=tk.BOTH, expand=True)  # ocupy main whole window

        # binds
        self.snip_mask.bind("<Escape>", self.exitScreenshotMode)
        self.screenshotCanvas.bind("<ButtonPress-1>", self.on_button_press)
        self.screenshotCanvas.bind("<ButtonPress-3>", self.exitScreenshotMode)
        self.screenshotCanvas.bind("<B1-Motion>", self.on_move_press)
        self.screenshotCanvas.bind("<ButtonRelease-1>", self.on_button_release)

        # ------------------ Set Icon ------------------
        try:
            self.root.iconbitmap(path_logo_icon)
        except:
            pass

    def onInit(self):
        self.root.geometry(getScreenTotalGeometry()[0])
        self.snip_mask.geometry(getScreenTotalGeometry()[0])

    def start_snipping(self, imagePath: str):
        logger.info(">> Snipped mode entered! Loading image...")
        imgObj = Image.open(imagePath)
        tkImg = ImageTk.PhotoImage(imgObj)
        self.screenshotCanvas.create_image(0, 0, anchor=tk.NW, image=tkImg)
        logger.info(">> Image loaded to canvas")

        # show window
        self.root.deiconify()

        self.snip_mask.attributes("-alpha", 0.3)
        self.snip_mask.lift()
        self.snip_mask.attributes("-topmost", True)
        self.snip_mask.focus_force()

    def on_button_release(self, event):
        """
        When the mouse button is released, take the screenshot then translate it and then exit snipping mode.

        Args:
            event: Ignored
        """
        self.recPosition()
        if self.curX is None:
            return

        # Change canvas cursor to watch
        self.screenshotCanvas.configure(cursor="watch")
        self.root.update_idletasks()

        if self.start_x <= self.curX and self.start_y <= self.curY:
            logger.info(">> Detected position direction: right down")
            self.takeBoundedScreenShot(self.start_x, self.start_y, self.curX - self.start_x, self.curY - self.start_y)

        elif self.start_x >= self.curX and self.start_y <= self.curY:
            logger.info(">> Detected position direction: left down")
            self.takeBoundedScreenShot(self.curX, self.start_y, self.start_x - self.curX, self.curY - self.start_y)

        elif self.start_x <= self.curX and self.start_y >= self.curY:
            logger.info(">> Detected position direction: right up")
            self.takeBoundedScreenShot(self.start_x, self.curY, self.curX - self.start_x, self.start_y - self.curY)

        elif self.start_x >= self.curX and self.start_y >= self.curY:
            logger.info(">> Detected position direction: left up")
            self.takeBoundedScreenShot(self.curX, self.curY, self.start_x - self.curX, self.start_y - self.curY)

        self.exitScreenshotMode()

    def takeBoundedScreenShot(self, x1, y1, x2, y2):
        coords = [x1, y1, x2, y2]
        gClass.lb_start()

        thread = threading.Thread(target=self.startOCR, args=(coords,), daemon=True)
        thread.start()

        gClass.lb_stop()

    def startOCR(self, coords):
        success, res = ocrFromCoords(coords)

        if success:
            gClass.insert_mw_res(res)
            gClass.insert_ex_res(res)
        else:
            if "is not installed or it's not in your PATH" in res:
                Mbox("Error: Tesseract Could not be Found", "Invalid path location for tesseract.exe, please change it in the setting!", 2)
            elif "Failed loading language" in res:
                Mbox(
                    "Error: Failed Loading Language",
                    "Language data not found! It could be that the language data is not installed! Please reinstall tesseract or download the language data and put it into Tesseract-OCR\\tessdata!\n\nThe official version that is used for this program is v5.0.0-alpha.20210811. You can download it from https://github.com/UB-Mannheim/tesseract/wiki or https://digi.bib.uni-mannheim.de/tesseract/",
                    2,
                )
            else:
                Mbox("Error", res, 2)

    def exitScreenshotMode(self, event=None):
        """
        Exit the snipping mode.

        Args:
            event : Ignored. Defaults to None.
        """
        logger.info(">> Snipped mode exited")
        self.snip_mask.wm_withdraw()
        self.root.wm_withdraw()

    def on_button_press(self, event):
        """
        When the mouse button is pressed, set the start position. And draw the rectangle.

        Args:
            event : Mouse event
        """
        # save mouse drag start position
        self.start_x = self.screenshotCanvas.canvasx(event.x)
        self.start_y = self.screenshotCanvas.canvasy(event.y)

        self.rect = self.screenshotCanvas.create_rectangle(self.x, self.y, 1, 1, outline="red", width=3, fill="blue")

    def on_move_press(self, event):
        """
        When the mouse is moved, update the rectangle.

        Args:
            event : Mouse event
        """
        self.curX, self.curY = (event.x, event.y)
        # expand rectangle as you drag the mouse
        self.screenshotCanvas.coords(self.rect, self.start_x, self.start_y, self.curX, self.curY)  # type: ignore

    def recPosition(self):
        """
        Get the position details
        """
        if self.curX is not None:
            logger.info(">> Captured")
            logger.debug("Starting position x:", self.start_x)
            logger.debug("End position x:", self.curX)
            logger.debug("Starting position y:", self.start_y)
            logger.debug("End position y:", self.curY)
