import asyncio
from typing import Literal

from screen_translate.Logging import logger
from screen_translate.Globals import fJson, gClass
from screen_translate.components.MBox import Mbox
from screen_translate.utils.Translator import google_tl, memory_tl, libre_tl, deepl_tl, pons_tl


def translate(query: str, from_lang: str, to_lang: str, engine: Literal["Google Translate", "Deepl", "MyMemoryTranslator", "PONS", "LibreTranslate"]):
    """Translate text

    Args:
    ---
        query (str): Text to translate
        from_lang (str): Language to translate from
        to_lang (str): Language to translate to
        engine (Literal["Google Translate", "Deepl", "MyMemoryTranslator", "PONS", "LibreTranslate"]): Engine to use
    """
    gClass.lb_start()
    logger.info(f"-" * 50)
    logger.info(f"Translate")
    logger.info(f"Length: {len(query)} -> {len(query.strip())} (stripped) | from {from_lang} to {to_lang} using {engine}")
    
    query = query.strip()
    if len(query) == 0:
        logger.warn("No text to translate!")
        gClass.lb_stop()
        return

    # --------------------------------
    # Deepl
    if engine == "Deepl":
        loop = asyncio.get_event_loop()  # deepl run separately because it is async
        loop.run_until_complete(deeplTl(query, from_lang, to_lang))
        return

    # --------------------------------
    # Google Translate
    if engine == "Google Translate":
        oldMethod = False
        if "- Alt" in from_lang or "- Alt" in to_lang:
            oldMethod = True
        success, result = google_tl(query, from_lang, to_lang, oldMethod=oldMethod)
    # --------------------------------
    # MyMemoryTranslator
    elif engine == "MyMemoryTranslator":
        success, result = memory_tl(query, from_lang, to_lang)
    # --------------------------------
    # PONS
    elif engine == "PONS":
        success, result = pons_tl(query, from_lang, to_lang)
    # --------------------------------
    # LibreTranslate
    elif engine == "LibreTranslate":
        success, result = libre_tl(
            query, to_lang, from_lang, https=fJson.settingCache["libre_https"], host=fJson.settingCache["libre_host"], port=fJson.settingCache["libre_port"], apiKeys=fJson.settingCache["libre_api_key"]
        )

    fill_tb_save_history(success, from_lang, to_lang, query, str(result), engine)

    gClass.lb_stop()


async def deeplTl(query: str, from_lang: str, to_lang: str):
    """Translate using deepl"""
    isSuccess, translateResult = await deepl_tl(query, to_lang, from_lang)
    fill_tb_save_history(isSuccess, from_lang, to_lang, query, str(translateResult), "Deepl")
    gClass.lb_stop()


def fill_tb_save_history(isSuccess: bool, from_lang: str, to_lang: str, query: str, result: str, engine: Literal["Google Translate", "Deepl", "MyMemoryTranslator", "PONS", "LibreTranslate"]):
    """Save the text to history"""
    if isSuccess:
        # clear tb
        gClass.clear_mw_res()
        gClass.clear_ex_res()

        # Fill the textbox
        gClass.insert_mw_res(result)
        gClass.insert_ex_res(result)

        if fJson.settingCache["save_history"]:
            # Write to History
            new_data = {"from": from_lang, "to": to_lang, "query": query, "result": result, "engine": engine}
            fJson.writeAdd_History(new_data)
            logger.info("TL saved to history")

    else:
        logger.info("Fail to translate and save to history")
        Mbox("Error: Translation Failed", result, 2)
