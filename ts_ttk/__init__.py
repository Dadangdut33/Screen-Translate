import os
from pathlib import Path
from typing import List

inited = False
root = None
theme_list = ["sv-light", "sv-dark"]


def init_theme(func):
    def wrapper(*args, **kwargs):
        global inited
        global root

        if not inited:
            from tkinter import _default_root  # type: ignore

            dir_theme = os.path.abspath(Path(__file__).parent / ".." / "theme")

            # only if a dir
            dir_theme_list = [name for name in os.listdir(dir_theme) if os.path.isdir(os.path.join(dir_theme, name))]

            # filter path list by making sure that the dir name contains .tcl with the same name as the dir
            dir_theme_list = [dir for dir in dir_theme_list if dir + ".tcl" in os.listdir(os.path.join(dir_theme, dir))]

            for dir in dir_theme_list:
                path = os.path.abspath(os.path.join(dir_theme, dir, (dir + ".tcl")))
                theme_list.append(dir)

                try:
                    _default_root.tk.call("source", str(path))
                except AttributeError:
                    raise RuntimeError("can't set theme, because tkinter is not initialized. " + "Please create a tkinter.Tk instance first and then set the theme.") from None
                else:
                    inited = True
                    root = _default_root

        return func(*args, **kwargs)

    return wrapper


@init_theme
def get_theme_list() -> List[str]:
    return theme_list


@init_theme
def set_theme(theme: str):
    real_theme_list = list(root.tk.call("ttk::style", "theme", "names"))  # type: ignore
    real_theme_list.extend(theme_list)
    if theme not in real_theme_list:
        raise RuntimeError("not a valid theme name: {}".format(theme))

    root.tk.call("set_theme", theme)  # type: ignore


@init_theme
def get_current_theme() -> str:
    theme = root.tk.call("ttk::style", "theme", "use")  # type: ignore

    return theme
