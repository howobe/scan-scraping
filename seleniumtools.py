#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from typing import TypeVar
import json
import utils

T = TypeVar('T')


class ElementTracker():

    def __init__(self, headless=True):
        self.driverOpts = Options()
        self.driverOpts.headless = headless

    def setUrl(self, url: str):
        self.url = url

    def setElement(self, element: str, method: str, hidden=False):
        self.element = {'element': element, 'hidden': hidden}
        if method in By.__dict__.values():
            self.element["method"] = method
            print("ok")
        else:
            print("Invalid method chosen. Consult 'By' attributes.")

    def setEvent(self, value: T = None, isKVPair=False, comp: str = "eq"):
        if isKVPair:
            value["value"] = str(value["value"]).lower()
        else:
            value = str(value).lower()
        self.trigger = {"value": value, "isKVPair": isKVPair, "comp":
                        comp.center(6, '_')}

    def setAction(self, actElement: str, method: str, hidden=False):
        self.actElement = {'element': actElement, 'hidden': hidden}
        if method in By.__dict__.values():
            self.actElement["method"] = method
            print("ok")
        else:
            print("Invalid method chosen. Consult 'By' attributes.")
            return

    def act(self, dictKeys: T = None):
        self._actEl = self.driver.find_element(self.actElement["method"],
                                               self.actElement["element"])
        if self.actElement["hidden"]:
            self._actEl = self.unhide(self._actEl, self.actElement)
        if dictKeys is None:
            return self._actEl.text
        actElStruct = self._jsonHandler(self._actEl.text)
        res = []
        if not isinstance(dictKeys, list):
            dictKeys = list(dictKeys)
        for el in actElStruct:
            res.extend([el[k] for k in dictKeys])
        return res

    def monitor(self):
        self.driver = webdriver.Firefox(options=self.driverOpts)
        self.driver.get(self.url)
        self._element = WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((self.element["method"],
                                                self.element["element"])))
        if self.element["hidden"]:
            self._element = self.unhide(self._element, self.element)
        self.elementText = self._element.text

    def unhide(self, driverElement, element):
        self.driver.execute_script("arguments[0].style.display = 'block';",
                                   driverElement)
        return self.driver.find_element(element["method"],
                                        element["element"])

    def check(self) -> bool:
        if not self.trigger["isKVPair"]:
            if getattr(self.elementText.lower(), self.trigger["comp"])(
                    self.trigger["value"]):
                self.announce()
                return True
        else:
            elementStruct = self._jsonHandler(self.elementText)
            for i in elementStruct:
                if getattr(i[self.trigger["key"]], self.trigger["comp"])(
                        self.trigger["value"]):
                    self.announce()
                    return True
        return False

    def _jsonHandler(self, elementText):
        elementStruct = json.loads(elementText)
        if type(elementStruct) != list:
            elementStruct = list(elementStruct)
        return elementStruct

    def announce(self):
        print("found it")

