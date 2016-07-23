#!/bin/env python3
# -*- coding: utf-8 -*-
# version: Python3.X
"""
负责编写视图的地方
"""
from django.shortcuts import render
from django.http import HttpResponse

__author__ = '__L1n__w@tch'


# Create your views here.
def home_page(requests):
    return HttpResponse("<html><title>To-Do lists</title></html>")


if __name__ == "__main__":
    pass
