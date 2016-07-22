#!/bin/env python3
# -*- coding: utf-8 -*-
# version: Python3.X
"""
对首页视图进行单元测试
"""
from django.core.urlresolvers import resolve
from django.test import TestCase
from lists.views import home_page  # 这是接下来要定义的视图函数，其作用是返回所需的 HTML。要把这个函数保存在文件 lists/views.py

__author__ = '__L1n__w@tch'


class HomePageTest(TestCase):
    def test_root_url_resolves_to_home_page_view(self):
        found = resolve("/")  # resolve 是 Django 内部使用的函数，用于解析 URL，并将其映射到对应的视图函数上。
        self.assertEqual(found.func, home_page)  # 检查解析网站根路径"/"时，是否能找到名为 home_page 的函数
