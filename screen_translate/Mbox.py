##  Styles:
##  0 : info
##  1 : warning
##  2 : error
##  3 : Yes No
from tkinter import messagebox
def Mbox(title, text, style, parent):
    """Message Box, made simpler
    ##  Styles:
    ##  0 : info
    ##  1 : warning
    ##  2 : error
    ##  3 : Yes No
    """
    if style == 0:
        return messagebox.showinfo(title, text, parent=parent) # Return ok x same as ok
    elif style == 1:
        return messagebox.showwarning(title, text, parent=parent) # Return ok x same as ok
    elif style == 2:
        return messagebox.showerror(title, text, parent=parent) # Return ok x same as ok
    elif style == 3:
        return messagebox.askyesno(title, text, parent=parent) # Return True False, x can't be clicked