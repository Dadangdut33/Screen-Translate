import threading
import tkinter as tk

from screen_translate.Globals import gClass, path_logo_icon, fJson
from screen_translate.Logging import logger
from screen_translate.components.MBox import Mbox
from screen_translate.utils.Translate import translate
from screen_translate.utils.Capture import ocrFromCoords
from screen_translate.utils.Monitor import getScreenTotalGeometry

from PIL import Image, ImageTk


class SnipWindow:
    """Snip Window"""

    def __init__(self, master: tk.Tk):
        self.root = tk.Toplevel(master)
        self.root.title("Snipper")
        self.root.geometry("500x500")  # placeholder
        self.root.overrideredirect(True)  # borderless
        self.root.wm_attributes("-topmost", True)  # topmost
        self.root.wm_withdraw()
        self.imgobj = None
        self.img = None
        gClass.csw = self  # type: ignore

        # mask
        self.tlw_snipmask = tk.Toplevel(self.root)
        self.tlw_snipmask.wm_withdraw()  # Hide the window
        self.tlw_snipmask.overrideredirect(True)  # Hide the top bar
        self.tlw_snipmask.attributes("-transparent", "blue")  # Make it transparent with blue backgrounds
        self.tlw_snipmask.geometry("500x500")  # placeholder
        self.f_snipper = tk.Frame(self.tlw_snipmask, bg="blue")  # placeholder
        self.f_snipper.pack(fill=tk.BOTH, expand=True)

        # variables
        self.rect = None
        self.x = self.y = 0
        self.start_x = 0
        self.start_y = 0
        self.curX = 0
        self.curY = 0

        # image canvas
        self.img_canvas = tk.Canvas(self.root, highlightthickness=0)
        self.img_canvas.pack(fill=tk.BOTH, expand=True)  # ocupy main whole window

        # binds
        self.tlw_snipmask.bind("<Escape>", self.exitScreenshotMode)
        self.img_canvas.bind("<Escape>", self.exitScreenshotMode)

        self.onInit()
        # ------------------ Set Icon ------------------
        try:
            self.root.iconbitmap(path_logo_icon)
        except:
            pass

    def onInit(self):
        self.root.geometry(getScreenTotalGeometry()[0])
        self.tlw_snipmask.geometry(getScreenTotalGeometry()[0])

    def start_snipping(self, imgObj: Image.Image):
        self.onInit()
        logger.info("Snipped mode entered! Loading image...")
        self.imgobj = imgObj
        self.img = ImageTk.PhotoImage(self.imgobj, master=self.img_canvas)
        self.img_canvas.create_image(0, 0, anchor=tk.NW, image=self.img)
        logger.info("Image loaded to canvas")

        # show window
        self.root.deiconify()

        # ss canvas
        self.ss_canvas = tk.Canvas(self.f_snipper, cursor="cross", bg="grey11")
        self.ss_canvas.pack(fill=tk.BOTH, expand=True)

        self.ss_canvas.bind("<Escape>", self.exitScreenshotMode)
        self.ss_canvas.bind("<ButtonPress-1>", self.on_button_press)
        self.ss_canvas.bind("<ButtonPress-3>", self.exitScreenshotMode)
        self.ss_canvas.bind("<B1-Motion>", self.on_move_press)
        self.ss_canvas.bind("<ButtonRelease-1>", self.on_button_release)

        self.tlw_snipmask.deiconify()
        self.tlw_snipmask.attributes("-alpha", 0.3)
        self.tlw_snipmask.lift()
        self.tlw_snipmask.attributes("-topmost", True)
        self.tlw_snipmask.focus_force()

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
        self.ss_canvas.configure(cursor="watch")
        self.root.update_idletasks()

        if self.start_x <= self.curX and self.start_y <= self.curY:
            logger.info("Detected position direction: right down")
            self.takeBoundedScreenShot(self.start_x, self.start_y, self.curX - self.start_x, self.curY - self.start_y)

        elif self.start_x >= self.curX and self.start_y <= self.curY:
            logger.info("Detected position direction: left down")
            self.takeBoundedScreenShot(self.curX, self.start_y, self.start_x - self.curX, self.curY - self.start_y)

        elif self.start_x <= self.curX and self.start_y >= self.curY:
            logger.info("Detected position direction: right up")
            self.takeBoundedScreenShot(self.start_x, self.curY, self.curX - self.start_x, self.start_y - self.curY)

        elif self.start_x >= self.curX and self.start_y >= self.curY:
            logger.info("Detected position direction: left up")
            self.takeBoundedScreenShot(self.curX, self.curY, self.start_x - self.curX, self.start_y - self.curY)

        self.exitScreenshotMode()

    def takeBoundedScreenShot(self, x1, y1, x2, y2):
        coords = [x1, y1, x2, y2]

        ocrThread = threading.Thread(target=self.startOCR, args=(coords,), daemon=True)
        ocrThread.start()

    def startOCR(self, coords):
        gClass.lb_start()
        success, res = ocrFromCoords(coords)

        if success:
            gClass.clear_mw_q()
            gClass.clear_ex_q()
            gClass.insert_mw_q(res)
            gClass.insert_ex_q(res)

            # translate if translate
            if fJson.settingCache["engine"] != "None":
                try:
                    tlThread = threading.Thread(target=translate, args=(res, fJson.settingCache["sourceLang"], fJson.settingCache["targetLang"], fJson.settingCache["engine"]))
                    tlThread.start()
                except Exception as e:
                    logger.exception(e)
                    Mbox("Error", "Error while translating: " + str(e), 2)
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

        gClass.lb_stop()

    def exitScreenshotMode(self, event=None):
        """
        Exit the snipping mode.

        Args:
            event : Ignored. Defaults to None.
        """
        logger.info("Snipped mode exited")
        self.ss_canvas.destroy()
        self.tlw_snipmask.wm_withdraw()
        self.root.wm_withdraw()

    def on_button_press(self, event):
        """
        When the mouse button is pressed, set the start position. And draw the rectangle.

        Args:
            event : Mouse event
        """
        # save mouse drag start position
        self.start_x = self.ss_canvas.canvasx(event.x)
        self.start_y = self.ss_canvas.canvasy(event.y)

        self.rect = self.ss_canvas.create_rectangle(self.x, self.y, 1, 1, outline="red", width=1, fill="blue")

    def on_move_press(self, event):
        """
        When the mouse is moved, update the rectangle.

        Args:
            event : Mouse event
        """
        self.curX, self.curY = (event.x, event.y)
        # expand rectangle as you drag the mouse
        self.ss_canvas.coords(self.rect, self.start_x, self.start_y, self.curX, self.curY)  # type: ignore

    def recPosition(self):
        """
        Get the position details
        """
        if self.curX is not None:
            logger.info("Captured")
            logger.debug(f"Starting position x: {self.start_x}")
            logger.debug(f"End position x: {self.curX}")
            logger.debug(f"Starting position y: {self.start_y}")
            logger.debug(f"End position y: {self.curY}")
