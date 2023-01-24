import os
import json
import keyboard
import tkinter as tk
import tkinter.ttk as ttk
from typing import Literal
from tkinter import filedialog, font, colorchooser
from send2trash import send2trash

from .MBox import Mbox
from .Tooltip import CreateToolTip
from screen_translate.Globals import gClass, path_logo_icon, dir_captured, fJson, app_name
from screen_translate.Logging import logger, current_log, dir_log
from screen_translate.utils.Helper import nativeNotify, startFile, tb_copy_only
from screen_translate.utils.Monitor import get_offset, getScreenTotalGeometry
from screen_translate.utils.Capture import seeFullWindow


def chooseColor_entry(theWidget: ttk.Entry, initialColor: str, parent: tk.Toplevel):
    color = colorchooser.askcolor(initialcolor=initialColor, title="Choose a color", parent=parent)
    if color[1] is not None:
        theWidget.delete(0, tk.END)
        theWidget.insert(0, color[1])


def chooseColor_label(theWidget: ttk.Label, initialColor: str, parent: tk.Toplevel, customText=None):
    color = colorchooser.askcolor(initialcolor=initialColor, title="Choose a color", parent=parent)
    if color[1] is not None:
        textRes = customText + " " + color[1] if customText is not None else color[1]
        theWidget.config(text=textRes)


# ----------------------------------------------------------------------
class SettingWindow:
    """Setting Window"""

    # ----------------------------------------------------------------------
    def __init__(self, master: tk.Tk):
        self.root = tk.Toplevel(master)
        self.root.title("Setting")
        self.root.geometry("1110x425")
        self.root.wm_attributes("-topmost", False)  # Default False
        self.root.wm_withdraw()
        self.fonts = font.families()
        self.onStart = True
        gClass.sw = self  # type: ignore

        # ----------------------------------------------------------------------
        # Main frame
        self.f_m_top = tk.Frame(self.root)
        self.f_m_top.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self.f_m_bot = tk.Frame(self.root, bg="#7E7E7E")
        self.f_m_bot.pack(side=tk.BOTTOM, fill=tk.X, pady=(5, 0), padx=5)

        # Left frame for categorization
        self.lf_m_bg_l = tk.LabelFrame(self.f_m_top, text="Menu", labelanchor=tk.N)
        self.lf_m_bg_l.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)

        # Listbox for the category list
        self.lb_cat = tk.Listbox(self.lf_m_bg_l, selectmode=tk.SINGLE, exportselection=False)
        self.lb_cat.pack(side=tk.LEFT, fill=tk.BOTH, padx=5, pady=5)

        self.lb_cat.insert(1, "Capturing/Offset")
        self.lb_cat.insert(2, "OCR Engine/Enhance")
        self.lb_cat.insert(3, "Translate")
        self.lb_cat.insert(4, "Hotkey")
        self.lb_cat.insert(5, "Textbox")
        self.lb_cat.insert(6, "Mask window")
        self.lb_cat.insert(7, "Other")

        # Bind the listbox to the function
        self.lb_cat.bind("<<ListboxSelect>>", self.on_category_select)

        # ----------------------------------------------------------------------
        # * CAT 1 - Capturing/Offset
        self.f_cat_1_cap = ttk.Frame(self.f_m_top)
        self.f_cat_1_cap.pack(side=tk.LEFT, fill=tk.X, padx=5, pady=5, expand=True)

        # -----------------------
        # [Capture Setting]
        self.lf_capture = tk.LabelFrame(self.f_cat_1_cap, text="• Capturing Setting")
        self.lf_capture.pack(side=tk.TOP, fill=tk.X, expand=True, padx=5, pady=(0, 5))

        self.f_capture = tk.Frame(self.lf_capture)
        self.f_capture.pack(side=tk.TOP, fill=tk.X, expand=True)

        self.cbtn_auto_copy = ttk.Checkbutton(self.f_capture, text="Auto Copy Captured Text To Clipboard")
        self.cbtn_auto_copy.pack(side=tk.LEFT, padx=5, pady=5)
        CreateToolTip(self.cbtn_auto_copy, "Copy the captured text to clipboard automatically")

        self.cbtn_keep_img = ttk.Checkbutton(self.f_capture, text="Save Captured Image")
        self.cbtn_keep_img.pack(side=tk.LEFT, padx=5, pady=5)
        CreateToolTip(self.cbtn_keep_img, "Save the captured image to img_captured folder")

        self.btn_open_dir_cap = ttk.Button(self.f_capture, text="🗁 Open Captured Image", command=lambda: startFile(dir_captured))
        self.btn_open_dir_cap.pack(side=tk.LEFT, padx=5, pady=5)

        self.btn_delete_all_cap = ttk.Button(self.f_capture, text="⚠ Delete All Captured Image", command=self.deleteAllCaptured)
        self.btn_delete_all_cap.pack(side=tk.LEFT, padx=5, pady=5)

        # -----------------------
        # [Offset capture window]
        self.lf_cw_offset = tk.LabelFrame(self.f_cat_1_cap, text="• Capture Window Offset")
        self.lf_cw_offset.pack(side=tk.TOP, fill=tk.X, expand=True, padx=5, pady=5)

        self.f_cw_offset_1 = ttk.Frame(self.lf_cw_offset)
        self.f_cw_offset_1.pack(side=tk.TOP, fill=tk.X, expand=True)
        self.f_cw_offset_2 = ttk.Frame(self.lf_cw_offset)
        self.f_cw_offset_2.pack(side=tk.TOP, fill=tk.X, expand=True)
        self.f_cw_offset_3 = ttk.Frame(self.lf_cw_offset)
        self.f_cw_offset_3.pack(side=tk.TOP, fill=tk.X, expand=True)
        self.f_cw_offset_4 = ttk.Frame(self.lf_cw_offset)
        self.f_cw_offset_4.pack(side=tk.TOP, fill=tk.X, expand=True)

        self.lbl_cw_xy_offset = ttk.Label(self.f_cw_offset_1, text="XY Offset :")
        self.lbl_cw_xy_offset.pack(side=tk.LEFT, padx=5, pady=5)
        CreateToolTip(self.lbl_cw_xy_offset, "The offset mode")

        self.cb_cw_xy_offset_type = ttk.Combobox(self.f_cw_offset_1, values=["No Offset", "Custom Offset"], state="readonly")
        self.cb_cw_xy_offset_type.pack(side=tk.LEFT, padx=5, pady=5)
        self.cb_cw_xy_offset_type.bind("<<ComboboxSelected>>", self.cb_xy_offset_change)

        self.btn_cw_check_layout = ttk.Button(self.f_cw_offset_1, text="Click to get A Screenshot of How The Program See Your Monitor", command=self.screenShotAndOpenLayout)
        self.btn_cw_check_layout.pack(side=tk.LEFT, padx=5, pady=5)

        self.lbl_hint_cw_offset = ttk.Label(self.f_cw_offset_1, text="❓")
        self.lbl_hint_cw_offset.pack(side=tk.RIGHT, padx=5, pady=5)
        CreateToolTip(self.lbl_hint_cw_offset, "Set the offset for capturing image. Usually needed if on multiple monitor or if monitor scaling is not 100%")

        self.cbtn_cw_auto_offset_x = ttk.Checkbutton(self.f_cw_offset_2, text="Auto Offset X", command=lambda: self.checkBtnOffset("x"))
        self.cbtn_cw_auto_offset_x.pack(side=tk.LEFT, padx=5, pady=5)

        self.cbtn_cw_auto_offset_y = ttk.Checkbutton(self.f_cw_offset_2, text="Auto Offset Y", command=lambda: self.checkBtnOffset("y"))
        self.cbtn_cw_auto_offset_y.pack(side=tk.LEFT, padx=5, pady=5)

        self.cbtn_cw_auto_offset_w = ttk.Checkbutton(self.f_cw_offset_2, text="Auto Offset W", command=lambda: self.checkBtnOffset("w"))
        self.cbtn_cw_auto_offset_w.pack(side=tk.LEFT, padx=5, pady=5)

        self.cbtn_cw_auto_offset_h = ttk.Checkbutton(self.f_cw_offset_2, text="Auto Offset H", command=lambda: self.checkBtnOffset("h"))
        self.cbtn_cw_auto_offset_h.pack(side=tk.LEFT, padx=5, pady=5)

        # [Offset X]
        self.lbl_cw_offset_x = ttk.Label(self.f_cw_offset_3, text="Offset X :")
        self.lbl_cw_offset_x.pack(side=tk.LEFT, padx=5, pady=5)
        CreateToolTip(self.lbl_cw_offset_x, "X Coordinates offset of the capture window")

        self.sb_cw_offset_x = ttk.Spinbox(self.f_cw_offset_3, from_=-100000, to=100000, width=20)
        self.sb_cw_offset_x.configure(validate="key", validatecommand=(self.root.register(lambda event: self.validateSpinbox(event, self.sb_cw_offset_x)), "%P"))
        self.sb_cw_offset_x.bind("<MouseWheel>", lambda event: self.stop_scroll_if_disabled(event, self.sb_cw_offset_x))
        self.sb_cw_offset_x.pack(side=tk.LEFT, padx=5, pady=5)

        # [Offset Y]
        self.lbl_cw_offset_y = ttk.Label(self.f_cw_offset_4, text="Offset Y :")
        self.lbl_cw_offset_y.pack(side=tk.LEFT, padx=5, pady=5)
        CreateToolTip(self.lbl_cw_offset_y, "Y Coordinates offset of the capture window")

        self.sb_cw_offset_y = ttk.Spinbox(self.f_cw_offset_4, from_=-100000, to=100000, width=20)
        self.sb_cw_offset_y.configure(validate="key", validatecommand=(self.root.register(lambda event: self.validateSpinbox(event, self.sb_cw_offset_y)), "%P"))
        self.sb_cw_offset_y.bind("<MouseWheel>", lambda event: self.stop_scroll_if_disabled(event, self.sb_cw_offset_y))
        self.sb_cw_offset_y.pack(side=tk.LEFT, padx=5, pady=5)

        # [Offset W]
        self.lbl_cw_offset_w = ttk.Label(self.f_cw_offset_3, text="Offset W :")
        self.lbl_cw_offset_w.pack(side=tk.LEFT, padx=5, pady=5)
        CreateToolTip(self.lbl_cw_offset_w, "Width offset of the capture window")

        self.sb_cw_offset_w = ttk.Spinbox(self.f_cw_offset_3, from_=-100000, to=100000, width=20)
        self.sb_cw_offset_w.configure(validate="key", validatecommand=(self.root.register(lambda event: self.validateSpinbox(event, self.sb_cw_offset_w)), "%P"))
        self.sb_cw_offset_w.bind("<MouseWheel>", lambda event: self.stop_scroll_if_disabled(event, self.sb_cw_offset_w))
        self.sb_cw_offset_w.pack(side=tk.LEFT, padx=5, pady=5)

        # [Offset H]
        self.lbl_cw_offset_h = ttk.Label(self.f_cw_offset_4, text="Offset H :")
        self.lbl_cw_offset_h.pack(side=tk.LEFT, padx=5, pady=5)
        CreateToolTip(self.lbl_cw_offset_h, "Height offset of the capture window")

        self.sb_cw_offset_h = ttk.Spinbox(self.f_cw_offset_4, from_=-100000, to=100000, width=20)
        self.sb_cw_offset_h.configure(validate="key", validatecommand=(self.root.register(lambda event: self.validateSpinbox(event, self.sb_cw_offset_h)), "%P"))
        self.sb_cw_offset_h.bind("<MouseWheel>", lambda event: self.stop_scroll_if_disabled(event, theSpinner=self.sb_cw_offset_h))
        self.sb_cw_offset_h.pack(side=tk.LEFT, padx=8, pady=5)

        # -----------------------
        # [Snippet geometry]
        self.lf_snippet_geometry = tk.LabelFrame(self.f_cat_1_cap, text="• Snippet Geometry")
        self.lf_snippet_geometry.pack(side=tk.TOP, fill=tk.X, expand=True, padx=5, pady=5)

        self.f_snippet_geometry = ttk.Frame(self.lf_snippet_geometry)
        self.f_snippet_geometry.pack(side=tk.TOP, fill=tk.X, expand=True)

        self.cbtn_auto_snippet = ttk.Checkbutton(self.f_snippet_geometry, text="Auto Geometry", command=self.check_snippet_offset)
        self.cbtn_auto_snippet.pack(side=tk.LEFT, padx=5, pady=5)
        CreateToolTip(self.cbtn_auto_snippet, text="Auto detect the layout of the monitor (May not work properly)")

        # [total width]
        self.lbl_snippet_total_w = ttk.Label(self.f_snippet_geometry, text="Total Width:")
        self.lbl_snippet_total_w.pack(side=tk.LEFT, padx=(0, 5), pady=0)
        CreateToolTip(self.lbl_snippet_total_w, "Total width of the monitor")

        self.sb_snippet_total_w = ttk.Spinbox(self.f_snippet_geometry, from_=-100000, to=100000, width=7)
        self.sb_snippet_total_w.configure(validate="key", validatecommand=(self.root.register(lambda event: self.validateSpinbox(event, self.sb_snippet_total_w)), "%P"))
        self.sb_snippet_total_w.bind("<MouseWheel>", lambda event: self.stop_scroll_if_disabled(event, theSpinner=self.sb_snippet_total_w))
        self.sb_snippet_total_w.pack(side=tk.LEFT, padx=0, pady=(3, 0))
        CreateToolTip(self.sb_snippet_total_w, "Total width of the monitor")

        # [total height]
        self.lbl_snippet_total_h = ttk.Label(self.f_snippet_geometry, text="Total Height:")
        self.lbl_snippet_total_h.pack(side=tk.LEFT, padx=(5, 0), pady=5)
        CreateToolTip(self.lbl_snippet_total_h, "Total height of the monitor")

        self.sb_snippet_total_h = ttk.Spinbox(self.f_snippet_geometry, from_=-100000, to=100000, width=7)
        self.sb_snippet_total_h.configure(validate="key", validatecommand=(self.root.register(lambda event: self.validateSpinbox(event, self.sb_snippet_total_h)), "%P"))
        self.sb_snippet_total_h.bind("<MouseWheel>", lambda event: self.stop_scroll_if_disabled(event, theSpinner=self.sb_snippet_total_h))
        self.sb_snippet_total_h.pack(side=tk.LEFT, padx=0, pady=(3, 0))
        CreateToolTip(self.sb_snippet_total_h, "Total height of the monitor")

        # [x offset]
        self.lbl_snippet_offset_x = ttk.Label(self.f_snippet_geometry, text="X Offset From Primary:")
        self.lbl_snippet_offset_x.pack(side=tk.LEFT, padx=(5, 0), pady=5)
        CreateToolTip(self.lbl_snippet_offset_x, "X offset of the monitor from the primary monitor")

        self.sb_snippet_offset_x = ttk.Spinbox(self.f_snippet_geometry, from_=-100000, to=100000, width=7)
        self.sb_snippet_offset_x.configure(validate="key", validatecommand=(self.root.register(lambda event: self.validateSpinbox(event, self.sb_snippet_offset_x)), "%P"))
        self.sb_snippet_offset_x.bind("<MouseWheel>", lambda event: self.stop_scroll_if_disabled(event, theSpinner=self.sb_snippet_offset_x))
        self.sb_snippet_offset_x.pack(side=tk.LEFT, padx=0, pady=(3, 0))
        CreateToolTip(self.sb_snippet_offset_x, "X offset of the monitor from the primary monitor")

        # [y offset]
        self.lbl_snippet_offset_y = ttk.Label(self.f_snippet_geometry, text="Y Offset From Primary:")
        self.lbl_snippet_offset_y.pack(side=tk.LEFT, padx=(5, 0), pady=5)
        CreateToolTip(self.lbl_snippet_offset_y, "Y offset of the monitor from the primary monitor")

        self.sb_snippet_offset_y = ttk.Spinbox(self.f_snippet_geometry, from_=-100000, to=100000, width=7)
        self.sb_snippet_offset_y.configure(validate="key", validatecommand=(self.root.register(lambda event: self.validateSpinbox(event, self.sb_snippet_offset_y)), "%P"))
        self.sb_snippet_offset_y.bind("<MouseWheel>", lambda event: self.stop_scroll_if_disabled(event, theSpinner=self.sb_snippet_offset_y))
        self.sb_snippet_offset_y.pack(side=tk.LEFT, padx=0, pady=(3, 0))
        CreateToolTip(self.sb_snippet_offset_y, "Y offset of the monitor from the primary monitor")

        self.lbl_hint_snippet = ttk.Label(self.f_snippet_geometry, text="❓")
        self.lbl_hint_snippet.pack(side=tk.RIGHT, padx=5, pady=5)
        CreateToolTip(
            self.lbl_hint_snippet,
            text="""If the snipping does not match the monitor, then you can manually set the height, width, and offsets.
        \rIf the offset is negative then you need to input (-) before it, if it's positive just leave it as normal
        \rTo get the offset, you need to identify your primary monitor position then you can calculate it by seeing wether the primary monitor is on the first position, in the top, in the middle, or etc.
        \rIf it is in the first position then you might not need any offset, if it's on the second from the left then you might need to add minus offset, etc.""",
        )

        # ----------------------------------------------------------------------
        # * CAT 2 - OCR Engine
        self.f_cat_2_ocr = tk.Frame(self.f_m_top)
        self.f_cat_2_ocr.pack(side=tk.LEFT, fill=tk.BOTH, padx=5, pady=5)

        self.lf_OCR_setting = tk.LabelFrame(self.f_cat_2_ocr, text="• Tesseract OCR Settings")
        self.lf_OCR_setting.pack(side=tk.TOP, fill=tk.X, expand=True, padx=5, pady=(0, 5))

        self.f_OCR_setting = tk.Frame(self.lf_OCR_setting)
        self.f_OCR_setting.pack(side=tk.TOP, fill=tk.X, expand=True)

        self.lbl_OCR_tesseract_path = ttk.Label(self.f_OCR_setting, text="Tesseract Path :")
        self.lbl_OCR_tesseract_path.pack(side=tk.LEFT, padx=5, pady=5)
        CreateToolTip(self.f_OCR_setting, "Tesseract.exe location")

        self.entry_OCR_tesseract_path = ttk.Entry(self.f_OCR_setting, width=70)
        self.entry_OCR_tesseract_path.bind("<Key>", lambda event: tb_copy_only(event))  # Disable textbox input
        self.entry_OCR_tesseract_path.pack(side=tk.LEFT, padx=5, pady=5, fill=tk.X, expand=True)
        CreateToolTip(self.entry_OCR_tesseract_path, "Tesseract.exe location")

        self.btnSearchTesseract = ttk.Button(self.f_OCR_setting, text="...", command=self.searchTesseract)
        self.btnSearchTesseract.pack(side=tk.LEFT, padx=5, pady=5)

        # [Ocr enhancement]
        self.lf_OCR_enhancement = tk.LabelFrame(self.f_cat_2_ocr, text="• OCR Enhancement", width=900, height=75)
        self.lf_OCR_enhancement.pack(side=tk.TOP, fill=tk.X, expand=False, padx=5, pady=5)

        self.f_OCR_enhancement = tk.Frame(self.lf_OCR_enhancement)
        self.f_OCR_enhancement.pack(side=tk.TOP, fill=tk.X, expand=False)

        self.lbl_OCR_cbbg = ttk.Label(self.f_OCR_enhancement, text="Background :")
        self.lbl_OCR_cbbg.pack(side=tk.LEFT, padx=5, pady=5)
        CreateToolTip(self.lbl_OCR_cbbg, "Background type of the area that will be captured. This variable is used only if detect contour using CV2 is checked.")

        self.cb_OCR_bg = ttk.Combobox(self.f_OCR_enhancement, values=["Auto-Detect", "Light", "Dark"], state="readonly")
        self.cb_OCR_bg.pack(side=tk.LEFT, padx=5, pady=5)
        CreateToolTip(self.cb_OCR_bg, "Background type of the area that will be captured. This variable is used only if detect contour using CV2 is checked.")

        self.cbtn_OCR_cv2contour = ttk.Checkbutton(self.f_OCR_enhancement, text="Detect Contour using CV2")
        self.cbtn_OCR_cv2contour.pack(side=tk.LEFT, padx=5, pady=5)
        CreateToolTip(self.cbtn_OCR_cv2contour, text="Enhance the OCR by applying filters and outlining the contour of the words.")

        self.cbtn_OCR_grayscale = ttk.Checkbutton(self.f_OCR_enhancement, text="Grayscale")
        self.cbtn_OCR_grayscale.pack(side=tk.LEFT, padx=5, pady=5)
        CreateToolTip(self.cbtn_OCR_grayscale, text="Enhance the OCR by making the captured picture grayscale on the character reading part.")

        self.cbtn_OCR_debug = ttk.Checkbutton(self.f_OCR_enhancement, text="Debug Mode")
        self.cbtn_OCR_debug.pack(side=tk.LEFT, padx=5, pady=5)
        CreateToolTip(self.cbtn_OCR_debug, text="Enable debug mode.")

        self.lbl_hint_OCR_enhance = ttk.Label(self.f_OCR_enhancement, text="❓")
        self.lbl_hint_OCR_enhance.pack(side=tk.RIGHT, padx=5, pady=5)
        CreateToolTip(
            self.lbl_hint_OCR_enhance,
            text="""Options saved in this section are for the inital value on startup.
        \rYou can experiment with the option to increase the accuracy of tesseract OCR.
        \rThe saved picture will not be affected by the options.""",
        )

        # [Captured Result]
        self.lf_OCR_3 = tk.LabelFrame(self.f_cat_2_ocr, text="• Result", width=900, height=75)
        self.lf_OCR_3.pack(side=tk.TOP, fill=tk.X, expand=False, padx=5, pady=5)

        self.f_OCR_3 = tk.Frame(self.lf_OCR_3)
        self.f_OCR_3.pack(side=tk.TOP, fill=tk.X, expand=False)

        self.lbl_OCR_delete_lastchar = ttk.Label(self.f_OCR_3, text="Delete Last Char :")
        self.lbl_OCR_delete_lastchar.pack(side=tk.LEFT, padx=5, pady=5)
        CreateToolTip(
            self.lbl_OCR_delete_lastchar,
            """The amount of captured word characters to be removed from the last.
        \rWhy? Because sometimes tesseract captured a garbage character that shows up in the last word.
        \rSet this to 0 if it deletes an actual character!""",
        )

        self.sb_OCR_delete_lastchar = ttk.Spinbox(self.f_OCR_3, from_=0, to=25, width=5)
        self.sb_OCR_delete_lastchar.configure(validate="key", validatecommand=(self.root.register(lambda event: self.validateSpinbox(event, self.sb_OCR_delete_lastchar)), "%P"))
        self.sb_OCR_delete_lastchar.pack(side=tk.LEFT, padx=5, pady=5)
        CreateToolTip(
            self.sb_OCR_delete_lastchar,
            """The amount of captured word characters to be removed from the last.
        \rWhy? Because sometimes tesseract captured a garbage character that shows up in the last word.
        \rSet this to 0 if it deletes an actual character!""",
        )

        self.cbtn_OCR_replace_newline = ttk.Checkbutton(self.f_OCR_3, text="Replace New Line")
        self.cbtn_OCR_replace_newline.pack(side=tk.LEFT, padx=5, pady=5)
        CreateToolTip(self.cbtn_OCR_replace_newline, "Replace new line with preferred character.")

        self.entry_OCR_replace_newline_with = ttk.Entry(self.f_OCR_3, width=5)
        self.entry_OCR_replace_newline_with.pack(side=tk.LEFT, padx=5, pady=5)
        CreateToolTip(self.entry_OCR_replace_newline_with, "Character to replace new line.\n Default is ' ' (space). (You can use escape character like \n for new line)")

        # ----------------------------------------------------------------------
        # * CAT 3 - Translate
        self.f_cat_3_tl = tk.Frame(self.f_m_top)
        self.f_cat_3_tl.pack(side=tk.LEFT, fill=tk.BOTH, padx=5, pady=5)

        self.lf_tl_setting = tk.LabelFrame(self.f_cat_3_tl, text="• Translation Settings")
        self.lf_tl_setting.pack(side=tk.TOP, fill=tk.X, expand=True, padx=5, pady=(0, 5))

        self.f_tl_setting_1 = tk.Frame(self.lf_tl_setting)
        self.f_tl_setting_1.pack(side=tk.TOP, fill=tk.X, expand=False)

        self.f_tl_setting_2 = tk.Frame(self.lf_tl_setting)
        self.f_tl_setting_2.pack(side=tk.TOP, fill=tk.X, expand=False)

        self.cbtn_tl_save_history = ttk.Checkbutton(self.f_tl_setting_2, text="Save to History")
        self.cbtn_tl_save_history.pack(side=tk.LEFT, padx=5, pady=5)
        CreateToolTip(self.cbtn_tl_save_history, text="Save the translation to history")

        self.cbtn_alert_no_text = ttk.Checkbutton(self.f_tl_setting_2, text="Show No Text Entered Alert")
        self.cbtn_alert_no_text.pack(side=tk.LEFT, padx=5, pady=5)
        CreateToolTip(self.cbtn_alert_no_text, text="Show alert when no text is entered or captured by the OCR")

        # Libretranslate
        self.lf_tl_libre_setting = tk.LabelFrame(self.f_cat_3_tl, text="• Libretranslate Settings")
        self.lf_tl_libre_setting.pack(side=tk.TOP, fill=tk.X, expand=True, padx=5, pady=(0, 5))

        self.f_tl_libre_setting = tk.Frame(self.lf_tl_libre_setting)
        self.f_tl_libre_setting.pack(side=tk.TOP, fill=tk.X, expand=False)

        self.lbl_tl_libre_setting_key = ttk.Label(self.f_tl_libre_setting, text="API Key :")
        self.lbl_tl_libre_setting_key.pack(side=tk.LEFT, padx=5, pady=5)
        CreateToolTip(self.lbl_tl_libre_setting_key, text="The API key for Libretranslate. Default: Empty.\n\nNot needed unless translating using the libretranslate.com domain/host.")

        self.entry_tl_libre_setting_key = ttk.Entry(self.f_tl_libre_setting)
        self.entry_tl_libre_setting_key.pack(side=tk.LEFT, padx=5, pady=5)
        CreateToolTip(self.entry_tl_libre_setting_key, text="The API key for Libretranslate. Default: Empty.\n\nNot needed unless translating using the libretranslate.com domain/host.")

        self.lbl_tl_libre_setting_host = ttk.Label(self.f_tl_libre_setting, text="Host :")
        self.lbl_tl_libre_setting_host.pack(side=tk.LEFT, padx=5, pady=5)
        CreateToolTip(self.lbl_tl_libre_setting_host, text="Host address of Libletranslate server. Default: libretranslate.de\n\nYou can find full lists of other dedicated server on Libretranslate github repository.")

        self.entry_tl_libre_setting_host = ttk.Entry(self.f_tl_libre_setting)
        self.entry_tl_libre_setting_host.pack(side=tk.LEFT, padx=5, pady=5)
        CreateToolTip(self.entry_tl_libre_setting_host, text="Host address of Libletranslate server. Default: libretranslate.de\n\nYou can find full lists of other dedicated server on Libretranslate github repository.")

        self.lbl_tl_libre_setting_port = ttk.Label(self.f_tl_libre_setting, text="Port :")
        self.lbl_tl_libre_setting_port.pack(side=tk.LEFT, padx=5, pady=5)
        CreateToolTip(self.lbl_tl_libre_setting_port, text="Port of Libletranslate server. Default: Empty\n\nSet it to empty if you are not using local server.")

        self.entry_tl_libre_setting_port = ttk.Entry(self.f_tl_libre_setting)
        self.entry_tl_libre_setting_port.pack(side=tk.LEFT, padx=5, pady=5)
        CreateToolTip(self.entry_tl_libre_setting_port, text="Port of Libletranslate server. Default: Empty\n\nSet it to empty if you are not using local server.")

        self.cbtn_tl_libre_setting_https = ttk.Checkbutton(self.f_tl_libre_setting, text="Use HTTPS")
        self.cbtn_tl_libre_setting_https.pack(side=tk.LEFT, padx=5, pady=5)
        CreateToolTip(self.cbtn_tl_libre_setting_https, text="HTTPS or HTTP. Default: HTTPS (checked)\n\nSet it to http if you are using local server.")

        # ----------------------------------------------------------------------
        # * CAT 4 - Hotkey
        self.f_cat_4_hotkey = tk.Frame(self.f_m_top)
        self.f_cat_4_hotkey.pack(side=tk.LEFT, fill=tk.BOTH, padx=5, pady=5)

        # [Capture Window]
        self.lf_cw_hk = tk.LabelFrame(self.f_cat_4_hotkey, text="• Capture Window Hotkey Settings")
        self.lf_cw_hk.pack(side=tk.TOP, fill=tk.X, expand=True, padx=5, pady=(0, 5))

        self.f_cwh_k = tk.Frame(self.lf_cw_hk)
        self.f_cwh_k.pack(side=tk.TOP, fill=tk.X, expand=False)

        self.lbl_cw_hk_delay = ttk.Label(self.f_cwh_k, text="Time delay (ms) : ")
        self.lbl_cw_hk_delay.pack(side=tk.LEFT, padx=5, pady=5)
        CreateToolTip(self.lbl_cw_hk_delay, text="The time delay to capture when the hotkey is pressed")

        self.sb_cw_hk_delay = ttk.Spinbox(self.f_cwh_k, from_=0, to=100000, width=20)
        self.sb_cw_hk_delay.configure(validate="key", validatecommand=(self.root.register(lambda event: self.validateSpinbox(event, self.sb_cw_hk_delay)), "%P"))
        self.sb_cw_hk_delay.pack(side=tk.LEFT, padx=5, pady=5)

        self.btn_set_cw_hk = tk.Button(self.f_cwh_k, text="Click to set the hotkey", command=self.setHKCapTl)
        self.btn_set_cw_hk.pack(side=tk.LEFT, padx=5, pady=5)

        self.btn_clear_cw_hk = ttk.Button(self.f_cwh_k, text="✕ Clear", command=self.clearHKCapTl)
        self.btn_clear_cw_hk.pack(side=tk.LEFT, padx=5, pady=5)

        self.lbl_cw_hk_is = ttk.Label(self.f_cwh_k, text="Current hotkey : ")
        self.lbl_cw_hk_is.pack(side=tk.LEFT, padx=5, pady=5)
        CreateToolTip(self.lbl_cw_hk_is, text="Currently set hotkey for capturing")

        self.lbl_cw_hk = ttk.Label(self.f_cwh_k, text="")
        self.lbl_cw_hk.pack(side=tk.LEFT, padx=5, pady=5)

        # [Snipping Mode]
        self.lf_snipping_hk = tk.LabelFrame(self.f_cat_4_hotkey, text="• Snipping Mode Hotkey Settings")
        self.lf_snipping_hk.pack(side=tk.TOP, fill=tk.X, expand=True, padx=5, pady=(0, 5))

        self.f_snipping_hk = tk.Frame(self.lf_snipping_hk)
        self.f_snipping_hk.pack(side=tk.TOP, fill=tk.X, expand=False)

        self.lbl_snipping_hk_delay = ttk.Label(self.f_snipping_hk, text="Time delay (ms) : ")
        self.lbl_snipping_hk_delay.pack(side=tk.LEFT, padx=5, pady=5)
        CreateToolTip(self.lbl_cw_hk_delay, text="The time delay to activate snipping mode when the hotkey is pressed")

        self.sb_snipping_hk_delay = ttk.Spinbox(self.f_snipping_hk, from_=0, to=100000, width=20)
        self.sb_snipping_hk_delay.configure(validate="key", validatecommand=(self.root.register(lambda event: self.validateSpinbox(event, self.sb_snipping_hk_delay)), "%P"))
        self.sb_snipping_hk_delay.pack(side=tk.LEFT, padx=5, pady=5)

        self.btn_set_snipping_hk = tk.Button(self.f_snipping_hk, text="Click to set the hotkey", command=self.setHKSnipCapTl)
        self.btn_set_snipping_hk.pack(side=tk.LEFT, padx=5, pady=5)

        self.btn_clear_snipping_hk = ttk.Button(self.f_snipping_hk, text="✕ Clear", command=self.clearHKSnipCapTl)
        self.btn_clear_snipping_hk.pack(side=tk.LEFT, padx=5, pady=5)

        self.lbl_snipping_hk_is = ttk.Label(self.f_snipping_hk, text="Current hotkey : ")
        self.lbl_snipping_hk_is.pack(side=tk.LEFT, padx=5, pady=5)
        CreateToolTip(self.lbl_snipping_hk_is, text="Currently set hotkey for snip & capture")

        self.lbl_snipping_hk = ttk.Label(self.f_snipping_hk, text="")
        self.lbl_snipping_hk.pack(side=tk.LEFT, padx=5, pady=5)

        # ----------------------------------------------------------------------
        # * CAT 5 - Textbox
        self.f_cat_5_textbox = tk.Frame(self.f_m_top)
        self.f_cat_5_textbox.pack(side=tk.LEFT, fill=tk.BOTH, padx=5, pady=5)

        # [mw q]
        self.lf_mw_q = tk.LabelFrame(self.f_cat_5_textbox, text="• Main Window Query Textbox")
        self.lf_mw_q.pack(side=tk.TOP, padx=5, pady=5, fill=tk.X, expand=True)

        self.lbl_mw_q_font = ttk.Label(self.lf_mw_q, text="Font")
        self.lbl_mw_q_font.pack(side=tk.LEFT, padx=5, pady=5)

        self.cb_mw_q_font = ttk.Combobox(self.lf_mw_q, values=self.fonts, state="readonly", width=30)
        self.cb_mw_q_font.pack(side=tk.LEFT, padx=5, pady=5)
        self.cb_mw_q_font.bind("<<ComboboxSelected>>", lambda e: self.preview_changes_tb())

        self.lbl_mw_q_font_size = ttk.Label(self.lf_mw_q, text="Font Size")
        self.lbl_mw_q_font_size.pack(side=tk.LEFT, padx=5, pady=5)

        self.sb_mw_q_font_size = ttk.Spinbox(self.lf_mw_q, from_=3, to=120, width=10)
        self.sb_mw_q_font_size.configure(validate="key", validatecommand=(self.root.register(lambda event: self.validateSpinbox(event, self.sb_mw_q_font_size)), "%P") or self.preview_changes_tb())
        self.sb_mw_q_font_size.bind("<MouseWheel>", lambda event: self.preview_changes_tb())
        self.sb_mw_q_font_size.pack(side=tk.LEFT, padx=5, pady=5)

        self.cbtn_mw_q_font_bold = ttk.Checkbutton(self.lf_mw_q, text="Bold", command=lambda: self.preview_changes_tb())
        self.cbtn_mw_q_font_bold.pack(side=tk.LEFT, padx=5, pady=5)

        self.lbl_mw_q_font_color = ttk.Label(self.lf_mw_q, text="Font Color")
        self.lbl_mw_q_font_color.pack(side=tk.LEFT, padx=5, pady=5)

        self.entry_mw_q_font_color = ttk.Entry(self.lf_mw_q, width=10)
        self.entry_mw_q_font_color.pack(side=tk.LEFT, padx=5, pady=5)
        self.entry_mw_q_font_color.bind("<Button-1>", lambda e: chooseColor_entry(self.entry_mw_q_font_color, self.entry_mw_q_font_color.get(), self.root) or self.preview_changes_tb())
        self.entry_mw_q_font_color.bind("<Key>", lambda e: "break")

        self.lbl_mw_q_bg_color = ttk.Label(self.lf_mw_q, text="Background Color")
        self.lbl_mw_q_bg_color.pack(side=tk.LEFT, padx=5, pady=5)

        self.entry_mw_q_bg_color = ttk.Entry(self.lf_mw_q, width=10)
        self.entry_mw_q_bg_color.pack(side=tk.LEFT, padx=5, pady=5)
        self.entry_mw_q_bg_color.bind(
            "<Button-1>",
            lambda e: chooseColor_entry(self.entry_mw_q_bg_color, self.entry_mw_q_bg_color.get(), self.root) or self.preview_changes_tb(),
        )
        self.entry_mw_q_bg_color.bind("<Key>", lambda e: "break")

        # [mw result]
        self.lf_mw_res = tk.LabelFrame(self.f_cat_5_textbox, text="• Main Window Result Textbox")
        self.lf_mw_res.pack(side=tk.TOP, padx=5, pady=5, fill=tk.X)

        self.lbl_mw_res_font = ttk.Label(self.lf_mw_res, text="Font")
        self.lbl_mw_res_font.pack(side=tk.LEFT, padx=5, pady=5)

        self.cb_mw_res_font = ttk.Combobox(self.lf_mw_res, values=self.fonts, state="readonly", width=30)
        self.cb_mw_res_font.pack(side=tk.LEFT, padx=5, pady=5)
        self.cb_mw_res_font.bind("<<ComboboxSelected>>", lambda e: self.preview_changes_tb())

        self.lbl_mw_res_font_size = ttk.Label(self.lf_mw_res, text="Font Size")
        self.lbl_mw_res_font_size.pack(side=tk.LEFT, padx=5, pady=5)

        self.sb_mw_res_font_size = ttk.Spinbox(self.lf_mw_res, from_=3, to=120, width=10)
        self.sb_mw_res_font_size.configure(validate="key", validatecommand=(self.root.register(lambda event: self.validateSpinbox(event, self.sb_mw_res_font_size)), "%P") or self.preview_changes_tb())
        self.sb_mw_res_font_size.bind("<MouseWheel>", lambda event: self.preview_changes_tb())
        self.sb_mw_res_font_size.pack(side=tk.LEFT, padx=5, pady=5)

        self.cbtn_mw_res_font_bold = ttk.Checkbutton(self.lf_mw_res, text="Bold", command=lambda: self.preview_changes_tb())
        self.cbtn_mw_res_font_bold.pack(side=tk.LEFT, padx=5, pady=5)

        self.lbl_mw_res_font_color = ttk.Label(self.lf_mw_res, text="Font Color")
        self.lbl_mw_res_font_color.pack(side=tk.LEFT, padx=5, pady=5)

        self.entry_mw_res_font_color = ttk.Entry(self.lf_mw_res, width=10)
        self.entry_mw_res_font_color.pack(side=tk.LEFT, padx=5, pady=5)
        self.entry_mw_res_font_color.bind("<Button-1>", lambda e: chooseColor_entry(self.entry_mw_res_font_color, self.entry_mw_res_font_color.get(), self.root) or self.preview_changes_tb())
        self.entry_mw_res_font_color.bind("<Key>", lambda e: "break")

        self.lbl_mw_res_bg_color = ttk.Label(self.lf_mw_res, text="Background Color")
        self.lbl_mw_res_bg_color.pack(side=tk.LEFT, padx=5, pady=5)

        self.entry_mw_res_bg_color = ttk.Entry(self.lf_mw_res, width=10)
        self.entry_mw_res_bg_color.pack(side=tk.LEFT, padx=5, pady=5)
        self.entry_mw_res_bg_color.bind("<Button-1>", lambda e: chooseColor_entry(self.entry_mw_res_bg_color, self.entry_mw_res_bg_color.get(), self.root) or self.preview_changes_tb())
        self.entry_mw_res_bg_color.bind("<Key>", lambda e: "break")

        # [detached query]
        self.lf_ex_q = tk.LabelFrame(self.f_cat_5_textbox, text="• Detached Query Window Textbox")
        self.lf_ex_q.pack(side=tk.TOP, padx=5, pady=5, fill=tk.X, expand=True)

        self.lbl_ex_q_font = ttk.Label(self.lf_ex_q, text="Font")
        self.lbl_ex_q_font.pack(side=tk.LEFT, padx=5, pady=5)

        self.cb_ex_q_font = ttk.Combobox(self.lf_ex_q, values=self.fonts, state="readonly", width=30)
        self.cb_ex_q_font.pack(side=tk.LEFT, padx=5, pady=5)
        self.cb_ex_q_font.bind("<<ComboboxSelected>>", lambda e: self.preview_changes_tb())

        self.lbl_ex_q_font_size = ttk.Label(self.lf_ex_q, text="Font Size")
        self.lbl_ex_q_font_size.pack(side=tk.LEFT, padx=5, pady=5)

        self.sb_ex_q_font_size = ttk.Spinbox(self.lf_ex_q, from_=3, to=120, width=10)
        self.sb_ex_q_font_size.configure(validate="key", validatecommand=(self.root.register(lambda event: self.validateSpinbox(event, self.sb_ex_q_font_size)), "%P") or self.preview_changes_tb())
        self.sb_ex_q_font_size.bind("<MouseWheel>", lambda event: self.preview_changes_tb())
        self.sb_ex_q_font_size.pack(side=tk.LEFT, padx=5, pady=5)

        self.cbtn_ex_q_font_bold = ttk.Checkbutton(self.lf_ex_q, text="Bold", command=lambda: self.preview_changes_tb())
        self.cbtn_ex_q_font_bold.pack(side=tk.LEFT, padx=5, pady=5)

        self.lbl_ex_q_font_color = ttk.Label(self.lf_ex_q, text="Font Color")
        self.lbl_ex_q_font_color.pack(side=tk.LEFT, padx=5, pady=5)

        self.entry_ex_q_font_color = ttk.Entry(self.lf_ex_q, width=10)
        self.entry_ex_q_font_color.pack(side=tk.LEFT, padx=5, pady=5)
        self.entry_ex_q_font_color.bind("<Button-1>", lambda e: chooseColor_entry(self.entry_ex_q_font_color, self.entry_ex_q_font_color.get(), self.root) or self.preview_changes_tb())
        self.entry_ex_q_font_color.bind("<Key>", lambda e: "break")

        self.lbl_ex_q_bg_color = ttk.Label(self.lf_ex_q, text="Background Color")
        self.lbl_ex_q_bg_color.pack(side=tk.LEFT, padx=5, pady=5)

        self.entry_ex_q_bg_color = ttk.Entry(self.lf_ex_q, width=10)
        self.entry_ex_q_bg_color.pack(side=tk.LEFT, padx=5, pady=5)
        self.entry_ex_q_bg_color.bind("<Button-1>", lambda e: chooseColor_entry(self.entry_ex_q_bg_color, self.entry_ex_q_bg_color.get(), self.root) or self.preview_changes_tb())
        self.entry_ex_q_bg_color.bind("<Key>", lambda e: "break")

        # [detached result]
        self.lf_ex_res = tk.LabelFrame(self.f_cat_5_textbox, text="• Detached Result Window Textbox")
        self.lf_ex_res.pack(side=tk.TOP, padx=5, pady=5, fill=tk.X)

        self.lbl_ex_res_font = ttk.Label(self.lf_ex_res, text="Font")
        self.lbl_ex_res_font.pack(side=tk.LEFT, padx=5, pady=5)

        self.cb_ex_res_font = ttk.Combobox(self.lf_ex_res, values=self.fonts, state="readonly", width=30)
        self.cb_ex_res_font.pack(side=tk.LEFT, padx=5, pady=5)
        self.cb_ex_res_font.bind("<<ComboboxSelected>>", lambda e: self.preview_changes_tb())

        self.lbl_ex_res_font_size = ttk.Label(self.lf_ex_res, text="Font Size")
        self.lbl_ex_res_font_size.pack(side=tk.LEFT, padx=5, pady=5)

        self.sb_ex_res_font_size = ttk.Spinbox(self.lf_ex_res, from_=3, to=120, width=10)
        self.sb_ex_res_font_size.configure(validate="key", validatecommand=(self.root.register(lambda event: self.validateSpinbox(event, self.sb_ex_res_font_size)), "%P") or self.preview_changes_tb())
        self.sb_ex_res_font_size.bind("<MouseWheel>", lambda event: self.preview_changes_tb())
        self.sb_ex_res_font_size.pack(side=tk.LEFT, padx=5, pady=5)

        self.cbtn_ex_res_font_bold = ttk.Checkbutton(self.lf_ex_res, text="Bold", command=lambda: self.preview_changes_tb())
        self.cbtn_ex_res_font_bold.pack(side=tk.LEFT, padx=5, pady=5)

        self.lbl_ex_res_font_color = ttk.Label(self.lf_ex_res, text="Font Color")
        self.lbl_ex_res_font_color.pack(side=tk.LEFT, padx=5, pady=5)

        self.entry_ex_res_font_color = ttk.Entry(self.lf_ex_res, width=10)
        self.entry_ex_res_font_color.pack(side=tk.LEFT, padx=5, pady=5)
        self.entry_ex_res_font_color.bind("<Button-1>", lambda e: chooseColor_entry(self.entry_ex_res_font_color, self.entry_ex_res_font_color.get(), self.root) or self.preview_changes_tb())
        self.entry_ex_res_font_color.bind("<Key>", lambda e: "break")

        self.lbl_ex_res_bg_color = ttk.Label(self.lf_ex_res, text="Background Color")
        self.lbl_ex_res_bg_color.pack(side=tk.LEFT, padx=5, pady=5)

        self.entry_ex_res_bg_color = ttk.Entry(self.lf_ex_res, width=10)
        self.entry_ex_res_bg_color.pack(side=tk.LEFT, padx=5, pady=5)
        self.entry_ex_res_bg_color.bind("<Button-1>", lambda e: chooseColor_entry(self.entry_ex_res_bg_color, self.entry_ex_res_bg_color.get(), self.root) or self.preview_changes_tb())
        self.entry_ex_res_bg_color.bind("<Key>", lambda e: "break")

        # [previews]
        self.f_tb_preview = ttk.Frame(self.f_cat_5_textbox)
        self.f_tb_preview.pack(side=tk.TOP, fill=tk.X, pady=5)

        self.tb_preview_1 = tk.Text(
            self.f_tb_preview,
            height=5,
            width=27,
            wrap=tk.WORD,
            font=(fJson.settingCache["tb_mw_q_font"], fJson.settingCache["tb_mw_q_font_size"], "bold" if fJson.settingCache["tb_mw_q_font_bold"] else "normal"),
            fg=fJson.settingCache["tb_mw_q_font_color"],
            bg=fJson.settingCache["tb_mw_q_bg_color"],
        )
        self.tb_preview_1.bind("<Key>", "break")
        self.tb_preview_1.insert(tk.END, "1234567 Preview プレビュー 预习 предварительный просмотр")
        self.tb_preview_1.pack(side=tk.LEFT, padx=5, pady=5, fill=tk.BOTH, expand=True)

        self.tb_preview_2 = tk.Text(
            self.f_tb_preview,
            height=5,
            width=27,
            wrap=tk.WORD,
            font=(fJson.settingCache["tb_mw_res_font"], fJson.settingCache["tb_mw_res_font_size"], "bold" if fJson.settingCache["tb_mw_res_font_bold"] else "normal"),
            fg=fJson.settingCache["tb_mw_res_font_color"],
            bg=fJson.settingCache["tb_mw_res_bg_color"],
        )
        self.tb_preview_2.bind("<Key>", "break")
        self.tb_preview_2.insert(tk.END, "1234567 Preview プレビュー 预习 предварительный просмотр")
        self.tb_preview_2.pack(side=tk.LEFT, padx=5, pady=5, fill=tk.BOTH, expand=True)

        self.tb_preview_3 = tk.Text(
            self.f_tb_preview,
            height=5,
            width=27,
            wrap=tk.WORD,
            font=(fJson.settingCache["tb_ex_q_font"], fJson.settingCache["tb_ex_q_font_size"], "bold" if fJson.settingCache["tb_ex_q_font_bold"] else "normal"),
            fg=fJson.settingCache["tb_ex_q_font_color"],
            bg=fJson.settingCache["tb_ex_q_bg_color"],
        )
        self.tb_preview_3.bind("<Key>", "break")
        self.tb_preview_3.insert(tk.END, "1234567 Preview プレビュー 预习 предварительный просмотр")
        self.tb_preview_3.pack(side=tk.LEFT, padx=5, pady=5, fill=tk.BOTH, expand=True)

        self.tb_preview_4 = tk.Text(
            self.f_tb_preview,
            height=5,
            width=27,
            wrap=tk.WORD,
            font=(fJson.settingCache["tb_ex_res_font"], fJson.settingCache["tb_ex_res_font_size"], "bold" if fJson.settingCache["tb_ex_res_font_bold"] else "normal"),
            fg=fJson.settingCache["tb_ex_res_font_color"],
            bg=fJson.settingCache["tb_ex_res_bg_color"],
        )
        self.tb_preview_4.bind("<Key>", "break")
        self.tb_preview_4.insert(tk.END, "1234567 Preview プレビュー 预习 предварительный просмотр")
        self.tb_preview_4.pack(side=tk.LEFT, padx=5, pady=5, fill=tk.BOTH, expand=True)

        # ----------------------------------------------------------------------
        # * CAT 6 - Mask window
        self.f_cat_6_maskwindow = tk.Frame(self.f_m_top)
        self.f_cat_6_maskwindow.pack(side=tk.LEFT, fill=tk.BOTH, padx=5, pady=5)

        self.lf_maskwindow = tk.LabelFrame(self.f_cat_6_maskwindow, text="• Mask Window")
        self.lf_maskwindow.pack(side=tk.TOP, fill=tk.X, expand=True, padx=5, pady=5)

        self.f_maskwindow = tk.Frame(self.lf_maskwindow)
        self.f_maskwindow.pack(side=tk.TOP, fill=tk.X, expand=True)

        self.lbl_maskwindow_color = ttk.Label(self.f_maskwindow, text="Color : ")
        self.lbl_maskwindow_color.pack(side=tk.LEFT, padx=5, pady=5)
        CreateToolTip(self.lbl_maskwindow_color, "Set mask window color")

        self.entry_maskwindow_color = ttk.Entry(self.f_maskwindow, width=10)
        self.entry_maskwindow_color.pack(side=tk.LEFT, padx=5, pady=5)
        self.entry_maskwindow_color.bind("<Button-1>", lambda e: chooseColor_entry(self.entry_maskwindow_color, self.entry_maskwindow_color.get(), self.root) or self.preview_changes_tb())
        self.entry_maskwindow_color.bind("<Key>", lambda e: "break")

        self.lbl_hint_maskwindow = ttk.Label(self.f_maskwindow, text="❓")
        self.lbl_hint_maskwindow.pack(padx=5, pady=5, side=tk.RIGHT)
        CreateToolTip(self.lbl_hint_maskwindow, "Settings for mask window")

        # ----------------------------------------------------------------------
        # * CAT 7 - Other
        self.f_cat_7_other = tk.Frame(self.f_m_top)
        self.f_cat_7_other.pack(side=tk.LEFT, fill=tk.BOTH, padx=5, pady=5)

        self.lf_other = tk.LabelFrame(self.f_cat_7_other, text="• Other Settings")
        self.lf_other.pack(side=tk.TOP, fill=tk.X, expand=True, padx=5, pady=(0, 5))

        self.f_other_1 = tk.Frame(self.lf_other)
        self.f_other_1.pack(side=tk.TOP, fill=tk.X, expand=False)

        self.f_other_2 = tk.Frame(self.lf_other)
        self.f_other_2.pack(side=tk.TOP, fill=tk.X, expand=False)

        # Checkbox for check for update
        self.cbtn_update = ttk.Checkbutton(self.f_other_1, text="Check for update on app start")
        self.cbtn_update.pack(side=tk.LEFT, padx=5, pady=5)
        CreateToolTip(self.cbtn_update, "Check for update on app start. You can also check manually by going to help in menubar")

        self.cbtn_keep_log = ttk.Checkbutton(self.f_other_2, text="Keep Log")
        self.cbtn_keep_log.pack(side=tk.LEFT, padx=(5, 4), pady=(4, 6))

        self.lbl_loglevel = ttk.Label(self.f_other_2, text="Log Level : ")
        self.lbl_loglevel.pack(side=tk.LEFT, padx=0, pady=5)

        self.cb_log_level = ttk.Combobox(self.f_other_2, values=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], state="readonly")
        self.cb_log_level.pack(side=tk.LEFT, padx=0, pady=5)

        # ----------------------------------------------------------------
        # Bottom tk.Frame
        # Create a bottom frame to hold the buttons
        self.bottomFrame = tk.Frame(self.f_m_bot)
        self.bottomFrame.pack(side=tk.BOTTOM, fill=tk.X, pady=(1, 0))

        # Create the buttons
        self.btnSave = ttk.Button(self.bottomFrame, text="🖪 Save Settings", command=self.saveSettings)
        self.btnSave.pack(side=tk.RIGHT, padx=4, pady=5)

        self.btnReset = ttk.Button(self.bottomFrame, text="⟳ Cancel Changes", command=self.reset_changes)
        self.btnReset.pack(side=tk.RIGHT, padx=5, pady=5)

        self.btnRestoreDefault = ttk.Button(self.bottomFrame, text="⚠ Restore Default", command=self.restoreDefault)
        self.btnRestoreDefault.pack(side=tk.RIGHT, padx=5, pady=5)

        # ----------------------------------------------------------------
        # On Close
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.onInit()

    # ----------------------------------------------------------------
    # Functions
    # ----------------------------------------------------------------
    def onInit(self):
        self.hideAllFrame()
        self.lb_cat.select_set(0)
        self.showFrame(self.f_cat_1_cap)
        self.deleteCapturedOnStart()
        self.deleteLogOnStart()
        self.init_setting()
        self.onStart = False

    def show(self):
        self.root.wm_deiconify()

    def on_closing(self):
        self.root.wm_withdraw()

    def stop_scroll_if_disabled(self, event, theSpinner: ttk.Spinbox):
        if str(theSpinner["state"]) == "disabled":
            return "break"

    def on_category_select(self, _event=None):
        """On Select for frame changing

        Args:
            event ([type]): Ignored click event
        """
        if self.lb_cat.curselection() == ():
            return

        sel_dict = {
            0: self.f_cat_1_cap,
            1: self.f_cat_2_ocr,
            2: self.f_cat_3_tl,
            3: self.f_cat_4_hotkey,
            4: self.f_cat_5_textbox,
            5: self.f_cat_6_maskwindow,
            6: self.f_cat_7_other,
        }

        self.hideAllFrame()
        self.showFrame(sel_dict[self.lb_cat.curselection()[0]])

    def hideAllFrame(self):
        """
        Hide all frames
        """
        self.f_cat_1_cap.pack_forget()
        self.f_cat_2_ocr.pack_forget()
        self.f_cat_3_tl.pack_forget()
        self.f_cat_4_hotkey.pack_forget()
        self.f_cat_5_textbox.pack_forget()
        self.f_cat_6_maskwindow.pack_forget()
        self.f_cat_7_other.pack_forget()

    def showFrame(self, frame):
        """Change frame for each setting

        Args:
            frame ([type]): The frame that will be displayed
        """
        frame.pack(side=tk.LEFT, fill=tk.BOTH, padx=5, pady=5)

    def cbtnInvoker(self, settingVal: bool, widget: ttk.Checkbutton):
        if self.onStart:
            if settingVal:
                widget.invoke()
            else:
                widget.invoke()
                widget.invoke()
        else:
            if settingVal and not widget.instate(["selected"]):
                widget.invoke()
            elif not settingVal and widget.instate(["selected"]):
                widget.invoke()

    def deleteLogOnStart(self):
        if not fJson.settingCache["keep_log"]:
            self.deleteTheLog()

    def deleteCapturedOnStart(self):
        if not fJson.settingCache["keep_image"]:
            self.deleteCaptured()

    def deleteTheLog(self):
        # delete all log files
        for file in os.listdir(dir_log):
            if file.endswith(".log"):
                try:
                    os.remove(os.path.join(dir_log, file))
                except Exception as e:
                    if file != current_log:  # show warning only if the fail to delete is not the current log
                        logger.warning("Failed to delete log file: " + file)
                        logger.warning("Reason " + str(e))

    def deleteCaptured(self):
        # delete all temp wav files
        for file in os.listdir(dir_captured):
            if file.endswith(".png"):
                try:
                    os.remove(os.path.join(dir_captured, file))
                except Exception as e:
                    logger.warning("Failed to delete image file: " + file)
                    logger.warning("Reason " + str(e))

    def reset_changes(self):
        if not Mbox("Confirmation", "Are you sure you want to reset all changes?", 3, self.root):
            return
        logger.info("Reset all changes")
        self.init_setting()

    def restoreDefault(self):
        """
        Restore default settings
        """
        if not Mbox("Confirmation", "Are you sure you want to set the settings to default?\n\n**WARNING! CURRENTLY SAVED SETTING WILL BE OVERWRITTEN**", 3, self.root):
            return

        # Restore Default Settings
        success, msg = fJson.setDefaultSetting()
        if success:
            # Unbind all hotkeys (default hotkey is empty)
            try:
                keyboard.unhook_all_hotkeys()
            except AttributeError:
                # No hotkeys to unbind
                pass

            # Update the settings
            self.init_setting()

            # Tell success
            logger.info("Restored Default Settings")
            Mbox("Success", "Successfully Restored Value to Default Settings", 0, self.root)
        else:
            logger.error("Error resetting setting file to default: " + msg)
            Mbox("Error resetting setting file to default", "Reason: " + msg, 2, self.root)

    def init_setting(self):
        """
        Reset the settings to currently stored settings
        """
        # If tesseract is not found
        if not os.path.exists(fJson.settingCache["tesseract_loc"]):
            nativeNotify("Error: Set tesseract Not Found!", "Please set tesseract location in Setting.json.\nYou can set this in setting menu or modify it manually in json/Setting.json", path_logo_icon, app_name)

        self.cbtnInvoker(fJson.settingCache["keep_image"], self.cbtn_keep_img)
        self.cbtnInvoker(fJson.settingCache["auto_copy"], self.cbtn_auto_copy)

        # cw
        # xy cw offset
        self.cb_cw_xy_offset_type.set(fJson.settingCache["offSetXYType"])
        self.cb_xy_offset_change()  # update xy cw offset

        # wh cw offset
        self.check_wh_offset()

        # snippet
        self.cbtnInvoker(fJson.settingCache["snippingWindowGeometry"] == "auto", self.cbtn_auto_snippet)

        # OCR
        self.entry_OCR_tesseract_path.delete(0, tk.END)
        self.entry_OCR_tesseract_path.insert(0, fJson.settingCache["tesseract_loc"])

        self.cb_OCR_bg.set(fJson.settingCache["enhance_background"])
        self.cbtnInvoker(fJson.settingCache["enhance_with_cv2_Contour"], self.cbtn_OCR_cv2contour)
        self.cbtnInvoker(fJson.settingCache["enhance_with_grayscale"], self.cbtn_OCR_grayscale)
        self.cbtnInvoker(fJson.settingCache["enhance_debugmode"], self.cbtn_OCR_debug)

        self.sb_OCR_delete_lastchar.set(fJson.settingCache["captureLastValDelete"])
        self.cbtnInvoker(fJson.settingCache["replaceNewLine"], self.cbtn_OCR_replace_newline)
        self.entry_OCR_replace_newline_with.delete(0, tk.END)
        self.entry_OCR_replace_newline_with.insert(0, fJson.settingCache["replaceNewLineWith"])

        # tl
        self.cbtnInvoker(fJson.settingCache["save_history"], self.cbtn_tl_save_history)
        self.cbtnInvoker(not fJson.settingCache["supress_no_text_alert"], self.cbtn_alert_no_text)

        self.entry_tl_libre_setting_key.delete(0, tk.END)
        self.entry_tl_libre_setting_key.insert(0, fJson.settingCache["libre_api_key"])

        self.entry_tl_libre_setting_host.delete(0, tk.END)
        self.entry_tl_libre_setting_host.insert(0, fJson.settingCache["libre_host"])

        self.entry_tl_libre_setting_port.delete(0, tk.END)
        self.entry_tl_libre_setting_port.insert(0, fJson.settingCache["libre_port"])

        self.cbtnInvoker(fJson.settingCache["libre_https"], self.cbtn_tl_libre_setting_https)

        # hk
        self.sb_cw_hk_delay.set(fJson.settingCache["hk_cap_window_delay"])
        self.lbl_cw_hk.config(text=fJson.settingCache["hk_cap_window"])

        self.sb_snipping_hk_delay.set(fJson.settingCache["hk_snip_cap_delay"])
        self.lbl_snipping_hk.config(text=fJson.settingCache["hk_snip_cap"])

        # textbox
        self.init_tb_settings()

        # mask window
        self.entry_maskwindow_color.delete(0, tk.END)
        self.entry_maskwindow_color.insert(0, fJson.settingCache["mask_window_color"])

        # other
        self.cbtnInvoker(fJson.settingCache["checkUpdateOnStart"], self.cbtn_update)
        self.cbtnInvoker(fJson.settingCache["keep_log"], self.cbtn_keep_log)
        self.cb_log_level.set(fJson.settingCache["log_level"])

        logger.info("Settings loaded to setting UI")

    def tb_delete(self):
        self.entry_mw_q_font_color.delete(0, tk.END)
        self.entry_mw_q_bg_color.delete(0, tk.END)

        self.entry_mw_res_font_color.delete(0, tk.END)
        self.entry_mw_res_bg_color.delete(0, tk.END)

        self.entry_ex_q_font_color.delete(0, tk.END)
        self.entry_ex_q_bg_color.delete(0, tk.END)

        self.entry_ex_res_font_color.delete(0, tk.END)
        self.entry_ex_res_bg_color.delete(0, tk.END)

    def init_tb_settings(self):
        self.tb_delete()
        self.cb_mw_q_font.set(fJson.settingCache["tb_mw_q_font"])
        self.sb_mw_q_font_size.set(fJson.settingCache["tb_mw_q_font_size"])
        self.cbtnInvoker(fJson.settingCache["tb_mw_q_font_bold"], self.cbtn_mw_q_font_bold)
        self.entry_mw_q_font_color.insert(0, fJson.settingCache["tb_mw_q_font_color"])
        self.entry_mw_q_bg_color.insert(0, fJson.settingCache["tb_mw_q_bg_color"])

        self.cb_mw_res_font.set(fJson.settingCache["tb_mw_res_font"])
        self.sb_mw_res_font_size.set(fJson.settingCache["tb_mw_res_font_size"])
        self.cbtnInvoker(fJson.settingCache["tb_mw_res_font_bold"], self.cbtn_mw_res_font_bold)
        self.entry_mw_res_font_color.insert(0, fJson.settingCache["tb_mw_res_font_color"])
        self.entry_mw_res_bg_color.insert(0, fJson.settingCache["tb_mw_res_bg_color"])

        self.cb_ex_q_font.set(fJson.settingCache["tb_ex_q_font"])
        self.sb_ex_q_font_size.set(fJson.settingCache["tb_ex_q_font_size"])
        self.cbtnInvoker(fJson.settingCache["tb_ex_q_font_bold"], self.cbtn_ex_q_font_bold)
        self.entry_ex_q_font_color.insert(0, fJson.settingCache["tb_ex_q_font_color"])
        self.entry_ex_q_bg_color.insert(0, fJson.settingCache["tb_ex_q_bg_color"])

        self.cb_ex_res_font.set(fJson.settingCache["tb_ex_res_font"])
        self.sb_ex_res_font_size.set(fJson.settingCache["tb_ex_res_font_size"])
        self.cbtnInvoker(fJson.settingCache["tb_ex_res_font_bold"], self.cbtn_ex_res_font_bold)
        self.entry_ex_res_font_color.insert(0, fJson.settingCache["tb_ex_res_font_color"])
        self.entry_ex_res_bg_color.insert(0, fJson.settingCache["tb_ex_res_bg_color"])

    def preview_changes_tb(self):
        if self.onStart:
            return

        self.tb_preview_1.config(
            font=(self.cb_mw_q_font.get(), int(self.sb_mw_q_font_size.get()), "bold" if self.cbtn_mw_q_font_bold.instate(["selected"]) else "normal"),
            fg=self.entry_mw_q_font_color.get(),
            bg=self.entry_mw_q_bg_color.get(),
        )

        self.tb_preview_2.config(
            font=(self.cb_mw_res_font.get(), int(self.sb_mw_res_font_size.get()), "bold" if self.cbtn_mw_res_font_bold.instate(["selected"]) else "normal"),
            fg=self.entry_mw_res_font_color.get(),
            bg=self.entry_mw_res_bg_color.get(),
        )

        self.tb_preview_3.config(
            font=(self.cb_ex_q_font.get(), int(self.sb_ex_q_font_size.get()), "bold" if self.cbtn_ex_q_font_bold.instate(["selected"]) else "normal"),
            fg=self.entry_ex_q_font_color.get(),
            bg=self.entry_ex_q_bg_color.get(),
        )

        self.tb_preview_4.config(
            font=(self.cb_ex_res_font.get(), int(self.sb_ex_res_font_size.get()), "bold" if self.cbtn_ex_res_font_bold.instate(["selected"]) else "normal"),
            fg=self.entry_ex_res_font_color.get(),
            bg=self.entry_ex_res_bg_color.get(),
        )

    # Save settings
    def saveSettings(self):
        """
        Save settings to file
        """
        # Check path tesseract
        tesseractPathInput = self.entry_OCR_tesseract_path.get().strip().lower()

        # # If tesseract is not found
        if not os.path.exists(tesseractPathInput):
            logger.warn("Tesseract Not Found Error")
            Mbox("Error: Tesseract not found", "Invalid Path Provided For Tesseract!", 2, self.root)
            return

        setting_collections = {
            "checkUpdateOnStart": self.cbtn_update.instate(["selected"]),
            # ------------------ #
            # App settings
            "keep_image": self.cbtn_keep_img.instate(["selected"]),
            "auto_copy": self.cbtn_auto_copy.instate(["selected"]),
            "save_history": self.cbtn_tl_save_history.instate(["selected"]),
            "supress_no_text_alert": not self.cbtn_alert_no_text.instate(["selected"]),  # Inverted
            # ------------------ #
            # logging
            "keep_log": self.cbtn_keep_log.instate(["selected"]),
            "log_level": self.cb_log_level.get(),  # INFO DEBUG WARNING ERROR
            # ------------------ #
            # capture window offsets
            "offSetXYType": self.cb_cw_xy_offset_type.get(),
            "offSetX": int(self.sb_cw_offset_x.get()) if self.cbtn_cw_auto_offset_x.instate(["selected"]) == False else "auto",
            "offSetY": int(self.sb_cw_offset_y.get()) if self.cbtn_cw_auto_offset_y.instate(["selected"]) == False else "auto",
            "offSetW": int(self.sb_cw_offset_w.get()) if self.cbtn_cw_auto_offset_w.instate(["selected"]) == False else "auto",
            "offSetH": int(self.sb_cw_offset_h.get()) if self.cbtn_cw_auto_offset_h.instate(["selected"]) == False else "auto",
            # ------------------ #
            # snipping window geometry
            "snippingWindowGeometry": "auto" if self.cbtn_auto_snippet.instate(["selected"]) else f"{self.sb_snippet_total_w.get()}x{self.sb_snippet_total_h.get()}+{self.sb_snippet_offset_x.get()}+{self.sb_snippet_offset_y.get()}",  # type: ignore
            # ------------------ #
            # Capture
            "tesseract_loc": tesseractPathInput,
            "replaceNewLine": self.cbtn_OCR_replace_newline.instate(["selected"]),
            "replaceNewLineWith": self.entry_OCR_replace_newline_with.get(),
            "captureLastValDelete": self.sb_OCR_delete_lastchar.get(),
            # capture enhancement
            "enhance_background": self.cb_OCR_bg.get(),
            "enhance_with_cv2_Contour": self.cbtn_OCR_cv2contour.instate(["selected"]),
            "enhance_with_grayscale": self.cbtn_OCR_grayscale.instate(["selected"]),
            "enhance_debugmode": self.cbtn_OCR_debug.instate(["selected"]),
            # ------------------ #
            # mask window
            "mask_window_bg_color": self.entry_maskwindow_color.get(),
            # ------------------ #
            # libre
            "libre_api_key": self.entry_tl_libre_setting_key.get(),
            "libre_host": self.entry_tl_libre_setting_host.get(),
            "libre_port": self.entry_tl_libre_setting_port.get(),
            "libre_https": self.cbtn_tl_libre_setting_https.instate(["selected"]),
            # ------------------ #
            # hotkey
            "hk_cap_window": self.lbl_cw_hk.cget("text"),
            "hk_cap_window_delay": int(self.sb_cw_hk_delay.get()),
            "hk_snip_cap": self.lbl_snipping_hk.cget("text"),
            "hk_snip_cap_delay": int(self.sb_snipping_hk_delay.get()),
            # ------------------ #
            # detached window
            "tb_mw_q_font": self.cb_mw_q_font.get(),
            "tb_mw_q_font_bold": self.cbtn_mw_q_font_bold.instate(["selected"]),
            "tb_mw_q_font_size": int(self.sb_mw_q_font_size.get()),
            "tb_mw_q_font_color": self.entry_mw_q_font_color.get(),
            "tb_mw_q_bg_color": self.entry_mw_q_bg_color.get(),
            "tb_mw_res_font": self.cb_mw_res_font.get(),
            "tb_mw_res_font_bold": self.cbtn_mw_res_font_bold.instate(["selected"]),
            "tb_mw_res_font_size": int(self.sb_mw_res_font_size.get()),
            "tb_mw_res_font_color": self.entry_mw_res_font_color.get(),
            "tb_mw_res_bg_color": self.entry_mw_res_bg_color.get(),
            "tb_ex_q_font": self.cb_ex_q_font.get(),
            "tb_ex_q_font_bold": self.cbtn_ex_q_font_bold.instate(["selected"]),
            "tb_ex_q_font_size": int(self.sb_ex_q_font_size.get()),
            "tb_ex_q_font_color": self.entry_ex_q_font_color.get(),
            "tb_ex_q_bg_color": self.entry_ex_q_bg_color.get(),
            "tb_ex_res_font": self.cb_ex_res_font.get(),
            "tb_ex_res_font_bold": self.cbtn_ex_res_font_bold.instate(["selected"]),
            "tb_ex_res_font_size": int(self.sb_ex_res_font_size.get()),
            "tb_ex_res_font_color": self.entry_ex_res_font_color.get(),
            "tb_ex_res_bg_color": self.entry_ex_res_bg_color.get(),
            "mask_window_color": self.entry_maskwindow_color.get(),
        }

        # Unbind all hotkey
        try:
            keyboard.unhook_all_hotkeys()
        except AttributeError:
            # No hotkeys to unbind
            pass

        # Bind hotkey
        if self.lbl_cw_hk.cget("text") != "":
            keyboard.add_hotkey(self.lbl_cw_hk["text"], gClass.hk_cap_window_callback)

        if self.lbl_snipping_hk.cget("text") != "":
            keyboard.add_hotkey(self.lbl_snipping_hk["text"], gClass.hk_snip_mode_callback)

        # update log level
        if fJson.settingCache["log_level"] != self.cb_log_level.get():
            logger.setLevel(self.cb_log_level.get())

        logger.info("-" * 50)
        logger.info("Saving setting")
        statusMsg = ""
        errorAmount = 0

        for key, val in setting_collections.items():
            check = fJson.savePartialSetting(key, val)
            if not check[0]:
                errorAmount += 1

        # update external
        self.updateExternal()

        if errorAmount > 0:
            statusMsg = "No error"
        else:
            statusMsg = f"{errorAmount} error(s) encountered"

        Mbox("Success", f"Saved settings with {statusMsg}", 0, self.root)

    def updateInternal(self):
        self.cb_OCR_bg.set(fJson.settingCache["enhance_background"])
        self.cbtnInvoker(fJson.settingCache["enhance_with_cv2_Contour"], self.cbtn_OCR_cv2contour)
        self.cbtnInvoker(fJson.settingCache["enhance_with_grayscale"], self.cbtn_OCR_grayscale)
        self.cbtnInvoker(fJson.settingCache["enhance_debugmode"], self.cbtn_OCR_debug)

        self.entry_maskwindow_color.delete(0, tk.END)
        self.entry_maskwindow_color.insert(0, fJson.settingCache["mask_window_color"])

    def updateExternal(self):
        assert gClass.mw is not None
        gClass.mw.tb_query.config(
            font=(self.cb_mw_q_font.get(), int(self.sb_mw_q_font_size.get()), "bold" if self.cbtn_mw_q_font_bold.instate(["selected"]) else "normal"),
            fg=self.entry_mw_q_font_color.get(),
            bg=self.entry_mw_q_bg_color.get(),
        )

        gClass.mw.tb_result.config(
            font=(self.cb_mw_res_font.get(), int(self.sb_mw_res_font_size.get()), "bold" if self.cbtn_mw_res_font_bold.instate(["selected"]) else "normal"),
            fg=self.entry_mw_res_font_color.get(),
            bg=self.entry_mw_res_bg_color.get(),
        )

        assert gClass.ex_qw is not None
        gClass.ex_qw.labelText.config(
            font=(self.cb_ex_q_font.get(), int(self.sb_ex_q_font_size.get()), "bold" if self.cbtn_ex_q_font_bold.instate(["selected"]) else "normal"),
            fg=self.entry_ex_q_font_color.get(),
            bg=self.entry_ex_q_bg_color.get(),
        )

        assert gClass.ex_resw is not None
        gClass.ex_resw.labelText.config(
            font=(self.cb_ex_res_font.get(), int(self.sb_ex_res_font_size.get()), "bold" if self.cbtn_ex_res_font_bold.instate(["selected"]) else "normal"),
            fg=self.entry_ex_res_font_color.get(),
            bg=self.entry_ex_res_bg_color.get(),
        )

        assert gClass.cw is not None
        toUpdate = {
            "enhance_background": self.cb_OCR_bg.get(),
            "enhance_with_cv2_Contour": self.cbtn_OCR_cv2contour.instate(["selected"]),
            "enhance_with_grayscale": self.cbtn_OCR_grayscale.instate(["selected"]),
            "enhance_debugmode": self.cbtn_OCR_debug.instate(["selected"]),
        }
        gClass.cw.updateInternal(toUpdate)

        assert gClass.mask is not None
        gClass.mask.updateInternal(self.entry_maskwindow_color.get())

    # --------------------------------------------------
    # Offset capturing settings
    def checkBtnOffset(self, offSetType: Literal["x", "y", "w", "h"]):
        """Set the state & value for each spinner

        Args:
            offSetType (Literal["x", "y", "w", "h"]): The type of offset
        """
        settingVal = {"x": fJson.settingCache["offSetX"], "y": fJson.settingCache["offSetY"], "w": fJson.settingCache["offSetW"], "h": fJson.settingCache["offSetH"]}
        cbtns = {"x": self.cbtn_cw_auto_offset_x, "y": self.cbtn_cw_auto_offset_y, "w": self.cbtn_cw_auto_offset_w, "h": self.cbtn_cw_auto_offset_h}
        spinners = {"x": self.sb_cw_offset_x, "y": self.sb_cw_offset_y, "w": self.sb_cw_offset_w, "h": self.sb_cw_offset_h}
        cbtnval = cbtns[offSetType].instate(["selected"])

        if cbtnval:  # if auto
            offsets = get_offset(offSetType)
            spinners[offSetType].config(state=tk.DISABLED)
            spinners[offSetType].set(offsets)
        else:
            spinners[offSetType].config(state=tk.NORMAL)
            spinners[offSetType].set(settingVal[offSetType])

    # ----------------------------------------------------------------
    # Engine
    # Search for tesseract
    def searchTesseract(self):
        """
        Search for tesseract by opening a file dialog
        """
        res = filedialog.askopenfilename(initialdir="/", title="Select file", filetypes=(("tesseract.exe", "*.exe"), ("all files", "*.*")))
        if res != "":
            self.entry_OCR_tesseract_path.delete(0, tk.END)
            self.entry_OCR_tesseract_path.insert(0, res)

    # ----------------------------------------------------------------
    # Hotkey
    def setHKCapTl(self):
        """
        Set the hotkey for capturing and translating
        """
        hotkey = keyboard.read_hotkey(suppress=False)
        self.lbl_cw_hk.config(text=str(hotkey))

    def clearHKCapTl(self):
        """
        Clear the hotkey for capturing and translating
        """
        self.lbl_cw_hk.config(text="")

    def setHKSnipCapTl(self):
        """
        Set the hotkey for snipping and translate
        """
        hotkey = keyboard.read_hotkey(suppress=False)
        self.lbl_snipping_hk.config(text=str(hotkey))

    def clearHKSnipCapTl(self):
        """
        Clear the hotkey for snipping and translate
        """
        self.lbl_snipping_hk.config(text="")

    # ----------------------------------------------------------------
    # Capture
    def screenShotAndOpenLayout(self):
        """
        Fully capture the window and open the image
        """
        seeFullWindow()

    # ----------------------------------------------------------------
    def cb_xy_offset_change(self, event=None):
        """offset cb

        Args:
            event: Ignored. Defaults to None.
        """
        xyOffSetType = self.cb_cw_xy_offset_type.get()

        # Check offset or not
        if xyOffSetType == "No Offset":  # No offset means auto
            self.cbtnInvoker(False, self.cbtn_cw_auto_offset_x)
            self.cbtnInvoker(False, self.cbtn_cw_auto_offset_y)

            # Disable spinner and the selector, also set stuff in spinner to 0
            self.cbtn_cw_auto_offset_x.config(state=tk.DISABLED)
            self.cbtn_cw_auto_offset_y.config(state=tk.DISABLED)
            self.sb_cw_offset_x.config(state=tk.DISABLED)
            self.sb_cw_offset_y.config(state=tk.DISABLED)

            # set sb value 0
            self.sb_cw_offset_x.set(0)
            self.sb_cw_offset_y.set(0)
        else:  # auto
            # enable changes
            self.cbtn_cw_auto_offset_x.config(state=tk.NORMAL)
            self.cbtn_cw_auto_offset_y.config(state=tk.NORMAL)

            # if x auto
            if fJson.settingCache["offSetX"] == "auto":
                self.cbtnInvoker(True, self.cbtn_cw_auto_offset_x)
                self.sb_cw_offset_x.config(state=tk.DISABLED)
            else:
                self.cbtnInvoker(False, self.cbtn_cw_auto_offset_x)
                self.sb_cw_offset_x.config(state=tk.NORMAL)

            # if y auto
            if fJson.settingCache["offSetY"] == "auto":
                self.cbtnInvoker(True, self.cbtn_cw_auto_offset_y)
                self.sb_cw_offset_y.config(state=tk.DISABLED)
            else:
                self.cbtnInvoker(False, self.cbtn_cw_auto_offset_y)
                self.sb_cw_offset_y.config(state=tk.NORMAL)

            # set value
            self.sb_cw_offset_x.set(get_offset("x"))
            self.sb_cw_offset_y.set(get_offset("y"))

    def check_wh_offset(self):
        if fJson.settingCache["offSetW"] == "auto":
            self.cbtnInvoker(True, self.cbtn_cw_auto_offset_w)
        else:
            self.cbtnInvoker(False, self.cbtn_cw_auto_offset_w)

        if fJson.settingCache["offSetH"] == "auto":
            self.cbtnInvoker(True, self.cbtn_cw_auto_offset_h)
        else:
            self.cbtnInvoker(False, self.cbtn_cw_auto_offset_h)

        self.sb_cw_offset_w.set(get_offset("w"))
        self.sb_cw_offset_h.set(get_offset("h"))

    def check_snippet_offset(self, event=None):
        """Disable/Enable the snip spinbox

        Args:
            event : Ignored. Defaults to None.
        """
        if not self.cbtn_auto_snippet.instate(["selected"]):  # IF disabled then enable it
            self.sb_snippet_total_w.config(state=tk.NORMAL)
            self.sb_snippet_total_h.config(state=tk.NORMAL)
            self.sb_snippet_offset_x.config(state=tk.NORMAL)
            self.sb_snippet_offset_y.config(state=tk.NORMAL)
        else:
            self.sb_snippet_total_w.config(state=tk.DISABLED)
            self.sb_snippet_total_h.config(state=tk.DISABLED)
            self.sb_snippet_offset_x.config(state=tk.DISABLED)
            self.sb_snippet_offset_y.config(state=tk.DISABLED)

        res = getScreenTotalGeometry(False)
        self.sb_snippet_total_w.set(res[1])
        self.sb_snippet_total_h.set(res[2])
        self.sb_snippet_offset_x.set(res[3])
        self.sb_snippet_offset_y.set(res[4])

    # ----------------------------------------------------------------
    # Spinbox validation
    def validateSpinbox(self, event, theSpinner):
        """Validate the spinbox

        Args:
            event: spinbox event
            theSpinner: the spinbox

        Returns:
            allowing the spinbox to be changed or not
        """
        if event == "":
            theSpinner.set(0)
            return False

        try:
            event = int(event)
            # Fetching minimum and maximum value of the spinbox
            minval = int(self.root.nametowidget(theSpinner).config("from")[4])
            maxval = int(self.root.nametowidget(theSpinner).config("to")[4])

            # check if the number is within the range
            if event not in range(minval, maxval):
                # if not, set the value to the nearest limit
                if event < minval:
                    theSpinner.set(minval)
                else:
                    theSpinner.set(maxval)
                return False

            # if all is well, return True
            return True
        except Exception:  # Except means that number is not a digit
            return False

    def deleteAllCaptured(self, event=None):
        """Delete all the cap images

        Args:
            event : Ignored. Defaults to None.
        """
        # Ask for confirmation first
        if Mbox("Confirmation", "Are you sure you want to delete all captured images?", 3, self.root):
            try:
                for file in os.listdir(dir_captured):
                    if file.endswith(".png"):
                        send2trash(os.path.join(dir_captured, file))

                Mbox("Success", "All captured images have been deleted successfully.", 0, self.root)
            except Exception as e:
                logger.warning("Failed to delete image file")
                logger.exception(e)
                Mbox("Error deleting images", f"Reason: {str(e)}", 2, self.root)
