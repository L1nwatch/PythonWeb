#!/bin/env python3
# -*- coding: utf-8 -*-
# version: Python3.X
"""
负责编写视图的地方
"""
from django.http import HttpResponse
from django.shortcuts import redirect, render
from lists.models import Item

__author__ = '__L1n__w@tch'


# Create your views here.
def home_page(request):
    if request.method == "POST":
        # .objects.create 是创建新 Item 对象的简化方式，无需再调用 .save() 方法
        Item.objects.create(text=request.POST["item_text"])
        return redirect("/lists/the-only-list-in-the-world")

    return render(request, "home.html")


def view_list(request):
    items = Item.objects.all()
    return render(request, "list.html", {"items": items})


if __name__ == "__main__":
    pass
