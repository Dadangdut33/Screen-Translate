import platform
import winreg

"""
https://stackoverflow.com/a/69643005/13997872
Create autostart:

set_autostart_registry('App name', r'C:\test\tes.exe')

Update autostart:

set_autostart_registry('App name', r'C:\test\tus.exe')

Delete autostart:

set_autostart_registry('App name', autostart=False)

Check autostart:

if check_autostart_registry('App name'):
"""

def set_autostart_registry(app_name, key_data=None, autostart: bool = True) -> bool:
    """
    Create/update/delete Windows autostart registry key

    ! Windows ONLY
    ! If the function fails, OSError is raised.

    :param app_name:    A string containing the name of the application name
    :param key_data:    A string that specifies the application path.
    :param autostart:   True - create/update autostart key / False - delete autostart key
    :return:            True - Success / False - Error, app name dont exist
    """

    if platform.system() != "Windows":
        return False

    with winreg.OpenKey(
        key=winreg.HKEY_CURRENT_USER,
        sub_key=r"Software\Microsoft\Windows\CurrentVersion\Run",
        reserved=0,
        access=winreg.KEY_ALL_ACCESS,
    ) as key:
        try:
            if autostart:
                winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, key_data) # type: ignore
            else:
                winreg.DeleteValue(key, app_name)
        except OSError:
            return False
    return True


def check_autostart_registry(value_name):
    """
    Check Windows autostart registry status

    ! Windows ONLY
    ! If the function fails, OSError is raised.

    :param value_name:  A string containing the name of the application name
    :return: True - Exist / False - Not exist
    """

    if platform.system() != "Windows":
        return False

    with winreg.OpenKey(
        key=winreg.HKEY_CURRENT_USER,
        sub_key=r"Software\Microsoft\Windows\CurrentVersion\Run",
        reserved=0,
        access=winreg.KEY_ALL_ACCESS,
    ) as key:
        idx = 0
        while idx < 1_000:  # Max 1.000 values
            try:
                key_name, _, _ = winreg.EnumValue(key, idx)
                if key_name == value_name:
                    return True
                idx += 1
            except OSError:
                break
    return False
