#!/bin/env python3
# -*- coding: utf-8 -*-
# version: Python3.X
"""
对首页视图进行单元测试
"""
from django.core.urlresolvers import resolve
from django.test import TestCase
from django.http import HttpRequest

from lists.views import home_page  # 这是接下来要定义的视图函数，其作用是返回所需的 HTML。要把这个函数保存在文件 lists/views.py

__author__ = '__L1n__w@tch'


class HomePageTest(TestCase):
    def test_root_url_resolves_to_home_page_view(self):
        found = resolve("/")  # resolve 是 Django 内部使用的函数，用于解析 URL，并将其映射到对应的视图函数上。
        self.assertEqual(found.func, home_page)  # 检查解析网站根路径"/"时，是否能找到名为 home_page 的函数

    def test_home_page_returns_correct_html(self):
        request = HttpRequest()  # 创建了一个 HttpRequest 对象，用户在浏览器中请求网页时，Django 看到的就是 HttpRequest 对象。

        response = home_page(request)  # 把这个 HttpRequest 对象传给 home_page 视图，得到响应。

        # 判定响应的 .content 属性(即发送给用户的 HTML)中有特定的内容，希望响应以<html> 标签开头。
        # 注意，response.content 是原始字节，不是 Python 字符串。更多信息参见 Django 文档中"移植到 Python 3"部分，
        # [地址](https://docs.djangoproject.com/en/1.7/topics/python3/)
        self.assertTrue(response.content.startswith(b"<html>"))

        # 希望响应中有一个 <title> 标签，其内容包含单词 "To-Do"——因为在功能测试中做了这项测试
        self.assertIn(b"<title>To-Do lists</title>", response.content)

        # 希望响应在结尾处关闭 <html> 标签。
        self.assertTrue(response.content.endswith(b"</html>"))
