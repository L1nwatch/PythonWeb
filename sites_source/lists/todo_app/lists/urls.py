#!/bin/env python3
# -*- coding: utf-8 -*-
# version: Python3.X
""" Description
"""
from django.conf.urls import patterns, url

__author__ = '__L1n__w@tch'

urlpatterns = patterns("",
                       url(r"^(\d+)/$", "lists.views.view_list", name="view_list"),
                       url(r"^(\d+)/add_item$", "lists.views.add_item", name="add_item"),
                       url(r"^new$", "lists.views.new_list", name="new_list")
                       )

if __name__ == "__main__":
    pass
