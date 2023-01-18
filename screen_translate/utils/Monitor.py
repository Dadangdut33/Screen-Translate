from typing import Literal, Optional
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
        # get_monitors() are not accurate sometimes
        img = ImageGrab.grab()
        totalX = img.size[0]
        totalY = img.size[1]

        return totalX, totalY


mInfo: MonitorInfo = MonitorInfo()


def getScreenInfo():
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

        # print(m)
        index += 1

    if mInfo.mInfoCache["mData"] != mData:
        totalX, totalY = mInfo.getWidthAndHeight()
    else:
        totalX = mInfo.mInfoCache["totalX"]
        totalY = mInfo.mInfoCache["totalY"]

    layoutType = "horizontal" if totalX > totalY else "vertical"

    mInfo.mInfoCache = {"totalX": totalX, "totalY": totalY, "primaryIn": primaryIn, "mData": mData, "layoutType": layoutType}
    logger.info(f"Monitor Info: {mInfo.mInfoCache}")

    return mInfo.mInfoCache


def get_offset(offSetType: Literal["x", "y", "w", "h"]) -> int:
    """
    Calculate and get the offset settings for the monitor.
    """
    logger.info(f"Getting offset for {offSetType}")
    if offSetType == "w":
        w = 60 if fJson.settingCache["offSetW"] == "auto" else fJson.settingCache["offSetW"]
        logger.debug(f"Offset W: {w}")
        return w
    elif offSetType == "h":
        h = 60 if fJson.settingCache["offSetH"] == "auto" else fJson.settingCache["offSetH"]
        logger.debug(f"Offset H: {h}")
        return h
    else:
        if fJson.settingCache["offSetX"] != "auto" and offSetType == "x":  # if x and manual
            logger.debug(f"Offset X: {fJson.settingCache['offSetX']}")
            return fJson.settingCache["offSetX"]
        elif fJson.settingCache["offSetY"] != "auto" and offSetType == "y":  # if y and manual
            logger.debug(f"Offset Y: {fJson.settingCache['offSetY']}")
            return fJson.settingCache["offSetY"]

        # else check auto offset for x and y
        mGet = get_monitors()
        totalMonitor = len(mGet)

        if totalMonitor == 1:
            logger.debug(f"Offset {offSetType}: 0")
            return 0  # no offset if only 1 monitor on both x and y

        totalX = 0
        totalY = 0
        index = 0
        primaryIn = 0
        mData = []
        for m in mGet:
            mData.append(m)
            totalX += abs(m.x)
            totalY += abs(m.y)
            if m.is_primary:
                primaryIn = index
            index += 1

        # auto x
        if offSetType == "x":
            if totalX > totalY and primaryIn != 0:  # Horizontal and primary not in the first monitor
                logger.debug(f"Offset X: {abs(mData[primaryIn - 1].x)}")
                return abs(mData[primaryIn - 1].x)
            else:
                logger.debug(f"Offset X: 0")
                return 0
        # auto y
        elif offSetType == "y":
            if totalY > totalX and primaryIn != 0:  # Vertical
                logger.debug(f"Offset Y: {abs(mData[primaryIn - 1].y)}")
                return abs(mData[primaryIn - 1].y)
            else:
                logger.debug(f"Offset Y: 0")
                return 0


def getScreenTotalGeometry():
    snippingType = None
    # Get ScreenData
    screenData = getScreenInfo()

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
    if screenData["layoutType"] == "horizontal":
        if primaryIn != 0:  # Make sure its not the first monitor
            counter = 0
            for monitor in screenData["mData"]:
                if counter != primaryIn:
                    offset_X += monitor.x

            # Set to 0 because the first monitor is the primary monitor
            if offset_X > 0:
                offset_X = 0
        else:
            offset_X = 0
    else:
        if primaryIn != 0:  # Make sure its not the first monitor
            counter = 0
            for monitor in screenData["mData"]:
                if counter != primaryIn:
                    offset_Y += monitor.y

            # Set to 0 because the first monitor is the primary monitor
            if offset_Y > 0:
                offset_Y = 0
        else:
            offset_Y = 0

    # ------------------
    # Result
    totalX: int = screenData["totalX"]
    totalY: int = screenData["totalY"]

    # Get the full screen size
    screenTotalGeometry = f"{totalX}x{totalY}+{str(offset_X)}+{str(offset_Y)}"
    logger.debug(f"Total Window Geometry: {screenTotalGeometry}")

    return screenTotalGeometry, totalX, totalY, int(offset_X), int(offset_Y)
