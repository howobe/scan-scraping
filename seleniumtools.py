#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.common import exceptions as SeleniumExceptions
from typing import TypeVar
import json
import logging

T = TypeVar('T')
logger = logging.getLogger("elementTracker")


class ElementTracker():

    def __init__(self, headless=True):
        self.driverOpts = Options()
        self.driverOpts.headless = headless
        logger.debug("Driver options: headless=" + str(headless))

    def setUrl(self, url: str):
        self.url = url
        logger.info("Url set: " + self.url)

    def setElement(self, element: str, method: str, hidden=False):
        if method in By.__dict__.values():
            self.element = {'element': element, 'method': method,
                            'hidden': hidden}
            logger.info("Element defined: " + str(self.element))
        else:
            logger.warning("Invalid search method chosen: " + method)

    def setEvent(self, value: T = None, isKVPair=False, comp: str = "eq"):
        if isKVPair:
            assert isinstance(value, dict), "Dictionary not provided"
            value["value"] = str(value["value"]).lower()
        else:
            value = str(value).lower()
        self.trigger = {"value": value, "isKVPair": isKVPair, "comp":
                        comp.center(6, '_')}
        logger.info("Trigger defined: " + str(self.trigger))

    def setAction(self, actElement: str, method: str, hidden=False):
        if method in By.__dict__.values():
            self.actElement = {'element': actElement, 'method': method,
                               'hidden': hidden}
            logger.info("Actionable element defined: " + str(self.actElement))
        else:
            logger.warning("Invalid search method chosen: " + method)

    def act(self, dictKeys: T = None) -> str:
        logger.info("Executing action...")
        try:
            self._actEl = self.driver.find_element(self.actElement["method"],
                                                   self.actElement["element"])
            logger.debug("Actionable element found")
        except SeleniumExceptions.NoSuchElementException as e:
            logger.exception(e)
        if self.actElement["hidden"]:
            self._actEl = self.unhide(self._actEl, self.actElement)
        if dictKeys is None:
            logger.info("Returing result")
            return self._actEl.text
        actElStruct = self._jsonHandler(self._actEl.text)
        res = []
        if not isinstance(dictKeys, list):
            dictKeys = list(dictKeys)
        for el in actElStruct:
            try:
                res.extend([el[k] for k in dictKeys])
            except KeyError as e:
                logger.exception(e)
        return ", ".join(res)

    def findElement(self):
        logger.debug("Starting webdriver...")
        self.driver = webdriver.Firefox(options=self.driverOpts)
        logger.debug("Driver loaded, loading webpage...")
        self.driver.get(self.url)
        logger.debug("Webpage loaded")
        try:
            self._element = WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((self.element["method"],
                                                self.element["element"])))
        except Exception as e:
            logger.exception(e)

        if self.element["hidden"]:
            self._element = self.unhide(self._element, self.element)
        self.elementText = self._element.text
        logger.debug("Element text: " + self.elementText)

    def unhide(self, driverElement, element):
        logger.debug("Unhiding element: " + str(element))
        self.driver.execute_script("arguments[0].style.display = 'block';",
                                   driverElement)
        return self.driver.find_element(element["method"],
                                        element["element"])

    def check(self) -> bool:
        logger.debug("Performing check...")
        if not self.trigger["isKVPair"]:
            logger.debug(f"Check occuring: {self.elementText.lower()}, " +
                         f"{self.trigger['comp']}, {self.trigger['value']}")
            if getattr(self.elementText.lower(), self.trigger["comp"])(
                    self.trigger["value"]):
                logger.info("Event conditions met!")
                return True
        else:
            elementStruct = self._jsonHandler(self.elementText)
            for i in elementStruct:
                logger.debug(f"Check occuring: {i[self.trigger['key']]}, " +
                             f"{self.trigger['comp']}, {self.trigger['value']}"
                             )
                if getattr(i[self.trigger["key"]], self.trigger["comp"])(
                        self.trigger["value"]):

                    logger.info("Event conditions met!")
                    return True
        logger.info("Event conditions not met")
        return False

    def _jsonHandler(self, elementText):
        try:
            elementStruct = json.loads(elementText)
        except Exception as e:
            logger.exception(e)
        if type(elementStruct) != list:
            elementStruct = list(elementStruct)
        return elementStruct

    def end(self):
        self.driver.close()
        logger.info("Driver closed")
