#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Oct 29 22:48:21 2020

@author: bj
"""


def xor(lst):
    if not lst:
        return
    return lst[0] != xor(lst[1:])
