#!/bin/env python3
# -*- coding: utf-8 -*-
# version: Python3.X
"""
负责编写视图的地方
"""
from django.shortcuts import render

__author__ = '__L1n__w@tch'


# Create your views here.
def home_page(request):
    return render(request, "home.html", {
        "new_item_text": request.POST.get("item_text", ""),
    })


if __name__ == "__main__":
    pass
