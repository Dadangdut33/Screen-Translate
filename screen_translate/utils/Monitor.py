from typing import Literal
from screeninfo import get_monitors

from screen_translate.Logging import logger
from screen_translate.Globals import fJson

# Settings to capture all screens
from PIL import ImageGrab
from functools import partial

ImageGrab.grab = partial(ImageGrab.grab, all_screens=True)


class MonitorInfo:
    def __init__(self):
        self.mInfoCache = {"totalX": 0, "totalY": 0, "primaryIn": None, "mData": None, "layoutType": None}

    def getWidthAndHeight(self):
        # Better solution for this case on getting the width and height
        img = ImageGrab.grab()
        totalX = img.size[0]
        totalY = img.size[1]

        return totalX, totalY


mInfo: MonitorInfo = MonitorInfo()


def getScreenInfo(supress_log=True):
    """
    Get the primary screen size.
    """
    mData = []
    index = 0
    primaryIn = 0
    layoutType = None
    for m in get_monitors():
        mData.append(m)
        if m.is_primary:
            primaryIn = index

        index += 1

    if mInfo.mInfoCache["mData"] != mData:
        totalX, totalY = mInfo.getWidthAndHeight()
    else:
        totalX = mInfo.mInfoCache["totalX"]
        totalY = mInfo.mInfoCache["totalY"]

    layoutType = "horizontal" if totalX > totalY else "vertical"

    mInfo.mInfoCache = {"totalX": totalX, "totalY": totalY, "primaryIn": primaryIn, "mData": mData, "layoutType": layoutType}
    if not supress_log:
        logger.info(f"Monitor Info: {mInfo.mInfoCache}")

    return mInfo.mInfoCache


def get_offset(offSetType: Literal["x", "y", "w", "h"]) -> int:
    """
    Calculate and get the offset settings for the capture window.
    """
    if offSetType == "w":
        w = 60 if fJson.settingCache["offSetW"] == "auto" else fJson.settingCache["offSetW"]
        return w
    elif offSetType == "h":
        h = 60 if fJson.settingCache["offSetH"] == "auto" else fJson.settingCache["offSetH"]
        return h
    else:
        if fJson.settingCache["offSetX"] != "auto" and offSetType == "x":  # if x and manual
            return fJson.settingCache["offSetX"]
        elif fJson.settingCache["offSetY"] != "auto" and offSetType == "y":  # if y and manual
            return fJson.settingCache["offSetY"]

        screenData = getScreenInfo()
        primaryIn = screenData["primaryIn"]
        if len(screenData["mData"]) == 1:
            return 0  # no offset if only 1 monitor on both x and y

        if offSetType == "x":
            if screenData["layoutType"] == "horizontal":
                if primaryIn == 0:
                    return 0
                else:
                    counter = 0
                    offset_X = 0
                    for monitor in screenData["mData"]:
                        if counter < primaryIn:
                            offset_X += abs(monitor.x)
                        counter += 1
                    return offset_X
            else:
                return 0

        if offSetType == "y":
            if screenData["layoutType"] == "vertical":
                if primaryIn == 0:
                    return 0
                else:
                    counter = 0
                    offset_Y = 0
                    for monitor in screenData["mData"]:
                        if counter < primaryIn:
                            offset_Y += abs(monitor.y)
                        counter += 1
                    return offset_Y
            else:
                return 0


def getScreenTotalGeometry(supress_log=True):
    snippingType = None
    # Get ScreenData
    screenData = getScreenInfo(supress_log)

    try:  # Try catch to avoid program crash.
        snippingType = fJson.settingCache["snippingWindowGeometry"]
    except KeyError:
        snippingType = "auto"

    if snippingType != "auto":  # IF set manually by user
        geometryStr = str(fJson.settingCache["snippingWindowGeometry"])
        newStr = "".join((ch if ch in "0123456789.-e" else " ") for ch in geometryStr)
        geometryList = [int(i) for i in newStr.split()]

        totalX = geometryList[0]
        totalY = geometryList[1]
        offset_X = geometryList[2]
        offset_Y = geometryList[3]

        return geometryStr, totalX, totalY, offset_X, offset_Y

    # Get offset for snipping
    offset_X, offset_Y = 0, 0
    primaryIn = screenData["primaryIn"]
    # offset would only be needed if the primary monitor is located on either the right or bottom of the other monitor
    # so.. going by this logic, we only needed to sum the x and y of the monitor that is located on the left or top of the primary monitor
    # if the primary monitor is located on the first monitor (meaning should be on the most left or most top), then we don't need to add any offset
    if screenData["layoutType"] == "horizontal":
        if primaryIn == 0:
            offset_X = 0
        else:  # Make sure its not the first monitor
            counter = 0
            for monitor in screenData["mData"]:
                if counter < primaryIn:  # the module can detect the - + of the monitor so we just need to add it
                    offset_X += monitor.x
                counter += 1
    else:
        if primaryIn == 0:
            offset_Y = 0
        else:  # Make sure its not the first monitor
            counter = 0
            for monitor in screenData["mData"]:
                if counter < primaryIn:  # the module can detect the - + of the monitor so we just need to add it
                    offset_Y += monitor.y
                counter += 1

    # ------------------
    # Result
    totalX: int = screenData["totalX"]
    totalY: int = screenData["totalY"]

    # Get the full screen size
    screenTotalGeometry = f"{totalX}x{totalY}+{str(offset_X)}+{str(offset_Y)}"

    return screenTotalGeometry, totalX, totalY, int(offset_X), int(offset_Y)
