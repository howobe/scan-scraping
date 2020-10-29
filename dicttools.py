#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# {cat: [{}, {}, {}, ...]}
from typing import TypeVar

T = TypeVar('T')


def flatten(dictionary: dict, newKeyName: str) -> list:
    newArr = []
    for k, v in dictionary.items():
        newArr.extend([{**vi, **{newKeyName: k}} for vi in v])
    return newArr


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
