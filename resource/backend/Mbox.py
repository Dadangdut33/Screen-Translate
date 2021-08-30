##  Styles:
##  0 : info
##  1 : warning
##  2 : error
from tkinter import messagebox
def Mbox(title, text, style):
    if style == 0:
        messagebox.showinfo(title, text)
    elif style == 1:
        messagebox.showwarning(title, text)
    elif style == 2:
        messagebox.showerror(title, text)