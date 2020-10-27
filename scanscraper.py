#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Oct 26 16:55:40 2020

@author: bj

To do:
    Make dict of prods
    Make adjustments (get h1) for single cat. pages
    setup add to order (https://secure.scan.co.uk/web/basket/addproduct/\
    2987654)
    add notifier functionality
    setup pi integration

    ignore data-price = 999999.0 - indicator unreleased
    if no 999999.0, check instock

    {cat1: [{'prodInfo': {'name':xxx,...,}, ..., ], cat2: [...]}
"""
import requests
from bs4 import BeautifulSoup
import time
import json
from typing import TypeVar

T = TypeVar('T')

ssdurl = "https://www.scan.co.uk/shop/computer-hardware/solid-state-drives/all"
ssdurl = "https://www.scan.co.uk/shop/computer-hardware/gpu-nvidia/nvidia-geforce-rtx-3080-graphics-cards"


class ScanScraper():

    stats = dict.fromkeys(["cats", "items", "instock", "unreleased",
                           "minPrice", "maxPrice", "avePrice"], 0)
    stocks = {"instock": [], "outofstock": [], "unreleased": []}

    def __init__(self, url: str, **kwargs):
        self.scrape(url, **kwargs)

    @classmethod
    def fromSearchQuery(cls, searchQuery: str, queryResults: int):
        baseUrl = "https://www.scan.co.uk/search?q="
        adjustedQuery = searchQuery.replace(" ", "+")
        return cls(baseUrl+adjustedQuery, threshold=queryResults)

    def alterURL(self, url: str):
        self.scrape(url)

    def scrape(self, url: str, threshold: int = None):
        response = ScanScraper.makeRequest(url)
        self.soup = ScanScraper.parse(response)
        self.getDictOfProducts(self.soup, threshold)

    def getDictOfProducts(self, parsedResponse: BeautifulSoup,
                          threshold: int = None):
        reqAttrs = ["data-"+i for i in ["description", "manufacturer", "price",
                                        "productflags", "wpid"]]
        division = parsedResponse.find("h1").text
        self.description = division
        cats = parsedResponse.find_all("div", {"class": "category"})
        total, prices, breaker = {}, [], False
        for cat in cats:
            self.stats["cats"] += 1
            if len(cats) > 1:
                title = cat.find("h2").text.strip("\n")
            else:
                title = division
            trueProds = cat.find_all("ul", {"class": "productColumns"})
            prods, lns, rCols = [], [], []
            for col in trueProds:
                prods += col.find_all("li", {"class": "product"})
                lns += col.find_all("span", {"class": "linkNo"})
                rCols += col.find_all("div", {"class": "rightColumn"})
            total[title] = []
            for prod, ln, rCol in zip(prods, lns, rCols):
                self.stats["items"] += 1
                if threshold is not None:
                    if self.stats["items"] >= threshold:
                        breaker = True
                        break
                tempDict = {k: v for k, v in prod.attrs.items() if k in
                            reqAttrs}
                tempDict["linkNo"] = ln.text
                prodPrice = float(tempDict["data-price"])
                if prodPrice == 999999.00:
                    tempDict["stockStatus"] = -1
                    tempDict["data-price"] = None
                    self.stats["unreleased"] += 1
                else:
                    prodStock = int(rCol.find("div").attrs["data-instock"])
                    tempDict["stockStatus"] = prodStock
                    tempDict["data-price"] = prodPrice
                    self.stats["instock"] += prodStock
                    prices.append(prodPrice)
                self.sortStockStatus(tempDict)
                total[title].append(tempDict)
            if breaker:
                break
        self.computeStats(prices)
        self.products = total

    def computeStats(self, prices: list):
        if len(prices) > 0:
            self.stats["minPrice"] = min(prices)
            self.stats["maxPrice"] = max(prices)
            self.stats["avePrice"] = sum(prices)/len(prices)

    def getDescription(self) -> str:
        return self.description

    def getCategories(self) -> list:
        return self.products.keys()

    def printCategories(self):
        ScanScraper.printDict(self.products, keys=True)

    def printProducts(self):
        for cat in self.products.keys():
            ScanScraper.printDict(self.products[cat], values=True)

    def sortStockStatus(self, productDict: dict):
        stockStatusStrs = ["outofstock", "instock", "unreleased"]
        self.stocks[stockStatusStrs[productDict["stockStatus"]]].\
            append(productDict["data-description"])

    def createJsonFile(self, filename: str):
        if filename.strip(".") == filename:
            filename += ".json"
        with open(filename, 'w') as out:
            json.dump(self.products, out, indent=4)

    @staticmethod
    def printDict(dictionary: dict, keys=False, values=False,
                  keyName: T = None):
        ks, vs = dictionary.keys(), dictionary.values()
        if keys == values:
            for k, v in zip(ks, vs):
                print(f"{k}:{v}")
        elif keys:
            for k in ks:
                print(k)
        elif values:
            for v in vs:
                print(v)
        elif keyName is not None:
            for v in dictionary[keyName]:
                print(v)

    @staticmethod
    def makeRequest(url: str) -> requests.models.Response:
        return requests.get(url, headers={"User-Agent": "Mozilla/5.0"})

    @staticmethod
    def parse(response: requests.models.Response, parser: str = "lxml"
              ) -> BeautifulSoup:
        return BeautifulSoup(response.content, parser)
