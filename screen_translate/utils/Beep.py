import os
import simpleaudio as sa

from screen_translate._path import dir_assets
from screen_translate.Logging import logger


def beep():
    beepPath = os.path.join(dir_assets, "beep.wav")
    if not os.path.exists(beepPath):
        logger.warning(f"{beepPath} not found. Beep sound will not be played.")
        return
    try:
        wave_obj = sa.WaveObject.from_wave_file(beepPath)
        wave_obj.play()
    except Exception as e:
        logger.exception(e)
