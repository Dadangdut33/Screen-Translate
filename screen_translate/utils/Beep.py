import os
import sounddevice as sd
import soundfile as sf

from screen_translate.Globals import dir_assets
from screen_translate.Logging import logger


def beep():
    beepPath = os.path.join(dir_assets, "beep.mp3")
    try:
        data, fs = sf.read(beepPath)
        sd.play(data, fs, blocking=False)
    except Exception as e:
        logger.exception(e)
        pass
