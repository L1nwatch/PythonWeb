#!/bin/env python3
# -*- coding: utf-8 -*-
# version: Python3.X
"""
# 测试 Django 是否正常工作
"""
from selenium import webdriver

__author__ = '__L1n__w@tch'

if __name__ == "__main__":
    browser = webdriver.Firefox()
    browser.get("http://localhost:8000")
    assert 'Django' in browser.title
