from screeninfo import get_monitors

# Settings to capture all screens
from PIL import ImageGrab
from functools import partial

ImageGrab.grab = partial(ImageGrab.grab, all_screens=True)


class MonitorInfo:
    def __init__(self):
        self.mInfoCache = {"totalX": 0, "totalY": 0, "primaryIn": None, "mData": None, "layoutType": None}
        self.mInfoCache = self.getScreenInfo()  # Fill the cache

    def getWidthAndHeight(self):
        # Better solution for this case on getting the width and height
        # get_monitors() are not accurate sometimes
        img = ImageGrab.grab()
        totalX = img.size[0]
        totalY = img.size[1]

        return totalX, totalY

    def getScreenInfo(self):
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

        if self.mInfoCache["mData"] != mData:
            totalX, totalY = self.getWidthAndHeight()
        else:
            totalX = self.mInfoCache["totalX"]
            totalY = self.mInfoCache["totalY"]

        if totalX > totalY:
            layoutType = "horizontal"
        else:
            layoutType = "vertical"

        self.mInfoCache = {"totalX": totalX, "totalY": totalY, "primaryIn": primaryIn, "mData": mData, "layoutType": layoutType}

        return self.mInfoCache


def get_offset(offSetX, offSetY, offSetW, offSetH, offSetXYType, custom=None):
    """
    Calculate and get the offset settings for the monitor.
    """
    x, y, w, h = 0, 0, 0, 0

    if custom is not None:
        offSetX = "auto"
        offSetY = "auto"

    w = 60 if offSetW == "auto" else offSetW
    h = 60 if offSetH == "auto" else offSetH

    #  If offset is set
    if offSetXYType.lower() != "no offset" or custom is not None:
        totalMonitor = len(get_monitors())
        totalX = 0
        totalY = 0
        index = 0
        primaryIn = 0
        mData = []
        for m in get_monitors():
            mData.append(m)
            totalX += abs(m.x)
            totalY += abs(m.y)
            if m.is_primary:
                primaryIn = index
            index += 1

        # If auto
        if offSetX == "auto":
            if totalMonitor > 1:
                if totalX > totalY:  # Horizontal
                    if primaryIn != 0:  # Make sure its not the first monitor
                        x = abs(mData[primaryIn - 1].x)
                    else:
                        x = 0
                else:
                    x = 0
            else:
                x = 0
        else:  # if set manually
            x = offSetX

        # If auto
        if offSetY == "auto":
            if totalMonitor > 1:
                if totalY > totalX:  # Vertical
                    if primaryIn != 0:
                        y = abs(mData[primaryIn - 1].y)
                    else:
                        y = 0
                else:
                    y = 0
            else:
                y = 0
        else:  # if set manually
            y = offSetY

    offSetsGet = [x, y, w, h]
    return offSetsGet
