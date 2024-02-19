import os

import simpleaudio as sa

from screen_translate._logging import logger
from screen_translate._path import path_beep


def beep():
    if not os.path.exists(path_beep):
        logger.warning(f"{path_beep} not found. Beep sound will not be played.")
        return
    try:
        wave_obj = sa.WaveObject.from_wave_file(path_beep)
        wave_obj.play()
    except Exception as e:
        logger.exception(e)
