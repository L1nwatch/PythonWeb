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
from lists.models import Item, List

__author__ = '__L1n__w@tch'


class ListViewTest(TestCase):
    def test_displays_all_list_items(self):
        """
        测试页面是否能把所有待办事项都显示出来
        :return:
        """
        list_ = List.objects.create()
        Item.objects.create(text="itemey 1", list_attr=list_)
        Item.objects.create(text="itemey 2", list_attr=list_)

        response = self.client.get("/lists/the-only-list-in-the-world/")  # 现在不直接调用视图函数了

        # 现在不必再使用 assertIn 和 response.content.decode() 了
        # Django 提供 assertContains 方法，它知道如何处理响应以及响应内容中的字节
        self.assertContains(response, "itemey 1")
        self.assertContains(response, "itemey 2")

    def test_uses_list_template(self):
        """
        测试是否使用了不同的模板
        :return:
        """
        response = self.client.get("/lists/the-only-list-in-the-world/")
        self.assertTemplateUsed(response, "list.html")


class ListAndItemModelTest(TestCase):
    def test_saving_and_retrieving_items(self):
        list_ = List()
        list_.save()

        first_item = Item()
        first_item.text = "The first (ever) list item"
        first_item.list_attr = list_
        first_item.save()

        second_item = Item()
        second_item.text = "Item the second"
        second_item.list_attr = list_
        second_item.save()

        saved_list = List.objects.first()
        self.assertEqual(saved_list, list_)

        saved_items = Item.objects.all()
        self.assertEqual(saved_items.count(), 2)

        first_saved_item = saved_items[0]
        second_saved_item = saved_items[1]
        self.assertEqual(first_saved_item.text, "The first (ever) list item")
        self.assertEqual(first_saved_item.list_attr, list_)
        self.assertEqual(second_saved_item.text, "Item the second")
        self.assertEqual(second_saved_item.list_attr, list_)


class NewListTest(TestCase):
    def test_saving_a_POST_request(self):
        """
        测试页面是否能够保存 POST 请求, 并且能够把用户提交的待办事项保存到表格中
        :return:
        """
        self.client.post("/lists/new", data={"item_text": "A new list item"})

        # 检查是否把一个新 Item 对象存入数据库。objects.count() 是 objects.all().count() 的简写形式。
        self.assertEqual(Item.objects.count(), 1, "希望数据库中现在有 1 条数据, 然而却有 {} 条数据".format(Item.objects.count()))
        new_item = Item.objects.first()  # objects.first() 等价于 objects.all()[0]
        self.assertEqual(new_item.text, "A new list item")  # 检查待办事项的文本是否正确

    def test_redirects_after_POST(self):
        """
        测试在发送 POST 请求后是否会重定向
        :return:
        """
        response = self.client.post("/lists/new", data={"item_text": "A new list item"})

        self.assertEqual(response.status_code, 302, "希望返回 302 代码, 然而却返回了 {}".format(response.status_code))
        self.assertEqual(response["location"], "/lists/the-only-list-in-the-world/")
        self.assertRedirects(response, "/lists/the-only-list-in-the-world/")  # 等价于上面两条


class HomePageTest(TestCase):
    def test_root_url_resolves_to_home_page_view(self):
        """
        测试访问根路径时是由 home_page 视图函数来负责相关处理的
        :return:
        """
        found = resolve("/")  # resolve 是 Django 内部使用的函数，用于解析 URL，并将其映射到对应的视图函数上。
        self.assertEqual(found.func, home_page)  # 检查解析网站根路径"/"时，是否能找到名为 home_page 的函数

    def test_home_page_returns_correct_html(self):
        """
        测试访问主页时得到的是一个正确的 html 文本
        :return:
        """
        request = HttpRequest()  # 创建了一个 HttpRequest 对象，用户在浏览器中请求网页时，Django 看到的就是 HttpRequest 对象。

        response = home_page(request)  # 把这个 HttpRequest 对象传给 home_page 视图，得到响应。

        excepted_html = render_to_string("home.html", request=request)
        self.assertEqual(response.content.decode("utf8"), excepted_html)
