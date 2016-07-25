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
from lists.models import Item

__author__ = '__L1n__w@tch'


class ListViewTest(TestCase):
    def test_displays_all_list_items(self):
        """
        测试页面是否能把所有待办事项都显示出来
        :return:
        """
        Item.objects.create(text="itemey 1")
        Item.objects.create(text="itemey 2")

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

class ItemModelTest(TestCase):
    def test_saving_and_retrieving_items(self):
        first_item = Item()
        first_item.text = "The first (ever) list item"
        first_item.save()

        second_item = Item()
        second_item.text = "Item the second"
        second_item.save()

        saved_items = Item.objects.all()
        self.assertEqual(saved_items.count(), 2)

        first_saved_item = saved_items[0]
        second_saved_item = saved_items[1]
        self.assertEqual(first_saved_item.text, "The first (ever) list item")
        self.assertEqual(second_saved_item.text, "Item the second")


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

    def test_home_page_can_save_a_POST_request(self):
        """
        测试主页能够保存 POST 请求, 并且主页能够把用户提交的待办事项保存到表格中
        :return:
        """
        request = HttpRequest()
        request.method = "POST"
        request.POST["item_text"] = "A new list item"

        response = home_page(request)

        # 检查是否把一个新 Item 对象存入数据库。objects.count() 是 objects.all().count() 的简写形式。
        self.assertEqual(Item.objects.count(), 1)
        new_item = Item.objects.first()  # objects.first() 等价于 objects.all()[0]
        self.assertEqual(new_item.text, "A new list item")  # 检查待办事项的文本是否正确

    def test_home_page_redirects_after_POST(self):
        """
        测试首页在发送 POST 请求后会重定向
        :return:
        """
        request = HttpRequest()
        request.method = "POST"
        request.POST["item_text"] = "A new list item"

        response = home_page(request)

        """ 不需要再拿响应中的 .content 属性值和渲染模板得到的结果比较
        self.assertIn("A new list item", response.content.decode("utf8"))
        expected_html = render_to_string(
            "home.html",
            {"new_item_text": "A new list item"},
            request=request
        )
        self.assertEqual(response.content.decode("utf8"), expected_html)
        """
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["location"], "/lists/the-only-list-in-the-world")

    def test_home_page_only_saves_items_when_necessary(self):
        """
        测试是否每次加载首页都会加入一个新的空项
        :return:
        """
        request = HttpRequest()
        home_page(request)
        self.assertEqual(Item.objects.count(), 0)

    '''首页不再需要显示清单了
    def test_home_page_displays_all_list_items(self):
        """
        测试首页是否能把所有待办事项都显示出来
        :return:
        """
        Item.objects.create(text="itemey 1")
        Item.objects.create(text="itemey 2")

        request = HttpRequest()
        response = home_page(request)
        response_content = response.content.decode()

        self.assertIn("itemey 1", response_content)
        self.assertIn("itemey 2", response_content)
    '''
