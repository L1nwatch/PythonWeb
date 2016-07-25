#!/bin/env python3
# -*- coding: utf-8 -*-
# version: Python3.X
"""
负责编写视图的地方
"""
from django.http import HttpResponse
from django.shortcuts import redirect, render
from lists.models import Item, List

__author__ = '__L1n__w@tch'


# Create your views here.
def home_page(request):
    return render(request, "home.html")


def view_list(request):
    items = Item.objects.all()
    return render(request, "list.html", {"items": items})


def new_list(request):
    list_ = List.objects.create()
    Item.objects.create(text=request.POST["item_text"], list_attr=list_)
    return redirect("/lists/the-only-list-in-the-world/")


if __name__ == "__main__":
    pass
