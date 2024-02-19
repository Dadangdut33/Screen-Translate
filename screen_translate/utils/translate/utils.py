from typing import Dict

import pyperclip

from screen_translate._globals import fj, gcl
from screen_translate._logging import logger

from ..helper import native_notify
from .translator import deepl_tl, google_tl, libre_tl, memory_tl, pons_tl

tl_dict = {
    "Google Translate": google_tl,
    "PONS": pons_tl,
    "MyMemoryTranslator": memory_tl,
    "LibreTranslate": libre_tl,
    "Deepl": deepl_tl,
}


def translate(engine: str, text: str, from_lang: str, to_lang: str, proxies: Dict, debug_log: bool = False, **kwargs):
    """Translate

    Args
    ----
        engine (str): Engine to use
        text (str): Text to translate
        from_lang (str): Language From
        to_lang (str): Language to translate
        proxies (Dict): Proxies. Defaults to None.
        debug_log (bool, optional): Debug Log. Defaults to False.
        **libre_kwargs: LibreTranslate kwargs

    Returns
    -------
        is_success: Success or not
        result: Translation result
    """
    logger.debug(f"Translate: {text} from {from_lang} to {to_lang} using {engine}")
    text = text.strip()
    if len(text) == 0:
        logger.warning("No text to translate!")
        return

    if engine not in tl_dict:
        raise ValueError(f"Invalid engine. Engine {engine} not found")

    status, msg = tl_dict[engine](text, from_lang, to_lang, proxies, debug_log, **kwargs)

    fill_tb_save_history(status, from_lang, to_lang, text, msg, engine)
    gcl.lb_stop()


def fill_tb_save_history(sucess: bool, from_lang: str, to_lang: str, query: str, result: str, engine: str):
    """Save the text to history"""
    if sucess:
        # clear tb
        gcl.clear_mw_res()
        gcl.clear_ex_res()

        # Fill the textbox
        gcl.insert_mw_res(result)
        gcl.insert_ex_res(result)

        if fj.setting_cache["auto_copy_translated"]:
            pyperclip.copy(result)
            logger.info("Copied translated text to clipboard!")

        if fj.setting_cache["auto_copy_captured"] and fj.setting_cache["auto_copy_translated"]:
            pyperclip.copy(query + " -> " + result)
            logger.info("Copied captured and translated text to clipboard!")

        if fj.setting_cache["save_history"]:
            # Write to History
            new_data = {"from": from_lang, "to": to_lang, "query": query, "result": result, "engine": engine}
            fj.write_add_history(new_data)
            logger.info("TL saved to history")

    else:
        logger.info("Fail to translate and save to history")
        native_notify("Error: Translation Failed", result)
