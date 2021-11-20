from tkinter import *
from screen_translate.Mbox import Mbox
from screen_translate.Public import fJson, mInfo, _StoredGlobal
import os

# Settings to capture all screens
from PIL import ImageGrab
from functools import partial
ImageGrab.grab = partial(ImageGrab.grab, all_screens=True)

# Get dir path
dir_path = os.path.dirname(os.path.realpath(__file__))
img_path = dir_path + r"\..\..\img_captured"

class Snip_Mask():
    """The UI for snipping"""
    # ----------------------------------------------------------------------
    def __init__(self):
        self.root = Tk()
        self.root.attributes("-transparent", "blue")
        self.root.geometry('400x50+200+200')  # set new geometry
        self.root.title('Lil Snippy')
        self.root.withdraw() # Hide the window cause it's actually not needed
        self.rect = None
        self.x = self.y = 0
        self.start_x = None
        self.start_y = None
        self.curX = None
        self.curY = None

        # The snipping mask
        self.snipping_Mask = Toplevel(self.root)
        self.snipping_Mask.withdraw() # Hide the window
        self.snipping_Mask.overrideredirect(True) # Hide the top bar
        self.snipping_Mask.attributes("-transparent", "blue") # Make it transparent with blue backgrounds
        self.snipping_Mask.geometry(self.getScreenTotalGeometry()) # The initial geometry of the mask
        self.picture_frame = Frame(self.snipping_Mask, background = "blue")
        self.picture_frame.pack(fill=BOTH, expand=YES)

    def getScreenTotalGeometry(self):
        snippingType = None
        # Get ScreenData
        screenData = mInfo.getScreenInfo()
        # Read settingsCache
        setting = fJson.readSetting()
        try: # Try catch to avoid program crash.
            snippingType = setting['snippingWindowGeometry']
        except KeyError: 
            snippingType = "auto" 

        if snippingType != "auto": # IF set by user
            return setting['snippingWindowGeometry']
        else: # If auto
            # Get offset
            offset_X, offset_Y = 0, 0
            primaryIn = screenData['primaryIn']
            if screenData['layoutType'] == "horizontal":
                if primaryIn != 0: # Make sure its not the first monitor
                    counter = 0
                    for monitor in screenData['mData']:
                        if counter != primaryIn:
                            offset_X += monitor.x

                    # Set to 0 because the first monitor is the primary monitor
                    if offset_X > 0:
                        offset_X = 0
                else:
                    offset_X = 0
            else:
                if primaryIn != 0: # Make sure its not the first monitor
                    counter = 0
                    for monitor in screenData['mData']:
                        if counter != primaryIn:
                            offset_Y += monitor.y
                    
                    # Set to 0 because the first monitor is the primary monitor
                    if offset_Y > 0:
                        offset_Y = 0
                else:
                    offset_Y = 0
            # Get the full screen size
            screenTotalGeometry = f"{screenData['totalX']}x{screenData['totalY']}+{offset_X}+{offset_Y}"
            return screenTotalGeometry

    def takeBoundedScreenShot(self, x1, y1, x2, y2):
        coords = [x1, y1, x2, y2]
        _StoredGlobal.main.capture_UI.getTextAndTranslate(snippedCoords = coords)

    def createScreenCanvas(self):
        """
        Create the canvas for the snipping mask
        """
        _StoredGlobal.set_Status_Busy()
        # Check for the lang from and langto only if it's on translation mode
        if _StoredGlobal.engine != "None":
            # If selected langfrom and langto is the same
            if(_StoredGlobal.langFrom) == (_StoredGlobal.langTo):
                _StoredGlobal.set_Status_Error()
                print("Error Language is the same as source! Please choose a different language")
                Mbox("Error: Language target is the same as source", "Language target is the same as source! Please choose a different language", 2, _StoredGlobal.main_Ui)
                _StoredGlobal.set_Status_Warning()
                return
            # If selected langfrom is autodetect -> invalid
            if _StoredGlobal.langFrom == "Auto-Detect":
                _StoredGlobal.set_Status_Error()
                print("Error: Invalid Language Selected! Can't Use Auto Detect in Capture Mode")
                Mbox("Error: Invalid Language Selected", "Invalid Language Selected! Can't Use Auto Detect in Capture Mode", 2, _StoredGlobal.main_Ui)
                _StoredGlobal.set_Status_Warning()
                return
            # If selected langto is autodetect -> also invalid
            if _StoredGlobal.langTo == "Auto-Detect":
                _StoredGlobal.set_Status_Error()
                print("Error: Invalid Language Selected! Must specify language destination")
                Mbox("Error: Invalid Language Selected", "Invalid Language Selected! Must specify language destination", 2, _StoredGlobal.main_Ui)
                _StoredGlobal.set_Status_Warning()
                return

        print(">> Snipped mode activated")
        self.snipping_Mask.geometry(self.getScreenTotalGeometry())

        # Show the mask
        self.snipping_Mask.deiconify()

        # Create the canvas
        self.screenCanvas = Canvas(self.picture_frame, cursor="cross", bg="grey11")
        self.screenCanvas.pack(fill=BOTH, expand=YES)

        # Bind events
        self.snipping_Mask.bind("<Escape>", self.exitScreenshotMode)
        self.screenCanvas.bind("<ButtonPress-1>", self.on_button_press)
        self.screenCanvas.bind("<ButtonPress-3>", self.exitScreenshotMode)
        self.screenCanvas.bind("<B1-Motion>", self.on_move_press)
        self.screenCanvas.bind("<ButtonRelease-1>", self.on_button_release)

        # self.master_screen.attributes('-fullscreen', True)
        self.snipping_Mask.attributes('-alpha', .3)
        self.snipping_Mask.lift()
        self.snipping_Mask.attributes("-topmost", True)
        self.snipping_Mask.focus_force()

    def on_button_release(self, event):
        """
        When the mouse button is released, take the screenshot then translate it and then exit snipping mode.

        Args:
            event: Ignored
        """
        self.recPosition()
        if self.curX is None:
            return

        if self.start_x <= self.curX and self.start_y <= self.curY:
            print(">> Detected position direction: right down")
            self.takeBoundedScreenShot(self.start_x, self.start_y, self.curX - self.start_x, self.curY - self.start_y)

        elif self.start_x >= self.curX and self.start_y <= self.curY:
            print(">> Detected position direction: left down")
            self.takeBoundedScreenShot(self.curX, self.start_y, self.start_x - self.curX, self.curY - self.start_y)

        elif self.start_x <= self.curX and self.start_y >= self.curY:
            print(">> Detected position direction: right up")
            self.takeBoundedScreenShot(self.start_x, self.curY, self.curX - self.start_x, self.start_y - self.curY)

        elif self.start_x >= self.curX and self.start_y >= self.curY:
            print(">> Detected position direction: left up")
            self.takeBoundedScreenShot(self.curX, self.curY, self.start_x - self.curX, self.start_y - self.curY)

        self.exitScreenshotMode()

    def exitScreenshotMode(self, event=None):
        """
        Exit the snipping mode.

        Args:
            event : Ignored. Defaults to None.
        """
        print(">> Snipped mode exited")
        _StoredGlobal.set_Status_Ready()
        self.screenCanvas.destroy()
        self.snipping_Mask.withdraw()

    def on_button_press(self, event):
        """
        When the mouse button is pressed, set the start position. And draw the rectangle.

        Args:
            event : Mouse event
        """
        # save mouse drag start position
        self.start_x = self.screenCanvas.canvasx(event.x)
        self.start_y = self.screenCanvas.canvasy(event.y)

        self.rect = self.screenCanvas.create_rectangle(self.x, self.y, 1, 1, outline='red', width=3, fill="blue")

    def on_move_press(self, event):
        """
        When the mouse is moved, update the rectangle.

        Args:
            event : Mouse event
        """
        self.curX, self.curY = (event.x, event.y)
        # expand rectangle as you drag the mouse
        self.screenCanvas.coords(self.rect, self.start_x, self.start_y, self.curX, self.curY)

    def recPosition(self):
        """
        Get the position details
        """
        if self.curX is not None:
            print(">> Captured")
            print("Starting position x:", self.start_x)
            print("End position x:",self.curX)
            print("Starting position y:",self.start_y)
            print("End position y:",self.curY)