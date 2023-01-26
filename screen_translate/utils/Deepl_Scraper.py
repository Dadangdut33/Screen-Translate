"""
* ORIGINAL FROM https://github.com/ffreemt/deepl-scraper-playwright
* Modified to works with thread by using playwright.sync_api.sync_playwright

Scrape deepl via playwright.

org deepl_tr_pp

import os
from pathlib import Path
os.environ['PYTHONPATH'] = Path(r"../get-pwbrowser-sync")
"""
import re
from time import sleep
from typing import Any, Callable, Optional
from urllib.parse import quote

from playwright.sync_api import sync_playwright
from pyquery import PyQuery as pq

from screen_translate.Logging import logger

URL = r"https://www.deepl.com/translator"


def with_func_attrs(**attrs: Any) -> Callable:
    """with_func_attrs"""

    def with_attrs(fct: Callable) -> Callable:
        for key, val in attrs.items():
            setattr(fct, key, val)
        return fct

    return with_attrs


@with_func_attrs(from_lang="", to_lang="", text="")
def deepl_tr(text: str, from_lang: str = "auto", to_lang: str = "zh", timeout: float = 5, headless: Optional[bool] = None):
    """Deepl via playwright-sync.

    text = "Test it and\n\n more"
    from_lang="auto"
    to_lang="zh"
    """

    # check playwright browser

    try:
        text = text.strip()
    except Exception as exc:
        logger.error(exc)
        logger.info("not a string?")
        raise

    logger.debug("Spawning playwright-sync")
    with sync_playwright() as playwright:
        logger.debug("Launching browser")
        browser = playwright.chromium.launch(headless=headless)

        logger.debug("Creating page")
        page = browser.new_page()

        logger.debug(f"Moving to {URL}")
        page.goto(URL, timeout=45 * 1000)

        logger.debug("Page loaded")
        # ----------------------------
        url0 = f"{URL}#{from_lang}/{to_lang}/"
        url_ = f"{URL}#{from_lang}/{to_lang}/{quote(text)}"

        # selector = ".lmt__language_select--target > button > span"
        try:
            content = page.content()
        except Exception as exc:
            logger.error(exc)
            raise

        doc = pq(content)
        text_old = doc("#source-dummydiv").html()

        # selector = "div.lmt__translations_as_text"
        if text.strip() == text_old.strip() and same_langs:  # type: ignore
            logger.debug(" ** early result: ** ")
            logger.debug("%s, %s", text, doc(".lmt__translations_as_text__text_btn").html())
            doc = pq(page.content())
            # content = doc(".lmt__translations_as_text__text_btn").text()
            content = doc(".lmt__translations_as_text__text_btn").html()
        else:
            # record content
            try:
                # page.goto(url_)
                page.goto(url0)
            except Exception as exc:
                logger.error(exc)
                raise

            try:
                # page.wait_for_selector(".lmt__translations_as_text", timeout=20000)
                page.wait_for_selector(".lmt__target_textarea", timeout=20000)
            except Exception as exc:
                logger.error(exc)
                raise

            doc = pq(page.content())
            # content_old = doc(".lmt__translations_as_text__text_btn").text()
            content_old = doc(".lmt__translations_as_text__text_btn").html()

            # selector = ".lmt__translations_as_text"
            # selector = ".lmt__textarea.lmt__target_textarea.lmt__textarea_base_style"
            # selector = ".lmt__textarea.lmt__target_textarea"
            # selector = '.lmt__translations_as_text__text_btn'
            try:
                page.goto(url_)
            except Exception as exc:
                logger.error(exc)
                raise

            try:
                # page.wait_for_selector(".lmt__translations_as_text", timeout=20000)
                page.wait_for_selector(".lmt__target_textarea", timeout=20000)
            except Exception as exc:
                logger.error(exc)
                raise

            doc = pq(page.content())
            content = doc(".lmt__translations_as_text__text_btn").text()

            # loop until content changed
            idx = 0
            # bound = 50  # 5s
            logger.debug("Getting content... wait...")
            while idx < timeout / 0.1:
                idx += 1
                sleep(0.1)
                doc = pq(page.content())
                content = doc(".lmt__translations_as_text__text_btn").html()

                if content_old != content and bool(content):
                    break

            logger.debug("Total Loop: %s", idx)

            browser.close()

        logger.info("Content get!")

        # remove possible attached suffix
        content = re.sub(r"[\d]+_$", "", content.strip()).strip()  # type: ignore

        return content
