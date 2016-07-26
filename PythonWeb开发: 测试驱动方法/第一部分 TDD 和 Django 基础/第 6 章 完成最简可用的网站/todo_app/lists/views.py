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


def view_list(request, list_id):
    list_ = List.objects.get(id=list_id)
    return render(request, "list.html", {"list_attr": list_})


def new_list(request):
    list_ = List.objects.create()
    Item.objects.create(text=request.POST["item_text"], list_attr=list_)
    return redirect("/lists/{unique_url}/".format(unique_url=list_.id))


def add_item(request, list_id):
    list_ = List.objects.get(id=list_id)
    Item.objects.create(text=request.POST["item_text"], list_attr=list_)
    return redirect("/lists/{unique_url}/".format(unique_url=list_id))


if __name__ == "__main__":
    pass
