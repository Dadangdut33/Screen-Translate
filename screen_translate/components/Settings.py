import os
import json
from typing import Literal, Optional
import keyboard
import tkinter as tk
import tkinter.ttk as ttk
from tkinter import filedialog
from send2trash import send2trash


from .MBox import Mbox
from .Tooltip import CreateToolTip
from screen_translate.Globals import gClass, path_logo_icon, dir_captured, fJson
from screen_translate.Logging import logger, current_log, dir_log
from screen_translate.utils.Helper import startFile, tb_copy_only
from screen_translate.utils.Monitor import get_offset, getScreenTotalGeometry
from screen_translate.utils.Capture import seeFullWindow

# ----------------------------------------------------------------------
class SettingWindow:
    """Setting Window"""

    # ----------------------------------------------------------------------
    def __init__(self, master):
        self.root = tk.Toplevel(master)
        self.root.title("Setting")
        self.root.geometry("1110x425")
        self.root.wm_attributes("-topmost", False)  # Default False
        self.root.wm_withdraw()

        # ----------------------------------------------------------------------
        # Main frame
        self.f_m_top = tk.Frame(self.root)
        self.f_m_top.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self.f_m_bot = tk.Frame(self.root, bg="#7E7E7E")
        self.f_m_bot.pack(side=tk.BOTTOM, fill=tk.X, pady=(5, 0), padx=5)

        # Left frame for categorization
        self.f_m_bg_l = tk.LabelFrame(self.f_m_top, text="Menu", labelanchor=tk.N)
        self.f_m_bg_l.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)

        # Listbox for the category list
        self.lb_cat = tk.Listbox(self.f_m_bg_l, selectmode=tk.SINGLE, exportselection=False)
        self.lb_cat.pack(side=tk.LEFT, fill=tk.BOTH, padx=5, pady=5)

        self.lb_cat.insert(1, "Capturing/Offset")
        self.lb_cat.insert(2, "OCR Engine/Enhance")
        self.lb_cat.insert(3, "Translate")
        self.lb_cat.insert(4, "Hotkey")
        self.lb_cat.insert(5, "Query/Result Box")
        self.lb_cat.insert(6, "Mask window")
        self.lb_cat.insert(7, "Other")

        # Bind the listbox to the function
        self.lb_cat.bind("<<ListboxSelect>>", self.onSelect)

        # ----------------------------------------------------------------------
        # * CAT 1 - Capturing/Offset
        self.f_cat_1 = tk.Frame(self.f_m_top)
        self.f_cat_1.pack(side=tk.LEFT, fill=tk.BOTH, padx=5, pady=5)

        # -----------------------
        # [Capture Setting]
        self.lf_capture = tk.LabelFrame(self.f_cat_1, text="• Capturing Setting")
        self.lf_capture.pack(side=tk.TOP, fill=tk.X, expand=True, padx=5, pady=(0, 5))
        self.f_capture_1 = tk.Frame(self.lf_capture)
        self.f_capture_1.pack(side=tk.TOP, fill=tk.X, expand=False)

        self.cb_autocopy = ttk.Checkbutton(self.f_capture_1, text="Auto Copy Captured Text To Clipboard")
        self.cb_autocopy.pack(side=tk.LEFT, padx=5, pady=5)
        CreateToolTip(self.cb_autocopy, "Copy the captured text to clipboard automatically")

        self.cb_saveimg = ttk.Checkbutton(self.f_capture_1, text="Save Captured Image")
        self.cb_saveimg.pack(side=tk.LEFT, padx=5, pady=5)
        CreateToolTip(self.cb_saveimg, "Save the captured image to img_captured folder")

        self.btn_open_dir_cap = ttk.Button(self.f_capture_1, text="🗁 Open Captured Image", command=lambda: startFile(dir_captured))
        self.btn_open_dir_cap.pack(side=tk.LEFT, padx=5, pady=5)

        self.btn_delete_all_cap = ttk.Button(self.f_capture_1, text="⚠ Delete All Captured Image", command=self.deleteAllCapImg)
        self.btn_delete_all_cap.pack(side=tk.LEFT, padx=5, pady=5)

        # -----------------------
        # [Offset capture window]
        self.lf_cw_offset = tk.LabelFrame(self.f_cat_1, text="• Capture Window Offset")
        self.lf_cw_offset.pack(side=tk.TOP, fill=tk.X, expand=True, padx=5, pady=5)

        self.f_cw_offset_1 = tk.Frame(self.lf_cw_offset)
        self.f_cw_offset_1.pack(side=tk.TOP, fill=tk.X, expand=False)
        self.f_cw_offset_2 = tk.Frame(self.lf_cw_offset)
        self.f_cw_offset_2.pack(side=tk.TOP, fill=tk.X, expand=False)
        self.f_cw_offset_3 = tk.Frame(self.lf_cw_offset)
        self.f_cw_offset_3.pack(side=tk.TOP, fill=tk.X, expand=False)
        self.f_cw_offset_4 = tk.Frame(self.lf_cw_offset)
        self.f_cw_offset_4.pack(side=tk.TOP, fill=tk.X, expand=False)

        self.lbl_cw_xy_offset = ttk.Label(self.f_cw_offset_1, text="XY Offset :")
        self.lbl_cw_xy_offset.pack(side=tk.LEFT, padx=5, pady=5)
        CreateToolTip(self.lbl_cw_xy_offset, "The offset mode")

        self.cb_cw_offset = ttk.Combobox(self.f_cw_offset_1, values=["No Offset", "Custom Offset"], state="readonly")
        self.cb_cw_offset.pack(side=tk.LEFT, padx=5, pady=5)
        self.cb_cw_offset.bind("<<ComboboxSelected>>", self.CBOffSetChange)

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
        # [Snippet offset]
        self.lf_snippet_offset = tk.LabelFrame(self.f_cat_1, text="• Snippet Offset")
        self.lf_snippet_offset.pack(side=tk.TOP, fill=tk.X, expand=True, padx=5, pady=5)

        self.f_snippet_offset_1 = tk.Frame(self.lf_snippet_offset)
        self.f_snippet_offset_1.pack(side=tk.TOP, fill=tk.X, expand=False)

        self.cbtn_auto_snippet = ttk.Checkbutton(self.f_snippet_offset_1, text="Auto", command=self.disableEnableSnipSpin)
        self.cbtn_auto_snippet.pack(side=tk.LEFT, padx=5, pady=5)
        CreateToolTip(self.cbtn_auto_snippet, text="Auto detect the layout of the monitor (May not work properly)")

        # [total width]
        self.lbl_snippet_total_w = ttk.Label(self.f_snippet_offset_1, text="Total Width:")
        self.lbl_snippet_total_w.pack(side=tk.LEFT, padx=(0, 5), pady=0)
        CreateToolTip(self.lbl_snippet_total_w, "Total width of the monitor")

        self.sb_snippet_total_w = ttk.Spinbox(self.f_snippet_offset_1, from_=-100000, to=100000, width=7)
        self.sb_snippet_total_w.configure(validate="key", validatecommand=(self.root.register(lambda event: self.validateSpinbox(event, self.sb_snippet_total_w)), "%P"))
        self.sb_snippet_total_w.bind("<MouseWheel>", lambda event: self.stop_scroll_if_disabled(event, theSpinner=self.sb_snippet_total_w))
        self.sb_snippet_total_w.pack(side=tk.LEFT, padx=0, pady=(3, 0))
        CreateToolTip(self.sb_snippet_total_w, "Total width of the monitor")

        # [total height]
        self.lbl_snippet_total_h = ttk.Label(self.f_snippet_offset_1, text="Total Height:")
        self.lbl_snippet_total_h.pack(side=tk.LEFT, padx=(5, 0), pady=5)
        CreateToolTip(self.lbl_snippet_total_h, "Total height of the monitor")

        self.sb_snippet_total_h = ttk.Spinbox(self.f_snippet_offset_1, from_=-100000, to=100000, width=7)
        self.sb_snippet_total_h.configure(validate="key", validatecommand=(self.root.register(lambda event: self.validateSpinbox(event, self.sb_snippet_total_h)), "%P"))
        self.sb_snippet_total_h.bind("<MouseWheel>", lambda event: self.stop_scroll_if_disabled(event, theSpinner=self.sb_snippet_total_h))
        self.sb_snippet_total_h.pack(side=tk.LEFT, padx=0, pady=(3, 0))
        CreateToolTip(self.sb_snippet_total_h, "Total height of the monitor")

        # [x offset]
        self.lbl_snippet_offset_x = ttk.Label(self.f_snippet_offset_1, text="X Offset From Primary:")
        self.lbl_snippet_offset_x.pack(side=tk.LEFT, padx=(5, 0), pady=5)
        CreateToolTip(self.lbl_snippet_offset_x, "X offset of the monitor from the primary monitor")

        self.sb_snippet_offset_x = ttk.Spinbox(self.f_snippet_offset_1, from_=-100000, to=100000, width=7)
        self.sb_snippet_offset_x.configure(validate="key", validatecommand=(self.root.register(lambda event: self.validateSpinbox(event, self.sb_snippet_offset_x)), "%P"))
        self.sb_snippet_offset_x.bind("<MouseWheel>", lambda event: self.stop_scroll_if_disabled(event, theSpinner=self.sb_snippet_offset_x))
        self.sb_snippet_offset_x.pack(side=tk.LEFT, padx=0, pady=(3, 0))
        CreateToolTip(self.sb_snippet_offset_x, "X offset of the monitor from the primary monitor")

        # [y offset]
        self.lbl_snippet_offset_y = ttk.Label(self.f_snippet_offset_1, text="Y Offset From Primary:")
        self.lbl_snippet_offset_y.pack(side=tk.LEFT, padx=(5, 0), pady=5)
        CreateToolTip(self.lbl_snippet_offset_y, "Y offset of the monitor from the primary monitor")

        self.sb_snippet_offset_y = ttk.Spinbox(self.f_snippet_offset_1, from_=-100000, to=100000, width=7)
        self.sb_snippet_offset_y.configure(validate="key", validatecommand=(self.root.register(lambda event: self.validateSpinbox(event, self.sb_snippet_offset_y)), "%P"))
        self.sb_snippet_offset_y.bind("<MouseWheel>", lambda event: self.stop_scroll_if_disabled(event, theSpinner=self.sb_snippet_offset_y))
        self.sb_snippet_offset_y.pack(side=tk.LEFT, padx=0, pady=(3, 0))
        CreateToolTip(self.sb_snippet_offset_y, "tk.Y offset of the monitor from the primary monitor")

        self.lbl_hint_snippet = ttk.Label(self.f_snippet_offset_1, text="❓")
        self.lbl_hint_snippet.pack(side=tk.RIGHT, padx=5, pady=5)
        CreateToolTip(
            self.lbl_hint_snippet,
            text="""If the snipping does not match the monitor, then you can manually set the height, width, and offsets.
        \rIf the offset is negative then you need to input (-) before it, if it's positive just leave it as normal
        \rTo get the offset, you need to identify your primary monitor position then you can calculate it by seeing wether the primary monitor is on the first position, in the top, in the middle, or etc.
        \rIf it is in the first position then you might not need any offset, if it's on the second from the left then you might need to add minus offset, etc.""",
        )

        # ----------------------------------------------------------------------
        # * CAT 1 - OCR Engine
        self.f_cat_2 = tk.Frame(self.f_m_top)
        self.f_cat_2.pack(side=tk.LEFT, fill=tk.BOTH, padx=5, pady=5)

        self.fLabelOCR_1 = LabelFrame(self.f_cat_2, text="• Tesseract OCR Settings", width=900, height=75)
        self.fLabelOCR_1.pack(side=tk.TOP, fill=tk.X, expand=False, padx=5, pady=(0, 5))
        self.fLabelOCR_1.pack_propagate(0)
        self.content_Engine_1 = tk.Frame(self.fLabelOCR_1)
        self.content_Engine_1.pack(side=tk.TOP, fill=tk.X, expand=False)

        self.labelTesseractPath = Label(self.content_Engine_1, text="Tesseract Path :")
        self.labelTesseractPath.pack(side=tk.LEFT, padx=5, pady=5)
        CreateToolTip(self.content_Engine_1, "Tesseract.exe location")

        self.textBoxTesseractPath = ttk.Entry(self.content_Engine_1, width=70, xscrollcommand=True)
        self.textBoxTesseractPath.bind("<Key>", lambda event: _StoredGlobal.allowedKey(event))  # Disable textbox input
        self.textBoxTesseractPath.pack(side=tk.LEFT, padx=5, pady=5, fill=tk.X, expand=True)
        CreateToolTip(self.textBoxTesseractPath, "Tesseract.exe location")

        self.btnSearchTesseract = ttk.Button(self.content_Engine_1, text="...", command=self.searchTesseract)
        self.btnSearchTesseract.pack(side=tk.LEFT, padx=5, pady=5)

        # [Ocr enhancement]
        self.fLabelOCR_2 = LabelFrame(self.f_cat_2, text="• OCR Enhancement", width=900, height=75)
        self.fLabelOCR_2.pack(side=tk.TOP, fill=tk.X, expand=False, padx=5, pady=5)
        self.fLabelOCR_2.pack_propagate(0)

        self.content_Enhance_1 = tk.Frame(self.fLabelOCR_2)
        self.content_Enhance_1.pack(side=tk.TOP, fill=tk.X, expand=False)

        self.checkVarCV2 = BooleanVar(self.root, value=True)
        self.checkVarGrayscale = BooleanVar(self.root, value=False)
        self.checkVarDebugmode = BooleanVar(self.root, value=False)

        self.labelCBBackground = Label(self.content_Enhance_1, text="Background :")
        self.labelCBBackground.pack(side=tk.LEFT, padx=5, pady=5)
        CreateToolTip(self.labelCBBackground, "Background type of the area that will be captured. This variable is used only if detect contour using CV2 is checked.")

        self.CBBackgroundType = ttk.Combobox(self.content_Enhance_1, values=["Auto-Detect", "Light", "Dark"], state="readonly")
        self.CBBackgroundType.pack(side=tk.LEFT, padx=5, pady=5)
        CreateToolTip(self.CBBackgroundType, "Background type of the area that will be captured. This variable is used only if detect contour using CV2 is checked.")

        self.checkCV2 = ttk.Checkbutton(self.content_Enhance_1, text="Detect Contour using CV2", variable=self.checkVarCV2)
        self.checkCV2.pack(side=tk.LEFT, padx=5, pady=5)
        CreateToolTip(self.checkCV2, text="Enhance the OCR by applying filters and outlining the contour of the words.")

        self.checkGrayscale = ttk.Checkbutton(self.content_Enhance_1, text="Grayscale", variable=self.checkVarGrayscale)
        self.checkGrayscale.pack(side=tk.LEFT, padx=5, pady=5)
        CreateToolTip(self.checkGrayscale, text="Enhance the OCR by making the captured picture grayscale on the character reading part.")

        self.checkDebugmode = ttk.Checkbutton(self.content_Enhance_1, text="Debug Mode", variable=self.checkVarDebugmode)
        self.checkDebugmode.pack(side=tk.LEFT, padx=5, pady=5)
        CreateToolTip(self.checkDebugmode, text="Enable debug mode.")

        self.hintLabelEnhance = Label(self.content_Enhance_1, text="❓")
        self.hintLabelEnhance.pack(side=tk.RIGHT, padx=5, pady=5)
        CreateToolTip(
            self.hintLabelEnhance,
            text="""Options saved in this section are for the inital value on startup.
        \rYou can experiment with the option to increase the accuracy of tesseract OCR.
        \rThe saved picture will not be affected by the options.""",
        )

        self.fLabelOCR_3 = LabelFrame(self.f_cat_2, text="• Misc", width=900, height=75)
        self.fLabelOCR_3.pack(side=tk.TOP, fill=tk.X, expand=False, padx=5, pady=5)

        self.content_Misc_1 = tk.Frame(self.fLabelOCR_3)
        self.content_Misc_1.pack(side=tk.TOP, fill=tk.X, expand=False)

        self.labelSpinValDel = Label(self.content_Misc_1, text="Delete Last Char :")
        self.labelSpinValDel.pack(side=tk.LEFT, padx=5, pady=5)
        CreateToolTip(
            self.labelSpinValDel,
            """The amount of captured word characters to be removed from the last.
        \rWhy? Because sometimes tesseract captured a garbage character that shows up in the last word.
        \rSet this to 0 if it deletes an actual character!""",
        )

        self.valDelLastChar = IntVar(self.root)
        self.spinnerDelLastChar = ttk.Spinbox(self.content_Misc_1, from_=0, to=10, width=5, textvariable=self.valDelLastChar)
        self.spinnerDelLastChar.pack(side=tk.LEFT, padx=5, pady=5)
        CreateToolTip(
            self.spinnerDelLastChar,
            """The amount of captured word characters to be removed from the last.
        \rWhy? Because sometimes tesseract captured a garbage character that shows up in the last word.
        \rSet this to 0 if it deletes an actual character!""",
        )

        self.replaceNewLineVar = BooleanVar(self.root, value=True)
        self.checkReplaceNewLine = ttk.Checkbutton(self.content_Misc_1, text="Replace New Line", variable=self.replaceNewLineVar)
        self.checkReplaceNewLine.pack(side=tk.LEFT, padx=5, pady=5)
        CreateToolTip(self.checkReplaceNewLine, "Replace new line with space.")

        self.validateDigits_SpinDel = (self.root.register(lambda event: self.validateSpinbox(event, self.spinnerDelLastChar)), "%P")
        self.spinnerDelLastChar.configure(validate="key", validatecommand=self.validateDigits_SpinDel)

        # ----------------------------------------------------------------------
        # Translate
        self.frameTranslate = tk.Frame(self.f_m_top)
        self.frameTranslate.pack(side=tk.LEFT, fill=tk.BOTH, padx=5, pady=5)

        self.fLabelTl_1 = LabelFrame(self.frameTranslate, text="• Translation Settings", width=900, height=100)
        self.fLabelTl_1.pack(side=tk.TOP, fill=tk.X, expand=False, padx=5, pady=(0, 5))
        self.fLabelTl_1.pack_propagate(0)

        self.content_Tl_1 = tk.Frame(self.fLabelTl_1)
        self.content_Tl_1.pack(side=tk.TOP, fill=tk.X, expand=False)

        self.content_Tl_2 = tk.Frame(self.fLabelTl_1)
        self.content_Tl_2.pack(side=tk.TOP, fill=tk.X, expand=False)

        self.fLabelTl_2 = LabelFrame(self.frameTranslate, text="• Libretranslate Settings", width=900, height=75)
        self.fLabelTl_2.pack(side=tk.TOP, fill=tk.X, expand=False, padx=5, pady=(0, 5))
        self.fLabelTl_2.pack_propagate(0)

        self.content_Tl_3 = tk.Frame(self.fLabelTl_2)
        self.content_Tl_3.pack(side=tk.TOP, fill=tk.X, expand=False)

        self.langOpt = optGoogle
        self.labelDefaultEngine = Label(self.content_Tl_1, text="Default TL Engine :")
        self.labelDefaultEngine.pack(side=tk.LEFT, padx=5, pady=5)
        CreateToolTip(self.labelDefaultEngine, text="The default translation engine on program startup")

        self.CBDefaultEngine = ttk.Combobox(self.content_Tl_1, values=engines, state="readonly")
        self.CBDefaultEngine.pack(side=tk.LEFT, padx=5, pady=5)
        self.CBDefaultEngine.bind("<<ComboboxSelected>>", self.CBTLChange_setting)

        self.labelDefaultFrom = Label(self.content_Tl_1, text="Default From :")
        self.labelDefaultFrom.pack(side=tk.LEFT, padx=5, pady=5)
        CreateToolTip(self.labelDefaultFrom, text="The default language to translate from on program startup")

        self.CBDefaultFrom = ttk.Combobox(self.content_Tl_1, values=self.langOpt, state="readonly")
        self.CBDefaultFrom.pack(side=tk.LEFT, padx=5, pady=5)

        self.labelDefaultTo = Label(self.content_Tl_1, text="Default To :")
        self.labelDefaultTo.pack(side=tk.LEFT, padx=5, pady=5)
        CreateToolTip(self.labelDefaultTo, text="The default language to translate to on program startup")

        self.CBDefaultTo = ttk.Combobox(self.content_Tl_1, values=self.langOpt, state="readonly")
        self.CBDefaultTo.pack(side=tk.LEFT, padx=5, pady=5)

        self.saveToHistoryVar = BooleanVar(self.root, value=True)
        self.checkSaveToHistory = ttk.Checkbutton(self.content_Tl_2, variable=self.saveToHistoryVar, text="Save to History")
        self.checkSaveToHistory.pack(side=tk.LEFT, padx=5, pady=5)
        CreateToolTip(self.checkSaveToHistory, text="Save the translation to history")

        self.showNoTextAlertVar = BooleanVar(self.root, value=True)
        self.checkShowNoTextAlert = ttk.Checkbutton(self.content_Tl_2, variable=self.showNoTextAlertVar, text="Show No Text Entered Alert")
        self.checkShowNoTextAlert.pack(side=tk.LEFT, padx=5, pady=5)
        CreateToolTip(self.checkShowNoTextAlert, text="Show alert when no text is entered or captured by the OCR")

        # Libretranslate
        self.labelKeys = Label(self.content_Tl_3, text="API Key :")
        self.labelKeys.pack(side=tk.LEFT, padx=5, pady=5)
        CreateToolTip(self.labelKeys, text="The API key for Libretranslate. Default: Empty.\n\nNot needed unless translating using the libretranslate.com domain/host.")

        self.libreTlKey = StringVar(self.root)
        self.libreTlKey.set("")
        self.entryKeys = ttk.Entry(self.content_Tl_3, textvariable=self.libreTlKey)
        self.entryKeys.pack(side=tk.LEFT, padx=5, pady=5)
        CreateToolTip(self.entryKeys, text="The API key for Libretranslate. Default: Empty.\n\nNot needed unless translating using the libretranslate.com domain/host.")

        self.labelHost = Label(self.content_Tl_3, text="Host :")
        self.labelHost.pack(side=tk.LEFT, padx=5, pady=5)
        CreateToolTip(self.labelHost, text="Host address of Libletranslate server. Default: localhost\n\nYou can find full lists of other dedicated server on Libretranslate github repository.")

        self.libreTlHost = StringVar(self.root)
        self.libreTlHost.set("localhost")
        self.entryLibleTlHost = ttk.Entry(self.content_Tl_3, textvariable=self.libreTlHost)
        self.entryLibleTlHost.pack(side=tk.LEFT, padx=5, pady=5)
        CreateToolTip(self.entryLibleTlHost, text="Host address of Libletranslate server. Default: localhost\n\nYou can find full lists of other dedicated server on Libretranslate github repository.")

        self.labelKey = Label(self.content_Tl_3, text="Port :")
        self.labelKey.pack(side=tk.LEFT, padx=5, pady=5)
        CreateToolTip(self.labelKey, text="Port of Libletranslate server. Default: 5000\n\nSet it to empty if you are not using local server.")

        self.libreTlPort = StringVar(self.root)
        self.libreTlPort.set("5000")
        self.entryLibreTlPort = ttk.Entry(self.content_Tl_3, textvariable=self.libreTlPort)
        self.entryLibreTlPort.pack(side=tk.LEFT, padx=5, pady=5)
        CreateToolTip(self.entryLibreTlPort, text="Port of Libletranslate server. Default: 5000\n\nSet it to empty if you are not using local server.")

        self.libreHttpsVar = BooleanVar(self.root, value=False)
        self.checkLibreHttps = ttk.Checkbutton(self.content_Tl_3, variable=self.libreHttpsVar, text="Use HTTPS")
        self.checkLibreHttps.pack(side=tk.LEFT, padx=5, pady=5)
        CreateToolTip(self.checkLibreHttps, text="HTTPS or HTTP. Default: HTTP\n\nSet it to https if you are not using local server.")

        # ----------------------------------------------------------------------
        # Hotkey
        self.frameHotkey = tk.Frame(self.f_m_top)
        self.frameHotkey.pack(side=tk.LEFT, fill=tk.BOTH, padx=5, pady=5)

        self.fLabelHKCapTl = LabelFrame(self.frameHotkey, text="• Capture Hotkey Settings", width=900, height=75)
        self.fLabelHKCapTl.pack(side=tk.TOP, fill=tk.X, expand=False, padx=5, pady=(0, 5))
        self.fLabelHKCapTl.pack_propagate(0)
        self.content_HKCapTl = tk.Frame(self.fLabelHKCapTl)
        self.content_HKCapTl.pack(side=tk.TOP, fill=tk.X, expand=False)

        self.spinValHKCapTl = IntVar(self.root)

        self.labelHkCapTl = Label(self.content_HKCapTl, text="Time delay (ms) : ")
        self.labelHkCapTl.pack(side=tk.LEFT, padx=5, pady=5)
        CreateToolTip(self.labelHkCapTl, text="The time delay to capture when the hotkey is pressed")

        self.spinnerHKCapTlDelay = ttk.Spinbox(self.content_HKCapTl, from_=0, to=100000, width=20, textvariable=self.spinValHKCapTl)
        self.validateDigits_Delay = (self.root.register(lambda event: self.validateSpinbox(event, self.spinnerHKCapTlDelay)), "%P")
        self.spinnerHKCapTlDelay.configure(validate="key", validatecommand=self.validateDigits_Delay)
        self.spinnerHKCapTlDelay.pack(side=tk.LEFT, padx=5, pady=5)

        self.buttonSetHKCapTl = Button(self.content_HKCapTl, text="Click to set the hotkey", command=self.setHKCapTl)
        self.buttonSetHKCapTl.pack(side=tk.LEFT, padx=5, pady=5)

        self.buttonClearHKCapTl = ttk.Button(self.content_HKCapTl, text="✕ Clear", command=self.clearHKCapTl)
        self.buttonClearHKCapTl.pack(side=tk.LEFT, padx=5, pady=5)

        self.labelHKCapTl = Label(self.content_HKCapTl, text="Current hotkey : ")
        self.labelHKCapTl.pack(side=tk.LEFT, padx=5, pady=5)
        CreateToolTip(self.labelHKCapTl, text="Currently set hotkey for capturing")

        self.labelCurrentHKCapTl = Label(self.content_HKCapTl, text="")
        self.labelCurrentHKCapTl.pack(side=tk.LEFT, padx=5, pady=5)

        # Snip and cap
        self.fLabelHKSnipCapTl = LabelFrame(self.frameHotkey, text="• Snip & Capture Hotkey Settings", width=900, height=75)
        self.fLabelHKSnipCapTl.pack(side=tk.TOP, fill=tk.X, expand=False, padx=5, pady=(0, 5))
        self.fLabelHKSnipCapTl.pack_propagate(0)
        self.content_HKSnipCapTl = tk.Frame(self.fLabelHKSnipCapTl)
        self.content_HKSnipCapTl.pack(side=tk.TOP, fill=tk.X, expand=False)

        self.spinValHKSnipCapTl = IntVar(self.root)

        self.labelHkSnipCapTl = Label(self.content_HKSnipCapTl, text="Time delay (ms) : ")
        self.labelHkSnipCapTl.pack(side=tk.LEFT, padx=5, pady=5)
        CreateToolTip(self.labelHkCapTl, text="The time delay to activate snipping mode when the hotkey is pressed")

        self.spinnerHKSnipCapTlDelay = ttk.Spinbox(self.content_HKSnipCapTl, from_=0, to=100000, width=20, textvariable=self.spinValHKSnipCapTl)
        self.validateDigits_DelaySnip = (self.root.register(lambda event: self.validateSpinbox(event, self.spinnerHKSnipCapTlDelay)), "%P")
        self.spinnerHKSnipCapTlDelay.configure(validate="key", validatecommand=self.validateDigits_DelaySnip)
        self.spinnerHKSnipCapTlDelay.pack(side=tk.LEFT, padx=5, pady=5)

        self.buttonHKSnipCapTl = Button(self.content_HKSnipCapTl, text="Click to set the hotkey", command=self.setHKSnipCapTl)
        self.buttonHKSnipCapTl.pack(side=tk.LEFT, padx=5, pady=5)

        self.buttonClearHKSnipCapTl = ttk.Button(self.content_HKSnipCapTl, text="✕ Clear", command=self.clearHKSnipCapTl)
        self.buttonClearHKSnipCapTl.pack(side=tk.LEFT, padx=5, pady=5)

        self.labelHKSnipCapTl = Label(self.content_HKSnipCapTl, text="Current hotkey : ")
        self.labelHKSnipCapTl.pack(side=tk.LEFT, padx=5, pady=5)
        CreateToolTip(self.labelHKSnipCapTl, text="Currently set hotkey for snip & capture")

        self.labelCurrentHKSnipCapTl = Label(self.content_HKSnipCapTl, text="")
        self.labelCurrentHKSnipCapTl.pack(side=tk.LEFT, padx=5, pady=5)

        # ----------------------------------------------------------------------
        # Query/Result box
        self.frameQueryResult = tk.Frame(self.f_m_top)
        self.frameQueryResult.pack(side=tk.LEFT, fill=tk.BOTH, padx=5, pady=5)

        self.fLabelQuery = LabelFrame(self.frameQueryResult, text="• Query Box", width=900, height=140)
        self.fLabelQuery.pack(side=tk.TOP, fill=tk.X, expand=False, padx=5, pady=(0, 5))
        self.fLabelQuery.pack_propagate(0)

        self.fQueryContent_1 = tk.Frame(self.fLabelQuery)
        self.fQueryContent_1.pack(side=tk.TOP, fill=tk.X, expand=False)

        self.fQueryContent_2 = tk.Frame(self.fLabelQuery)
        self.fQueryContent_2.pack(side=tk.TOP, fill=tk.X, expand=False)

        self.fQueryContent_3 = tk.Frame(self.fLabelQuery)
        self.fQueryContent_3.pack(side=tk.TOP, fill=tk.X, expand=False)

        self.queryBgVar = _StoredGlobal.queryBg
        self.queryBg = Label(self.fQueryContent_1, text="Textbox Bg Color : ")
        self.queryBg.pack(side=tk.LEFT, padx=5, pady=5)
        self.queryBg.bind("<Button-1>", lambda event: self.colorChoosing(label=self.queryBg, theVar=self.queryBgVar, theText="Textbox BG color: ", destination=_StoredGlobal.main.query_Detached_Window_UI))
        CreateToolTip(self.queryBg, "Click to choose query textbox background color")

        self.hintLabelQuery = Label(self.fQueryContent_1, text="❓")
        self.hintLabelQuery.pack(padx=5, pady=5, side=tk.RIGHT)
        CreateToolTip(self.hintLabelQuery, "Click on the label to change the value of the settings")

        self.queryFgVar = _StoredGlobal.queryFg
        self.queryFg = Label(self.fQueryContent_2, text="Textbox Fg Color : ")
        self.queryFg.pack(side=tk.LEFT, padx=5, pady=5)
        self.queryFg.bind("<Button-1>", lambda event: self.colorChoosing(label=self.queryFg, theVar=self.queryFgVar, theText="Textbox FG color: ", destination=_StoredGlobal.main.query_Detached_Window_UI))
        CreateToolTip(self.queryFg, "Click to choose query textbox foreground color")

        self.queryFontVar = _StoredGlobal.queryFont
        self.queryFontDict = json.loads(self.queryFontVar.get().replace("'", '"'))
        self.queryFont = Label(self.fQueryContent_3, text="Textbox Font : ")
        self.queryFont.pack(side=tk.LEFT, padx=5, pady=5)
        self.queryFont.bind("<Button-1>", lambda event: self.fontChooser(label=self.queryFont, theVar=self.queryFontVar, theDict=self.queryFontDict, destination=_StoredGlobal.main.query_Detached_Window_UI))
        CreateToolTip(self.queryFont, "Click to choose query textbox font")

        self.fLabelResult = LabelFrame(self.frameQueryResult, text="• Result Box", width=900, height=140)
        self.fLabelResult.pack(side=tk.TOP, fill=tk.X, expand=False, padx=5, pady=5)
        self.fLabelResult.pack_propagate(0)

        self.fResultContent_1 = tk.Frame(self.fLabelResult)
        self.fResultContent_1.pack(side=tk.TOP, fill=tk.X, expand=False)

        self.fResultContent_2 = tk.Frame(self.fLabelResult)
        self.fResultContent_2.pack(side=tk.TOP, fill=tk.X, expand=False)

        self.fResultContent_3 = tk.Frame(self.fLabelResult)
        self.fResultContent_3.pack(side=tk.TOP, fill=tk.X, expand=False)

        self.resultBgVar = _StoredGlobal.resultBg
        self.resultBg = Label(self.fResultContent_1, text="Textbox Bg Color : ")
        self.resultBg.pack(side=tk.LEFT, padx=5, pady=5)
        self.resultBg.bind("<Button-1>", lambda event: self.colorChoosing(label=self.resultBg, theVar=self.resultBgVar, theText="Textbox BG color: ", destination=_StoredGlobal.main.result_Detached_Window_UI))
        CreateToolTip(self.resultBg, "Click to choose result textbox background color")

        self.hintLabelResult = Label(self.fResultContent_1, text="❓")
        self.hintLabelResult.pack(padx=5, pady=5, side=tk.RIGHT)
        CreateToolTip(self.hintLabelResult, "Click on the label to change the value of the settings")

        self.resultFgVar = _StoredGlobal.resultFg
        self.resultFg = Label(self.fResultContent_2, text="Textbox Fg Color : ")
        self.resultFg.pack(side=tk.LEFT, padx=5, pady=5)
        self.resultFg.bind("<Button-1>", lambda event: self.colorChoosing(label=self.resultFg, theVar=self.resultFgVar, theText="Textbox FG color: ", destination=_StoredGlobal.main.result_Detached_Window_UI))
        CreateToolTip(self.resultFg, "Click to choose result textbox foreground color")

        self.resultFontVar = _StoredGlobal.resultFont
        self.resultFontDict = json.loads(self.resultFontVar.get().replace("'", '"'))
        self.resultFont = Label(self.fResultContent_3, text="Textbox Font : ")
        self.resultFont.pack(side=tk.LEFT, padx=5, pady=5)
        self.resultFont.bind("<Button-1>", lambda event: self.fontChooser(label=self.resultFont, theVar=self.resultFontVar, theDict=self.resultFontDict, destination=_StoredGlobal.main.result_Detached_Window_UI))
        CreateToolTip(self.resultFont, "Click to choose result textbox font")

        # ----------------------------------------------------------------------
        # Mask window
        self.frameMask = tk.Frame(self.f_m_top)
        self.frameMask.pack(side=tk.TOP, fill=tk.X, expand=False, padx=5, pady=5)

        self.fLabelMask = LabelFrame(self.frameMask, text="• Mask Window", width=900, height=110)
        self.fLabelMask.pack(side=tk.TOP, fill=tk.X, expand=False, padx=5, pady=5)
        self.fLabelMask.pack_propagate(0)

        self.fMaskContent_1 = tk.Frame(self.fLabelMask)
        self.fMaskContent_1.pack(side=tk.TOP, fill=tk.X, expand=False)

        self.fMaskContent_2 = tk.Frame(self.fLabelMask)
        self.fMaskContent_2.pack(side=tk.TOP, fill=tk.X, expand=False)

        self.maskColorVar = StringVar()
        self.maskColorLabel = Label(self.fMaskContent_1, text="Color     :     ")
        self.maskColorLabel.pack(side=tk.LEFT, padx=5, pady=5)
        self.maskColorLabel.bind("<Button-1>", lambda event: self.colorChoosing(label=self.maskColorLabel, theVar=self.maskColorVar, theText="Color     :     "))
        CreateToolTip(self.maskColorLabel, "Click to choose mask window color on startup")

        self.maskOpacityVar = DoubleVar()
        self.maskOpacityLabel = Label(self.fMaskContent_2, text="Opacity : ")
        self.maskOpacityLabel.pack(side=tk.LEFT, padx=5, pady=5)
        CreateToolTip(self.maskOpacityLabel, "Mask window opacity on startup")

        self.maskOpacityLabel2 = Label(self.fMaskContent_2, text="0.5")

        self.maskOpacitySlider = ttk.Scale(self.fMaskContent_2, from_=0.0, to=1.0, length=150, orient=HORIZONTAL, variable=self.maskOpacityVar, command=self.maskOpacitySlider_Callback)
        self.maskOpacitySlider.pack(side=tk.LEFT, padx=5, pady=5)
        self.maskOpacityLabel2.pack(side=tk.LEFT, padx=5, pady=5)
        CreateToolTip(self.maskOpacityLabel2, "Mask window opacity on startup")

        self.maskWindowHint = Label(self.fMaskContent_1, text="❓")
        self.maskWindowHint.pack(padx=5, pady=5, side=tk.RIGHT)
        CreateToolTip(self.maskWindowHint, "Settings for default startup value")

        # ----------------------------------------------------------------------
        # Other
        self.frameOther = tk.Frame(self.f_m_top)
        self.frameOther.pack(side=tk.LEFT, fill=tk.BOTH, padx=5, pady=5)

        self.fLabelOther = LabelFrame(self.frameOther, text="• Other Settings", width=900, height=110)
        self.fLabelOther.pack(side=tk.TOP, fill=tk.X, expand=False, padx=5, pady=(0, 5))
        self.fLabelOther.pack_propagate(0)

        self.fOtherContent_1 = tk.Frame(self.fLabelOther)
        self.fOtherContent_1.pack(side=tk.TOP, fill=tk.X, expand=False)

        self.fOtherContent_2 = tk.Frame(self.fLabelOther)
        self.fOtherContent_2.pack(side=tk.TOP, fill=tk.X, expand=False)

        # Checkbox for check for update
        self.checkUpdateVar = BooleanVar(self.root, value=True)
        self.checkUpdateBox = ttk.Checkbutton(self.fOtherContent_1, text="Check for update on app start", variable=self.checkUpdateVar)
        self.checkUpdateBox.pack(side=tk.LEFT, padx=5, pady=5)
        CreateToolTip(self.checkUpdateBox, "Check for update on app start. You can also check manually by going to help in menubar")

        self.loggingVar = BooleanVar(self.root, value=True)
        self.loggingBox = ttk.Checkbutton(self.fOtherContent_2, text="Logging", variable=self.loggingVar)
        self.loggingBox.pack(side=tk.LEFT, padx=(5, 4), pady=(4, 6))

        self.loggingLineVar = IntVar(self.root, value=10)
        self.loggingLineLabel = Label(self.fOtherContent_2, text="Max line : ")
        self.loggingLineLabel.pack(side=tk.LEFT, padx=0, pady=5)

        self.loggingLineSpinner = ttk.Spinbox(self.fOtherContent_2, from_=1, to=1000, textvariable=self.loggingLineVar, width=7)
        self.validateDigits_Logging = (self.root.register(lambda event: self.validateSpinbox(event, self.loggingLineSpinner)), "%P")
        self.loggingLineSpinner.configure(validate="key", validatecommand=self.validateDigits_Logging)
        self.loggingLineSpinner.pack(side=tk.LEFT, padx=4, pady=(6, 4))
        CreateToolTip(self.loggingLineSpinner, "Max line of logging")

        # ----------------------------------------------------------------
        # Bottom tk.Frame
        # Create a bottom frame to hold the buttons
        self.bottomFrame = tk.Frame(self.f_m_bot)
        self.bottomFrame.pack(side=tk.BOTTOM, fill=tk.X, pady=(1, 0))

        # Create the buttons
        self.btnSave = ttk.Button(self.bottomFrame, text="🖪 Save Settings", command=self.saveSettings)
        self.btnSave.pack(side=tk.RIGHT, padx=4, pady=5)

        self.btnReset = ttk.Button(self.bottomFrame, text="⟳ Reset To Currently Stored Setting", command=self.reset)
        self.btnReset.pack(side=tk.RIGHT, padx=5, pady=5)

        self.btnRestoreDefault = ttk.Button(self.bottomFrame, text="⚠ Restore Default", command=self.restoreDefault)
        self.btnRestoreDefault.pack(side=tk.RIGHT, padx=5, pady=5)

        # ----------------------------------------------------------------
        # On Close
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.hideAllFrame()
        self.lb_cat.select_set(0)
        self.showFrame(self.f_cat_1)

    # ----------------------------------------------------------------
    # Functions
    # ----------------------------------------------------------------
    def show(self):
        fJson.loadSetting()  # read settings every time it is opened
        self.reset()
        self.root.wm_deiconify()

    def on_closing(self):
        self.root.wm_withdraw()

    def stop_scroll_if_disabled(self, event, theSpinner: ttk.Spinbox):
        if str(theSpinner["state"]) == "disabled":
            return "break"

    def onSelect(self, event):
        """On Select for frame changing

        Args:
            event ([type]): Ignored click event
        """
        if self.lb_cat.curselection() != ():
            self.hideAllFrame()

            if self.lb_cat.curselection()[0] == 0:
                self.showFrame(self.f_cat_1)

            elif self.lb_cat.curselection()[0] == 1:
                self.showFrame(self.f_cat_2)

            elif self.lb_cat.curselection()[0] == 2:
                self.showFrame(self.frameTranslate)

            elif self.lb_cat.curselection()[0] == 3:
                self.showFrame(self.frameHotkey)

            elif self.lb_cat.curselection()[0] == 4:
                self.showFrame(self.frameQueryResult)

            elif self.lb_cat.curselection()[0] == 5:
                self.showFrame(self.frameMask)

            elif self.lb_cat.curselection()[0] == 6:
                self.showFrame(self.frameOther)

    def hideAllFrame(self):
        """
        Hide all frames
        """
        self.f_cat_1.pack_forget()
        self.f_cat_2.pack_forget()
        self.frameTranslate.pack_forget()
        self.frameHotkey.pack_forget()
        self.frameQueryResult.pack_forget()
        self.frameMask.pack_forget()
        self.frameOther.pack_forget()

    def showFrame(self, frame):
        """Change frame for each setting

        Args:
            frame ([type]): The frame that will be displayed
        """
        frame.pack(side=tk.LEFT, fill=tk.BOTH, padx=5, pady=5)

    def restoreDefault(self):
        """
        Restore default settings
        """
        x = Mbox("Confirmation", "Are you sure you want to set the settings to default?\n\n**WARNING! CURRENTLY SAVED SETTING WILL BE OVERWRITTEN**", 3, self.root)
        if x == False:
            return

        # Restore Default Settings
        tStatus, settings = fJson.setDefault()
        if tStatus == True:
            # Unbind all hotkeys
            try:
                keyboard.unhook_all_hotkeys()
            except AttributeError:
                # No hotkeys to unbind
                pass
            # Update the settings
            self.reset()

            # Tell success
            print("Restored Default Settings")
            Mbox("Success", "Successfully Restored Value to Default Settings", 0, self.root)

    def reset(self):
        """
        Reset the settings to currently stored settings
        """
        settings = fJson.loadSetting()[1]

        validTesseract = "tesseract" in settings["tesseract_loc"].lower()
        # If tesseract is not found
        if os.path.exists(settings["tesseract_loc"]) == False or validTesseract == False:
            Mbox("Error: Tesseract Not Found!", "Please set tesseract location in Setting.json.\nYou can set this in setting menu or modify it manually in json/Setting.json", 2, self.root)

        # Cache checkbox
        try:
            self.checkVarImgSaved.set(settings["cached"])
        except Exception:
            print("Error: Invalid Image Saving Options")
            Mbox("Error: Invalid Image Saving Options", "Please do not modify the setting manually if you don't know what you are doing", 2, self.root)
            self.checkVarImgSaved.set(True)

        # Autocopy checkbox
        try:
            self.checkVarAutoCopy.set(settings["autoCopy"])
        except Exception:
            print("Error: Invalid Autocopy Options")
            Mbox("Error: Invalid Autocopy Options", "Please do not modify the setting manually if you don't know what you are doing", 2, self.root)
            self.checkVarAutoCopy.set(True)

        # Save to history checkbox
        try:
            self.saveToHistoryVar.set(settings["saveHistory"])
        except Exception:
            print("Error: Invalid History Saving Options")
            Mbox("Error: Invalid History Saving Options", "Please do not modify the setting manually if you don't know what you are doing", 2, self.root)
            self.saveToHistoryVar.set(True)

        # Show no text alert checkbox
        try:
            self.showNoTextAlertVar.set(settings["show_no_text_alert"])
        except Exception:
            print("Error: Invalid Show No Text Alert Options")
            Mbox("Error: Invalid Show No Text Alert Options", "Please do not modify the setting manually if you don't know what you are doing", 2, self.root)
            self.showNoTextAlertVar.set(False)

        # Check for update checkbox
        try:
            self.checkUpdateVar.set(settings["checkUpdateOnStart"])
        except Exception:
            print("Error: Invalid Update Checking Options")
            Mbox("Error: Invalid Update Checking Options", "Please do not modify the setting manually if you don't know what you are doing", 2, self.root)
            self.checkUpdateVar.set(True)

        # Check for cv2 checkbox
        try:
            self.checkVarCV2.set(settings["enhance_Capture"]["cv2_Contour"])
        except Exception:
            print("Error: Invalid OpenCV Options")
            Mbox("Error: Invalid OpenCV Options", "Please do not modify the setting manually if you don't know what you are doing", 2, self.root)
            self.checkVarCv2.set(True)

        # Check for grayscale
        try:
            self.checkVarGrayscale.set(settings["enhance_Capture"]["grayscale"])
        except Exception:
            print("Error: Invalid Grayscale Options")
            Mbox("Error: Invalid Grayscale Options", "Please do not modify the setting manually if you don't know what you are doing", 2, self.root)
            self.checkVarGrayscale.set(True)

        # Check for debug
        try:
            self.checkVarDebugmode.set(settings["enhance_Capture"]["debugmode"])
        except Exception:
            print("Error: Invalid Debug Options")
            Mbox("Error: Invalid Debug Options", "Please do not modify the setting manually if you don't know what you are doing", 2, self.root)
            self.checkVarDebugmode.set(False)

        # Check for delete last char
        try:
            if settings["captureLastValDelete"] > 10 or settings["captureLastValDelete"] < 0:
                raise Exception
            self.valDelLastChar.set(settings["captureLastValDelete"])
        except Exception:
            print("Error: Invalid Delete Last Char Value")
            Mbox("Error: Invalid Delete Last Char Value", "Please do not modify the setting manually if you don't know what you are doing", 2, self.root)
            self.valDelLastChar.set(0)

        try:
            self.replaceNewLineVar.set(settings["replaceNewLine"])
        except Exception:
            print("Error: Invalid Replace New Line Options")
            Mbox("Error: Invalid Replace New Line Options", "Please do not modify the setting manually if you don't know what you are doing", 2, self.root)
            self.replaceNewLineVar.set(True)

        # Check for maskwindow
        try:
            self.maskColorLabel.config(text="Color     :     " + settings["Masking_Window"]["color"])
            self.maskColorVar.set(settings["Masking_Window"]["color"])
            self.maskOpacityLabel2.config(text=str(settings["Masking_Window"]["alpha"]))
            self.maskOpacitySlider.set(settings["Masking_Window"]["alpha"])
        except Exception:
            print("Error: Invalid Mask Window Options")
            Mbox("Error: Invalid Mask Window Options", "Please do not modify the setting manually if you don't know what you are doing", 2, self.root)
            self.maskColorLabel.config(text="Color     :     #555555")
            self.maskColorVar.set("#555555")
            self.maskOpacityLabel2.config(text="0.5")
            self.maskOpacitySlider.set(0.5)

        # Check for snip offset
        try:
            if settings["snippingWindowGeometry"] == "auto":
                self.checkAutoSnippetVar.set(True)
                geometryStr = _StoredGlobal.main.snipper_UI.getScreenTotalGeometry()
            else:
                self.checkAutoSnippetVar.set(False)
                geometryStr = settings["snippingWindowGeometry"]
            newStr = "".join((ch if ch in "0123456789.-e" else " ") for ch in geometryStr)
            geometryNum = [int(i) for i in newStr.split()]
            self.sb_snippet_total_w.set(geometryNum[0])
            self.sb_snippet_total_h.set(geometryNum[1])
            self.sb_snippet_offset_x.set(geometryNum[2])
            self.sb_snippet_offset_y.set(geometryNum[3])
        except Exception:
            print("Error: Invalid Snip Offset Options")
            Mbox("Error: Invalid Snip Offset Options", "Please do not modify the setting manually if you don't know what you are doing", 2, self.root)
            self.checkAutoSnippetVar.set(True)

        # Update the spinner offset
        self.disableEnableSnipSpin()

        # check for libretl
        try:
            self.libreTlKey.set(settings["libreTl"]["api_key"])
            self.libreTlHost.set(settings["libreTl"]["host"])
            self.libreTlPort.set(settings["libreTl"]["port"])
            self.libreHttpsVar.set(settings["libreTl"]["https"])
        except Exception:
            self.libreTlKey.set("")
            self.libreTlHost.set("localhost")
            self.libreTlPort.set("5000")
            self.libreHttpsVar.set(False)
            print("Error: Invalid LibreTranslate Options")
            Mbox("Error: Invalid LibreTranslate Options", "Please do not modify the setting manually if you don't know what you are doing", 2, self.root)

        # Logging
        try:
            self.loggingVar.set(settings["logging"]["enabled"])
            self.loggingLineVar.set(settings["logging"]["max_line"])
        except Exception:
            print("Error: Invalid Logging Options")
            Mbox("Error: Invalid Logging Options", "Please do not modify the setting manually if you don't know what you are doing", 2, self.root)
            self.loggingVar.set(False)
            self.loggingLineVar.set(10)

        # Check for cb background
        try:
            self.CBBackgroundType.current(searchList(settings["enhance_Capture"]["background"], ["Auto-Detect", "Light", "Dark"]))
        except Exception:
            print("Error: Invalid Background Options")
            Mbox("Error: Invalid Background Options", "Please do not modify the setting manually if you don't know what you are doing", 2, self.root)
            self.CBBackgroundType.current(0)

        # Set label value for query and result box
        # Query
        try:
            self.queryFontVar.set(settings["Query_Box"]["font"])
            self.queryFontDict = json.loads(self.queryFontVar.get().replace("'", '"'))
            self.queryBgVar.set(settings["Query_Box"]["bg"])
            self.queryFgVar.set(settings["Query_Box"]["fg"])
            query_font_str = "%(family)s %(size)i %(weight)s %(slant)s" % self.queryFontDict
            self.queryBg.config(text="Textbox Bg Color : " + self.queryBgVar.get())
            self.queryFg.config(text="Textbox Fg Color : " + self.queryFgVar.get())
            self.queryFont.config(text="Textbox Font : " + query_font_str)

            # Result
            self.resultFontVar.set(settings["Result_Box"]["font"])
            self.resultFontDict = json.loads(self.resultFontVar.get().replace("'", '"'))
            self.resultBgVar.set(settings["Result_Box"]["bg"])
            self.resultFgVar.set(settings["Result_Box"]["fg"])
            result_font_str = "%(family)s %(size)i %(weight)s %(slant)s" % self.resultFontDict
            self.resultBg.config(text="Textbox Bg Color : " + self.resultBgVar.get())
            self.resultFg.config(text="Textbox Fg Color : " + self.resultFgVar.get())
            self.resultFont.config(text="Textbox Font : " + result_font_str)
        except Exception:
            print("Error: Invalid Font Options")
            Mbox("Error: Invalid Font Options", "Please do not modify the setting manually if you don't know what you are doing", 2, self.root)
            self.queryFontVar.set("{'family': 'Segoe UI', 'size': 10, 'weight': 'normal', 'slant': 'roman'}")
            self.queryFontDict = json.loads(self.queryFontVar.get().replace("'", '"'))
            self.queryBgVar.set("#ffffff")
            self.queryFgVar.set("#000000")
            self.queryBg.config(text="Textbox Bg Color : " + self.queryBgVar.get())
            self.queryFg.config(text="Textbox Fg Color : " + self.queryFgVar.get())
            self.queryFont.config(text="Textbox Font : " + "%(family)s %(size)i %(weight)s %(slant)s" % self.queryFontDict)

            # Result
            self.resultFontVar.set("{'family': 'Segoe UI', 'size': 10, 'weight': 'normal', 'slant': 'roman'}")
            self.resultFontDict = json.loads(self.resultFontVar.get().replace("'", '"'))
            self.resultBgVar.set("#ffffff")
            self.resultFgVar.set("#000000")
            self.resultBg.config(text="Textbox Bg Color : " + self.resultBgVar.get())
            self.resultFg.config(text="Textbox Fg Color : " + self.resultFgVar.get())

        # Show current hotkey
        try:
            self.labelCurrentHKCapTl.config(text=settings["hotkey"]["captureAndTl"]["hk"])
            self.spinValHKCapTl.set(settings["hotkey"]["captureAndTl"]["delay"])

            self.labelCurrentHKSnipCapTl.config(text=settings["hotkey"]["snipAndCapTl"]["hk"])
            self.spinValHKSnipCapTl.set(settings["hotkey"]["snipAndCapTl"]["delay"])
        except KeyError:
            print("Error: Invalid Hotkey Options")

        # Store setting to localvar
        try:
            offSetXY = settings["offSetXY"]
            xyOffSetType = settings["offSetXYType"]
        except Exception:
            print("Error: Invalid Offset Options")
            Mbox("Error: Invalid Offset Options", "Please do not modify the setting manually if you don't know what you are doing", 2, self.root)
            offSetXY = [0, 0]
            xyOffSetType = "No Offset"

        # Get offset
        x, y, w, h = getTheOffset()
        # If cb no offset
        if xyOffSetType == "No Offset":
            self.cb_cw_offset.current(0)
            self.cbtn_cw_auto_offset_x.config(state=tk.DISABLED)
            self.cbtn_cw_auto_offset_y.config(state=tk.DISABLED)
            self.sb_cw_offset_x.config(state=tk.DISABLED)
            self.sb_cw_offset_y.config(state=tk.DISABLED)
            self.spinValOffSetX.set(0)
            self.spinValOffSetY.set(0)

            self.checkVarOffSetX.set(False)
            self.checkVarOffSetY.set(False)

        # If cb custom offset
        elif xyOffSetType == "Custom Offset":
            self.cb_cw_offset.current(1)
            self.spinValOffSetX.set(x)
            self.spinValOffSetY.set(y)
            self.cbtn_cw_auto_offset_x.config(state=tk.NORMAL)
            self.cbtn_cw_auto_offset_y.config(state=tk.NORMAL)

            if offSetXY[0] == "auto":
                self.checkVarOffSetX.set(True)
                self.sb_cw_offset_x.config(state=tk.DISABLED)
            else:
                self.checkVarOffSetX.set(False)
                self.sb_cw_offset_x.config(state=tk.NORMAL)

            if offSetXY[1] == "auto":
                self.checkVarOffSetY.set(True)
                self.sb_cw_offset_y.config(state=tk.DISABLED)
            else:
                self.checkVarOffSetY.set(False)
                self.sb_cw_offset_y.config(state=tk.NORMAL)
        else:
            self.cb_cw_offset.current(0)
            print("Error: Invalid Offset Type")
            Mbox("Error: Invalid Offset Type", "Please do not modify the setting manually if you don't know what you are doing", 2, self.root)

        # W H
        self.spinValOffSetW.set(w)
        self.spinValOffSetH.set(h)

        try:
            if settings["offSetWH"][0] == "auto":
                self.checkVarOffSetW.set(True)
                self.sb_cw_offset_w.config(state=tk.DISABLED)
            else:
                self.checkVarOffSetW.set(False)
                self.sb_cw_offset_w.config(state=tk.NORMAL)

            if settings["offSetWH"][1] == "auto":
                self.checkVarOffSetH.set(True)
                self.sb_cw_offset_h.config(state=tk.DISABLED)
            else:
                self.checkVarOffSetH.set(False)
                self.sb_cw_offset_h.config(state=tk.NORMAL)
        except Exception:
            print("Error: Invalid Offset Options")
            Mbox("Error: Invalid Offset Options", "Please do not modify the setting manually if you don't know what you are doing", 2, self.root)
            self.checkVarOffSetW.set(False)
            self.checkVarOffSetH.set(False)

        self.CBTLChange_setting()
        try:
            self.CBDefaultEngine.current(searchList(settings["default_Engine"], engines))
            self.CBDefaultFrom.current(searchList(settings["default_FromOnOpen"], self.langOpt))
            self.CBDefaultTo.current(searchList(settings["default_ToOnOpen"], self.langOpt))
            self.textBoxTesseractPath.delete(0, END)
            self.textBoxTesseractPath.insert(0, settings["tesseract_loc"])
        except Exception:
            print("Error: Invalid Engine Options")
            Mbox("Error: Invalid Engine Options", "Please do not modify the setting manually if you don't know what you are doing", 2, self.root)
            self.CBDefaultEngine.current(0)
            self.CBDefaultFrom.current(0)
            self.CBDefaultTo.current(0)
            self.textBoxTesseractPath.delete(0, END)
            self.textBoxTesseractPath.insert(0, "C:/Program Files/Tesseract-OCR/tesseract.exe")

        _StoredGlobal.main.query_Detached_Window_UI.updateStuff()
        _StoredGlobal.main.result_Detached_Window_UI.updateStuff()
        print("Setting Loaded")
        # No need for mbox

    # Save settings
    def saveSettings(self):
        """
        Save settings to file
        """
        # Check path tesseract
        tesseractPathInput = self.textBoxTesseractPath.get().strip().lower()
        # Get the exe name or the last / in tesseract path
        tesseractPath = tesseractPathInput.split("/")[-1]
        validTesseract = "tesseract" in tesseractPath.lower()
        # # If tesseract is not found
        if os.path.exists(tesseractPathInput) == False or validTesseract == False:
            print("Tesseract Not Found Error")
            Mbox("Error: Tesseract not found", "Invalid Path Provided For Tesseract.exe!", 2, self.root)
            return

        # Checking each checkbox for the offset of x,y,w,h
        # x
        x = int(self.sb_cw_offset_x.get()) if self.checkVarOffSetX.get() == False else "auto"
        y = int(self.sb_cw_offset_y.get()) if self.checkVarOffSetY.get() == False else "auto"
        w = int(self.sb_cw_offset_w.get()) if self.checkVarOffSetW.get() == False else "auto"
        h = int(self.sb_cw_offset_h.get()) if self.checkVarOffSetH.get() == False else "auto"

        self.queryFontDict = json.loads(self.queryFontVar.get().replace("'", '"'))
        self.resultFontDict = json.loads(self.resultFontVar.get().replace("'", '"'))

        if self.checkAutoSnippetVar.get():
            snippingWindowGeometry = "auto"
        else:
            snippingWindowGeometry = f"{self.sb_snippet_total_w.get()}x{self.sb_snippet_total_h.get()}+{self.sb_snippet_offset_x.get()}+{self.sb_snippet_offset_y.get()}"

        settingToSave = {
            "cached": self.checkVarImgSaved.get(),
            "autoCopy": self.checkVarAutoCopy.get(),
            "offSetXYType": self.cb_cw_offset.get(),
            "offSetXY": [x, y],
            "offSetWH": [w, h],
            "snippingWindowGeometry": snippingWindowGeometry,
            "tesseract_loc": self.textBoxTesseractPath.get().strip(),
            "default_Engine": self.CBDefaultEngine.get(),
            "default_FromOnOpen": self.CBDefaultFrom.get(),
            "default_ToOnOpen": self.CBDefaultTo.get(),
            "captureLastValDelete": self.valDelLastChar.get(),
            "replaceNewLine": self.replaceNewLineVar.get(),
            "libreTl": {"api_key": self.libreTlKey.get(), "https": self.libreHttpsVar.get(), "host": self.libreTlHost.get(), "port": self.libreTlPort.get()},
            "hotkey": {
                "captureAndTl": {"hk": self.labelCurrentHKCapTl["text"], "delay": self.spinValHKCapTl.get()},
                "snipAndCapTl": {"hk": self.labelCurrentHKSnipCapTl["text"], "delay": self.spinValHKSnipCapTl.get()},
            },
            "Query_Box": {
                "font": {
                    "family": self.queryFontDict["family"],
                    "size": self.queryFontDict["size"],
                    "weight": self.queryFontDict["weight"],
                    "slant": self.queryFontDict["slant"],
                    "underline": self.queryFontDict["underline"],
                    "overstrike": self.queryFontDict["overstrike"],
                },
                "bg": self.queryBgVar.get(),
                "fg": self.queryFgVar.get(),
            },
            "Result_Box": {
                "font": {
                    "family": self.resultFontDict["family"],
                    "size": self.resultFontDict["size"],
                    "weight": self.resultFontDict["weight"],
                    "slant": self.resultFontDict["slant"],
                    "underline": self.resultFontDict["underline"],
                    "overstrike": self.resultFontDict["overstrike"],
                },
                "bg": self.resultBgVar.get(),
                "fg": self.resultFgVar.get(),
            },
            "Masking_Window": {"color": self.maskColorVar.get(), "alpha": self.maskOpacityVar.get()},
            "logging": {"enabled": self.loggingVar.get(), "max_line": self.loggingLineVar.get()},
            "saveHistory": self.saveToHistoryVar.get(),
            "checkUpdateOnStart": self.checkUpdateVar.get(),
            "enhance_Capture": {"cv2_Contour": self.checkVarCV2.get(), "grayscale": self.checkVarGrayscale.get(), "background": self.CBBackgroundType.get(), "debugmode": self.checkVarDebugmode.get()},
            "show_no_text_alert": self.showNoTextAlertVar.get(),
        }

        # Unbind all hotkey
        try:
            keyboard.unhook_all_hotkeys()
        except AttributeError:
            # No hotkeys to unbind
            pass
        # Bind hotkey
        if self.labelCurrentHKCapTl["text"] != "":
            keyboard.add_hotkey(self.labelCurrentHKCapTl["text"], _StoredGlobal.hotkeyCapTLCallback)

        if self.labelCurrentHKSnipCapTl["text"] != "":
            keyboard.add_hotkey(self.labelCurrentHKSnipCapTl["text"], _StoredGlobal.hotkeySnipCapTLCallback)

        print("-" * 50)
        print("Setting saved!")
        print(settingToSave)

        status, dataStatus = fJson.writeSetting(settingToSave)
        if status:
            print("-" * 50)
            print(dataStatus)
            Mbox("Success", dataStatus, 0, self.root)
        else:
            print("-" * 50)
            print(dataStatus)
            Mbox("Error", dataStatus, 2, self.root)

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
            spinners[offSetType].config(state=tk.tk.DISABLED)
            spinners[offSetType].set(offsets)
        else:
            spinners[offSetType].config(state=tk.tk.NORMAL)
            spinners[offSetType].set(settingVal[offSetType])

    # ----------------------------------------------------------------
    # Engine
    # Search for tesseract
    def searchTesseract(self):
        """
        Search for tesseract by opening a file dialog
        """
        self.tesseract_path = filedialog.askopenfilename(initialdir="/", title="Select file", filetypes=(("tesseract.exe", "*.exe"),))
        if self.tesseract_path != "":
            self.textBoxTesseractPath.delete(0, END)
            self.textBoxTesseractPath.insert(0, self.tesseract_path)

    # ----------------------------------------------------------------
    # Hotkey
    def setHKCapTl(self):
        """
        Set the hotkey for capturing and translating
        """
        hotkey = keyboard.read_hotkey(suppress=False)
        self.labelCurrentHKCapTl.config(text=str(hotkey))

    def clearHKCapTl(self):
        """
        Clear the hotkey for capturing and translating
        """
        self.labelCurrentHKCapTl.config(text="")

    def setHKSnipCapTl(self):
        """
        Set the hotkey for snipping and translate
        """
        hotkey = keyboard.read_hotkey(suppress=False)
        self.labelCurrentHKSnipCapTl.config(text=str(hotkey))

    def clearHKSnipCapTl(self):
        """
        Clear the hotkey for snipping and translate
        """
        self.labelCurrentHKSnipCapTl.config(text="")

    # ----------------------------------------------------------------
    # Capture
    def screenShotAndOpenLayout(self):
        """
        Fully capture the window and open the image
        """
        seeFullWindow()

    # ----------------------------------------------------------------
    # CB Settings
    def CBTLChange_setting(self, event=None):
        """Change the state of the CB when the default engine is changed

        Args:
            event: Ignored. Defaults to None
        """
        # In settings
        # Get the engine from the combobox
        curr_Engine = self.CBDefaultEngine.get()
        previous_From = self.CBDefaultFrom.get()
        previous_To = self.CBDefaultTo.get()

        # Translate
        if curr_Engine == "Google Translate":
            self.langOpt = optGoogle
            self.CBDefaultFrom["values"] = optGoogle
            self.CBDefaultFrom.current(searchList(previous_From, optGoogle))
            self.CBDefaultTo["values"] = optGoogle
            self.CBDefaultTo.current(searchList(previous_To, optGoogle))
            self.CBDefaultTo.config(state="readonly")
        elif curr_Engine == "Deepl":
            self.langOpt = optDeepl
            self.CBDefaultFrom["values"] = optDeepl
            self.CBDefaultFrom.current(searchList(previous_From, optDeepl))
            self.CBDefaultTo["values"] = optDeepl
            self.CBDefaultTo.current(searchList(previous_To, optDeepl))
            self.CBDefaultTo.config(state="readonly")
        elif curr_Engine == "MyMemoryTranslator":
            self.langOpt = optMyMemory
            self.CBDefaultFrom["values"] = optMyMemory
            self.CBDefaultFrom.current(searchList(previous_From, optMyMemory))
            self.CBDefaultTo["values"] = optMyMemory
            self.CBDefaultTo.current(searchList(previous_To, optMyMemory))
            self.CBDefaultTo.config(state="readonly")
        elif curr_Engine == "PONS":
            self.langOpt = optPons
            self.CBDefaultFrom["values"] = optPons
            self.CBDefaultFrom.current(searchList(previous_From, optPons))
            self.CBDefaultTo["values"] = optPons
            self.CBDefaultTo.current(searchList(previous_To, optPons))
            self.CBDefaultTo.config(state="readonly")
        elif curr_Engine == "LibreTranslate":
            self.langOpt = optLibre
            self.CBDefaultFrom["values"] = optLibre
            self.CBDefaultFrom.current(searchList(previous_From, optLibre))
            self.CBDefaultTo["values"] = optLibre
            self.CBDefaultTo.current(searchList(previous_To, optLibre))
            self.CBDefaultTo.config(state="readonly")
        elif curr_Engine == "None":
            self.langOpt = optNone
            self.CBDefaultFrom["values"] = optNone
            self.CBDefaultFrom.current(searchList(previous_From, optNone))
            self.CBDefaultTo["values"] = optNone
            self.CBDefaultTo.current(searchList(previous_To, optNone))
            self.CBDefaultTo.config(state="disabled")

    def CBOffSetChange(self, event=None):
        """Change the state of the CB when the default engine is changed

        Args:
            event: Ignored. Defaults to None.
        """
        offSets = getTheOffset("Custom")
        xyOffSetType = self.cb_cw_offset.get()

        # Check offset or not
        if xyOffSetType == "No Offset":
            # Select auto
            self.checkVarOffSetX.set(False)
            self.checkVarOffSetY.set(False)
            # Disable spinner and the selector, also set stuff in spinner to 0
            self.cbtn_cw_auto_offset_x.config(state=tk.DISABLED)
            self.cbtn_cw_auto_offset_y.config(state=tk.DISABLED)
            self.sb_cw_offset_x.config(state=tk.DISABLED)
            self.sb_cw_offset_y.config(state=tk.DISABLED)
            self.spinValOffSetX.set(0)
            self.spinValOffSetY.set(0)
        else:
            # Disselect auto
            self.checkVarOffSetX.set(True)
            self.checkVarOffSetY.set(True)
            # Make checbtn clickable, but set auto which means spin is disabled
            self.cbtn_cw_auto_offset_x.config(state=tk.NORMAL)
            self.cbtn_cw_auto_offset_y.config(state=tk.NORMAL)
            self.spinValOffSetX.set(offSets[0])
            self.spinValOffSetY.set(offSets[1])
            self.sb_cw_offset_x.config(state=tk.DISABLED)
            self.sb_cw_offset_y.config(state=tk.DISABLED)

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

    # ----------------------------------------------------------------
    # Slider
    def maskOpacitySlider_Callback(self, event):
        """Callback for the mask opacity slider

        Args:
            event: value of the slider
        """
        self.maskOpacityVar.set(event)
        self.maskOpacityLabel2.config(text=str(round(float(event), 2)))

    # ----------------------------------------------------------------
    # For choosing color
    def colorChoosing(self, event=None, label=None, theVar=None, theText=None, destination=None):
        """
        Color chooser

        Args:
            event: Ignored. Defaults to None
            label: Label to change
            theVar: Variable to change
            theText: Text for the label
            destination: Destination to change
        """
        # Get the color
        color = colorchooser.askcolor(color=theVar.get(), title="Choose a color")[1]
        # If the color is not None
        if color is not None:
            theVar.set(color)
            label.config(text=theText + theVar.get())

            if destination is not None:
                destination.updateStuff()

    # Font Chooser
    def fontChooser(self, event=None, label=None, theVar=None, theDict=None, destination=None):
        """Font chooser

        Args:
            event : Ignored. Defaults to None.
            label : The targeted label object. Defaults to None.
            theVar : The targeted var object. Defaults to None.
            destination : The targeted destination object, destination targeted is a UI window. Defaults to None.
        """
        fontGet = askfont(self.root, title="Choose a font", text="Preview プレビュー معاينة 预览", family=theDict["family"], size=theDict["size"], weight=theDict["weight"], slant=theDict["slant"])
        if fontGet:
            theVar.set(fontGet)
            theDict = json.loads(theVar.get().replace("'", '"'))
            font_str = "%(family)s %(size)i %(weight)s %(slant)s" % theDict
            label.configure(text="Textbox Font : " + font_str)
            destination.updateStuff()

    # Update lbl
    def updateLbl(self):
        """
        Update the UI Font lbl
        """
        self.queryFontDict = json.loads(self.queryFontVar.get().replace("'", '"'))
        query_font_str = "%(family)s %(size)i %(weight)s %(slant)s" % self.queryFontDict
        self.queryBg.config(text="Textbox Bg Color : " + self.queryBgVar.get())
        self.queryFg.config(text="Textbox Fg Color : " + self.queryFgVar.get())
        self.queryFont.config(text="Textbox Font : " + query_font_str)

        # Result
        self.resultFontDict = json.loads(self.resultFontVar.get().replace("'", '"'))
        result_font_str = "%(family)s %(size)i %(weight)s %(slant)s" % self.resultFontDict
        self.resultBg.config(text="Textbox Bg Color : " + self.resultBgVar.get())
        self.resultFg.config(text="Textbox Fg Color : " + self.resultFgVar.get())
        self.resultFont.config(text="Textbox Font : " + result_font_str)

    def disableEnableSnipSpin(self, event=None):
        """Disable/Enable the snip spinbox

        Args:
            event : Ignored. Defaults to None.
        """
        if not self.checkAutoSnippetVar.get():  # IF disabled then enable it
            self.sb_snippet_total_w.config(state=tk.NORMAL)
            self.sb_snippet_total_h.config(state=tk.NORMAL)
            self.sb_snippet_offset_x.config(state=tk.NORMAL)
            self.sb_snippet_offset_y.config(state=tk.NORMAL)
        else:
            self.sb_snippet_total_w.config(state=tk.DISABLED)
            self.sb_snippet_total_h.config(state=tk.DISABLED)
            self.sb_snippet_offset_x.config(state=tk.DISABLED)
            self.sb_snippet_offset_y.config(state=tk.DISABLED)

            res = getScreenTotalGeometry()
            self.sb_snippet_total_w.set(res[1])
            self.sb_snippet_total_h.set(res[2])
            self.sb_snippet_offset_x.set(res[3])
            self.sb_snippet_offset_y.set(res[4])

    def deleteAllCapImg(self, event=None):
        """Delete all the cap images

        Args:
            event : Ignored. Defaults to None.
        """
        # Ask for confirmation first
        if Mbox("Confirmation", "Are you sure you want to delete all captured images?", 3, self.root):
            imgArr = os.listdir(dir_captured)
            # Filter only for .png
            imgArr = [i for i in imgArr if i.endswith(".png")]

            try:
                for img in imgArr:
                    send2trash(".\\img_captured\\" + img)

                    # alt: # os.remove(os.path.join(dir_captured + "/" + img))
                Mbox("Success", "All captured images have been deleted successfully.", 0, self.root)
            except Exception as e:
                print(e)
                Mbox("Error", "Error deleting images", 2, self.root)
