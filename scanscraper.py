#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import requests
from bs4 import BeautifulSoup
from bs4.element import Tag as bs4Tag
import json
import dicttools
import pandas as pd


class WebScraper():

    def __init__(self, url: str):
        self.url = url
        self.soup = self.getParsedResponse()

    @staticmethod
    def makeRequest(url: str) -> requests.models.Response:
        return requests.get(url, headers={"User-Agent": "Mozilla/5.0"})

    @staticmethod
    def parse(response: requests.models.Response, parser: str = "lxml"
              ) -> BeautifulSoup:
        return BeautifulSoup(response.content, parser)

    def getParsedResponse(self):
        self.response = WebScraper.makeRequest(self.url)
        return WebScraper.parse(self.response)


class ScanScraper(WebScraper):

    baseUrl = "https://www.scan.co.uk"

    def __init__(self, url: str, **kwargs):
        super().__init__(url)
        self.scrape(**kwargs)

    @classmethod
    def fromSearchQuery(cls, searchQuery: str, queryResults: int = None):
        searchUrl = ScanScraper.createQueryUrl(cls.baseUrl, searchQuery)
        return cls(searchUrl, threshold=queryResults)

    @classmethod
    def selectCateogryFromSearchQuery(cls, searchQuery: str, **kwargs):
        searchUrl = ScanScraper.createQueryUrl(cls.baseUrl, searchQuery)
        response = ScanScraper.makeRequest(searchUrl)
        soup = ScanScraper.parse(response)
        url = cls._selectItemCategories(cls._getItemCategories(soup))
        return cls(cls.baseUrl + url)

    def _getItemCategories(parsedResponse: BeautifulSoup) -> list:
        ics = parsedResponse.find_all("span", {"class": "itemCategorys"})
        icsConcat = []
        for i in ics:
            icsConcat += i.find_all("a")
        return icsConcat

    def _selectItemCategories(itemCategories: list, superC=False) -> str:
        if not superC:
            itemCategories = itemCategories[1::2]
        for index, item in enumerate(itemCategories, 1):
            print(f"{index}. {item.text}")
        chosenCat = int(input("Select category: "))
        return itemCategories[chosenCat-1].get("href")

    def alterURL(self, url: str, **kwargs):
        self.scrape(url, **kwargs)

    def getStatusCode(self) -> int:
        return self.response.status_code

    def scrape(self, threshold: int = None):
        self.resetData()
        self.description = self._getMainCategoryTitle(self.soup)
        cats = self._getCategoryDivs(self.soup)
        breaker = False
        for cat in cats:
            self.stats["cats"] += 1
            if len(cats) < 2:
                title = self.description
            else:
                title = self._getSubcateogryTitle(cat)
            cols = self._getProductColumnList(cat)
            prods, lns, rCols = self._getProductData(cols)
            self.products[title] = []
            for prod, ln, rCol in zip(prods, lns, rCols):
                if threshold is not None:
                    if self.stats["items"] >= threshold:
                        breaker = True
                        break
                pDict = self._getProductDictionary(prod, ln, rCol)
                self.products[title].append(pDict)
            if breaker:
                break

    def _getMainCategoryTitle(self, parsedResponse: BeautifulSoup):
        return parsedResponse.find("h1").text

    def _getCategoryDivs(self, parsedResponse: BeautifulSoup) -> list:
        return parsedResponse.find_all("div", {"class": "category"})

    def _getSubcateogryTitle(self, category: bs4Tag) -> str:
        return category.find("h2").text.strip("\n")

    def _getProductColumnList(self, category: bs4Tag) -> list:
        return category.find_all("div", {"class":
                                         "productsCont"})

    def _getProductData(self, columns: list) -> tuple:
        prods, lns, rCols = [], [], []
        for col in columns:
            prods += col.find_all("li", {"class": "product"})
            lns += col.find_all("span", {"class": "linkNo"})
            rCols += col.find_all("div", {"class": "rightColumn"})
        return prods, lns, rCols

    def _getStockData(self, stockDataDiv: bs4Tag):
        return int(stockDataDiv.find("div").attrs["data-instock"])

    def _assignStockStatus(self, productDict: dict):
        stockStatusStrs = ["outofstock", "instock", "unreleased"]
        self.stocks[stockStatusStrs[productDict["stockStatus"]]].\
            append(productDict["data-description"])

    def _getProductDictionary(self, prod: bs4Tag, ln: bs4Tag, rCol: bs4Tag,
                              threshold: int = None) -> dict:
        tempDict = {k: v for k, v in prod.attrs.items() if k in self.dataAttrs}
        tempDict["linkNo"] = ln.text
        prodPrice = float(tempDict["data-price"])
        if prodPrice == 999999.00:
            tempDict["stockStatus"] = -1
            tempDict["data-price"] = None
            self.stats["unreleased"] += 1
        else:
            prodStock = self._getStockData(rCol)
            tempDict["stockStatus"] = prodStock
            tempDict["data-price"] = prodPrice
            self.stats["instock"] += prodStock
            self.prices.append(prodPrice)
        self._assignStockStatus(tempDict)
        self.stats["items"] += 1
        self.computeStats()
        return tempDict

    def recount(self):
        self.stats["cats"] = len(self.products)
        flattened = dicttools.flatten(self.products, "cat")
        self.reset()
        for prod in flattened:
            self.stats["items"] += 1
            if prod["stockStatus"] >= 0:
                self.stats["instock"] += prod["stockStatus"]
            else:
                self.stats["unreleased"] += 1
            self._assignStockStatus(prod)
            self.prices.append(prod["data-price"])
        self.computeStats()

    def computeStats(self):
        if len(self.prices) > 0:
            self.stats["minPrice"] = min(self.prices)
            self.stats["maxPrice"] = max(self.prices)
            self.stats["avePrice"] = sum(self.prices) / len(self.prices)

    def getDescription(self) -> str:
        return self.description

    def getCategories(self) -> list:
        return self.products.keys()

    def getDataAttributes(self) -> list:
        return self.dataAttrs

    def addDataAttribute(self, attribute: str):
        if attribute.strip("data-") == attribute:
            attribute = "data-" + attribute
        self.dataAttrs.append(attribute)

    def printCategories(self):
        dicttools.printDict(self.products, keys=True)

    def printProducts(self):
        for cat in self.products.keys():
            dicttools.printDict(self.products[cat], values=True)

    def createJsonFile(self, filename: str):
        if filename.strip(".") == filename:
            filename += ".json"
        with open(filename, 'w') as out:
            json.dump(self.products, out, indent=4)

    def resetData(self):
        self.stats = dict.fromkeys(["cats", "items", "instock", "unreleased",
                                    "minPrice", "maxPrice", "avePrice"], 0)
        self.prices = []
        self.stocks = {"instock": [], "outofstock": [], "unreleased": []}
        self.dataAttrs = ["data-"+i for i in ["description", "manufacturer",
                                              "price", "productflags", "wpid"]]
        self.products = {}

    def createDataFrame(self) -> pd.core.frame.DataFrame:
        flattened = dicttools.flatten(self.products, "category")
        return pd.DataFrame.from_dict(flattened)

    @staticmethod
    def createQueryUrl(baseUrl: str, queryParameters: str) -> str:
        searchExt = "/search?q="
        return baseUrl + searchExt + queryParameters.replace(" ", "+")
