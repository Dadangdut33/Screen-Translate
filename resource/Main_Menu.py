from re import T
import pyautogui
import backend.Translate as tl
import backend.Capture as capture
import backend.JsonHandling as fJson
from tkinter import *
import tkinter.ttk as ttk
from Mbox import Mbox

class CaptureUI():
    root = Tk()
    stayOnTop = True
    currOpacity = '0.8'

    # Empty for padding purposes
    Label(root, text="").grid(row=0, column=0)
    Label(root, text="").grid(row=0, column=2)
    Label(root, text="").grid(row=0, column=3)
    Label(root, text="").grid(row=0, column=4)
    Label(root, text="").grid(row=0, column=5)
    Label(root, text="").grid(row=0, column=6)

    # Label for opacity slider
    opacityLabel = Label(root, text="Opacity: " + str(currOpacity))
    opacityLabel.grid(row=0, column=4, sticky='w')

    # Show/Hide
    def show(self):
        self.root.wm_deiconify()
    
    def on_closing(self):
         self.root.wm_withdraw()

    # Slider function
    root.attributes('-alpha', 0.8)
    def sliderOpac(self, x):
        self.root.attributes('-alpha', x)
        self.opacityLabel.config(text="Opacity: " + str(round(float(x), 2)))
        self.currOpacity = x

    # Capture the text
    def getText(self, offsetXY=["auto", "auto"]):
        opacBefore = self.currOpacity
        self.root.attributes('-alpha', 0)
        # Get xywh of the screen
        x, y, w, h = self.root.winfo_x(), self.root.winfo_y(
        ), self.root.winfo_width(), self.root.winfo_height()

        # X Y offset
        if offsetXY[0] == "auto":
            offsetX = pyautogui.size().width
            offsetY = pyautogui.size().height
        else:
            offsetX = offsetXY[0]
            offsetY = offsetXY[1]

        #  Alignment offset
        if offsetXY[1] == "auto":
            if(offsetX > offsetY):  # Horizontal alignment
                if(x < offsetX):
                    x += offsetX
            else:  # Vertical Alignment
                if(y < offsetY):
                    y += offsetY
        elif offsetXY[1] == "horizontal":
            if(x < offsetX):
                x += offsetX
        elif offsetXY[1] == "vertical":
            if(y < offsetY):
                y += offsetY

        # Capture screen
        w += 60 # added extra pixel cause sometimes it gets cut off
        h += 60
        coords = [x, y, w, h]
        tStatus, settings = fJson.readSetting()
        if tStatus == False or settings['tesseract_loc'] == "":
            self.root.wm_withdraw()  # Hide the capture window
            x = Mbox("Error: Tesseract Not Set!",
                        "Please set tesseract_loc in Setting.json.\nYou can set this in setting or modify it manually in resource/backend/json/Setting.json", 0)
            self.root.wm_deiconify()  # Show the capture window
            return
        is_Success, result = capture.captureImg(coords, "ind", settings['tesseract_loc'], settings['cached']) # MODIF THE LANG LATER
        self.root.attributes('-alpha', opacBefore)
        print(result)
        print(len(result))
        if is_Success == False or len(result) == 1:
            Mbox("Error", "Failed to Capture Text!", 0)
        else:
            # Pass it to mainMenu
            main_Menu.textBoxTop.delete(1.0, END)
            main_Menu.textBoxTop.insert(END, result[:-1]) # Delete last character


    def __init__(self):
        self.root.title('Text Capture Area')
        self.root.geometry('500x150')
        self.root.wm_attributes('-topmost', True)
        
        # Menubar
        def stay_on_top():
            if self.stayOnTop:
                self.root.wm_attributes('-topmost', False)
                self.stayOnTop = False
            else:
                self.root.wm_attributes('-topmost', True)
                self.stayOnTop = True

        menubar = Menu(self.root)
        filemenu = Menu(menubar, tearoff=0)
        filemenu.add_checkbutton(label="Disable Stay on Top", command=stay_on_top)
        menubar.add_cascade(label="Options", menu=filemenu)

        # Add to self.root
        self.root.config(menu=menubar)

        # Button
        captureBtn = Button(self.root, text="Translate", command=self.getText)
        captureBtn.grid(row=0, column=1, sticky='e')

        # opacity slider # the slider will be added to main menu not here
        opacitySlider = ttk.Scale(self.root, from_=0.01, to=1.0, value=0.8, orient=HORIZONTAL, command=self.sliderOpac)
        opacitySlider.grid(row=0, column=7, sticky='e')

        # On Close
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

class main_Menu():
    capture = CaptureUI()

    root = Tk()
    stayOnTop = False

    textBoxTop = Text(root, height = 5, width = 52, font=("Arial", 10), yscrollcommand=True)

    # On Close
    def on_closing(self):
        exit(0)
    
    # Open Capture Window
    def open_capture_screen(self):
        self.capture.show()

    def __init__(self):
        self.root.title("Screen Translate - Main Menu")
        self.root.geometry("900x300")
        self.root.wm_attributes('-topmost', False) # Default False
        
        # Menubar
        def stay_on_top():
            if self.stayOnTop:
                self.root.wm_attributes('-topmost', False)
                self.stayOnTop = False
            else:
                self.root.wm_attributes('-topmost', True)
                self.stayOnTop = True

        menubar = Menu(self.root)
        filemenu = Menu(menubar, tearoff=0)
        filemenu.add_checkbutton(label="Stay on Top", command=stay_on_top)
        filemenu.add_separator()
        filemenu.add_command(label="Exit Application", command=self.root.quit)
        menubar.add_cascade(label="Options", menu=filemenu)

        filemenu2 = Menu(menubar, tearoff=0)
        filemenu2.add_command(label="History") # Open Mbox Tutorials
        filemenu2.add_command(label="Setting") # Open Mbox Tutorials
        menubar.add_cascade(label="View", menu=filemenu2)

        filemenu3 = Menu(menubar, tearoff=0)
        filemenu3.add_command(label="Capture Window", command=self.open_capture_screen) # Open Mbox Tutorials
        menubar.add_cascade(label="Generate", menu=filemenu3)

        filemenu4 = Menu(menubar, tearoff=0)
        filemenu4.add_command(label="Tutorials") # Open Mbox Tutorials
        filemenu4.add_command(label="FAQ") # Open Mbox Tutorials
        filemenu4.add_separator()
        filemenu4.add_command(label="About") # Open Mbox About
        menubar.add_cascade(label="Help", menu=filemenu4)

        # Add to self.root
        self.root.config(menu=menubar)

        # 
        self.textBoxTop.pack()

        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

main_Menu()
main_Menu.root.mainloop()