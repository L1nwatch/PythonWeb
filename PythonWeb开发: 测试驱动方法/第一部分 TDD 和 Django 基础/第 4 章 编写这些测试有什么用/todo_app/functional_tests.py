#!/bin/env python3
# -*- coding: utf-8 -*-
# version: Python3.X
"""
进行功能测试的文件
"""
import unittest
from selenium import webdriver
from selenium.webdriver.common.keys import Keys

__author__ = '__L1n__w@tch'


class NewVisitorTest(unittest.TestCase):
    def setUp(self):
        """
        setUp 是特殊的方法, 在各个测试方法之前运行。
        使用这个方法打开浏览器。
        :return:
        """
        self.browser = webdriver.Firefox()
        self.browser.implicitly_wait(3)  # 等待 3 秒钟

    def tearDown(self):
        """
        tearDown 是特殊的方法, 在各个测试方法之后运行。使用这个方法关闭浏览器.
        注意, 这个方法有点类似 try/except 语句, 就算测试中出错了, 也会运行 tearDown 方法(如果 setUp 出错了就不会执行这个方法).
        所以测试结束后, Firefox 窗口不会一直停留在桌面上了.
        :return:
        """
        # 她很满意, 去睡觉了
        self.browser.quit()

    def test_can_start_a_list_and_retrieve_it_later(self):
        """
        测试的主要代码写在名为 test_can_start_a_list_and_retrieve_it_later 的方法中。
        名字以 test_ 开头的方法都是测试方法, 由测试运行程序运行.
        类中可以定义多个测试方法. 为测试方法起个有意义的名字是个好主意.
        :return:
        """
        # Y 访问在线待办事项应用的首页
        self.browser.get("http://localhost:8000")

        # Y 注意到网页的标题和头部都包含 "To-Do" 这个词
        """
        使用 self.assertIn 代替 assert 编写测试断言。
        unittest 提供了很多这种用于编写测试断言的辅助函数,如 assertEqual、assertTrue 和 assertFalse 等。
        更多断言辅助函数参见 unittest 的文档,地址是 http://docs.python.org/3/library/unittest.html。
        """
        self.assertIn("To-Do", self.browser.title)
        header_text = self.browser.find_element_by_tag_name("h1").text
        self.assertIn("To-Do", header_text)

        # 应用邀请 Y 输入一个待办事项
        input_box = self.browser.find_element_by_id("id_new_item")
        self.assertEqual(
            input_box.get_attribute("placeholder"),
            "Enter a to-do item"
        )

        # Y 在一个文本框中输入了 Buy pen
        # Y 的爱好是读书
        input_box.send_keys("Buy pen")

        # Y 按下回车键后, 页面更新了
        # 待办事项表格中显示了 "1: Buy pen"
        input_box.send_keys(Keys.ENTER)

        table = self.browser.find_element_by_id("id_list_table")
        rows = table.find_elements_by_tag_name("tr")
        self.assertTrue(
            any(row.text == "1: Buy pen" for row in rows)
        )

        # 页面中又显示了一个文本框, 可以输入其他的待办事项
        # Y 输入了 Use pen to take notes
        # Y 做事很有条理
        self.fail("Finish the test!")  # 不管怎样, self.fail 都会失败, 生成指定的错误消息。我使用这个方法提醒测试结束了。

        # 页面再次更新, 她的清单中显示了这两个待办事项

        # Y 想知道这个网站是否会记住她的清单

        # 她看到网站为她生成了一个唯一的 URL
        # 而且页面中有一些文字解说这个功能

        # 她访问那个 URL, 发现她的待办事项列表还在
        pass


if __name__ == "__main__":
    # 调用 unittest.main() 启动 unittest 的测试运行程序, 这个程序会在文件中自动查找测试类和方法, 然后运行。
    # warnings='ignore' 的作用是禁止抛出 ResourceWarning 异常。
    unittest.main()
