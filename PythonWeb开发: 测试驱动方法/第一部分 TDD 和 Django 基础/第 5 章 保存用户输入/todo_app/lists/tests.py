#!/bin/env python3
# -*- coding: utf-8 -*-
# version: Python3.X
"""
对首页视图进行单元测试
"""
from django.core.urlresolvers import resolve
from django.test import TestCase
from django.http import HttpRequest
from django.template.loader import render_to_string
from lists.views import home_page  # 这是接下来要定义的视图函数，其作用是返回所需的 HTML。要把这个函数保存在文件 lists/views.py

__author__ = '__L1n__w@tch'


class HomePageTest(TestCase):
    def test_root_url_resolves_to_home_page_view(self):
        found = resolve("/")  # resolve 是 Django 内部使用的函数，用于解析 URL，并将其映射到对应的视图函数上。
        self.assertEqual(found.func, home_page)  # 检查解析网站根路径"/"时，是否能找到名为 home_page 的函数

    def test_home_page_returns_correct_html(self):
        request = HttpRequest()  # 创建了一个 HttpRequest 对象，用户在浏览器中请求网页时，Django 看到的就是 HttpRequest 对象。

        response = home_page(request)  # 把这个 HttpRequest 对象传给 home_page 视图，得到响应。

        excepted_html = render_to_string("home.html", request=request)
        self.assertEqual(response.content.decode("utf8"), excepted_html)

    def test_home_page_can_save_a_POST_request(self):
        request = HttpRequest()
        request.method = "POST"
        request.POST["item_text"] = "A new list item"

        response = home_page(request)
        self.assertIn("A new list item", response.content.decode("utf8"))
        expected_html = render_to_string(
            "home.html",
            {"new_item_text": "A new list item"},
            request=request
        )
        self.assertEqual(response.content.decode("utf8"), expected_html)
