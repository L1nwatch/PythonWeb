#!/bin/env python3
# -*- coding: utf-8 -*-
# version: Python3.X
"""
进行功能测试的文件
"""
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from django.test import LiveServerTestCase

__author__ = '__L1n__w@tch'


class NewVisitorTest(LiveServerTestCase):
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

    def check_for_low_in_list_table(self, row_text):
        """
        测试给定字符串是否在表格中
        :param row_text: 需要判断的字符串
        :return: None
        """
        table = self.browser.find_element_by_id("id_list_table")
        rows = table.find_elements_by_tag_name("tr")
        # self.assertTrue(
        #     any(row.text == row_text for row in rows),
        #     "New to-do item did not appear in table -- its text was:\n{}".format(table.text)
        # )
        self.assertIn(row_text, [row.text for row in rows])  # 这句话与上面那句等价, 不过精简了很多

    def test_can_start_a_list_and_retrieve_it_later(self):
        """
        测试的主要代码写在名为 test_can_start_a_list_and_retrieve_it_later 的方法中。
        名字以 test_ 开头的方法都是测试方法, 由测试运行程序运行.
        类中可以定义多个测试方法. 为测试方法起个有意义的名字是个好主意.
        :return:
        """
        # Y 访问在线待办事项应用的首页
        # self.browser.get("http://localhost:8000") # 不用硬编码了
        self.browser.get(self.live_server_url)

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
        edith_list_url = self.browser.current_url
        # assertRegex 是 unittest 中的一个辅助函数，检查字符串是否和正则表达式匹配。我们使用这个方法检查是否实现了新的 REST 式设计。
        # 具体用法参阅 [unittest 的文档](https://docs.python.org/3/library/unittest.html)
        self.assertRegex(edith_list_url, "/lists/.+")  # TestCase 里的
        self.check_for_low_in_list_table("1: Buy pen")

        # 页面中又显示了一个文本框, 可以输入其他的待办事项
        # Y 输入了 Use pen to take notes
        # Y 做事很有条理
        input_box = self.browser.find_element_by_id("id_new_item")
        input_box.send_keys("Use pen to take notes")
        input_box.send_keys(Keys.ENTER)

        # 页面再次更新, 她的清单中显示了这两个待办事项
        self.check_for_low_in_list_table("1: Buy pen")
        self.check_for_low_in_list_table("2: Use pen to take notes")

        # 现在一个叫做 F 的新用户访问了网站
        ## 使用一个新浏览器会话
        ## 确保 Y 的信息不会从 cookie 中泄露出来
        self.browser.quit()
        self.browser = webdriver.Firefox()

        # F 访问首页
        # 页面中看不到 Y 的清单
        self.browser.get(self.live_server_url)
        page_text = self.browser.find_element_by_tag_name("body").text
        self.assertNotIn("Buy pen", page_text)
        self.assertNotIn("Use pen to take notes", page_text)

        # F 输入一个新待办事项，新建一个清单
        input_box = self.browser.find_element_by_id("id_new_item")
        input_box.send_keys("Buy milk")
        input_box.send_keys(Keys.ENTER)

        # F 获得了他唯一的 URL
        francis_list_url = self.browser.current_url
        self.assertRegex(francis_list_url, "/lists/.+")
        self.assertNotEqual(francis_list_url, edith_list_url)

        # 这个页面还是没有 U 的清单
        page_text = self.browser.find_element_by_tag_name("body").text
        self.assertNotIn("Buy pen", page_text)
        self.assertIn("Buy milk", page_text)

        # Y 想知道这个网站是否会记住她的清单

        # 她看到网站为她生成了一个唯一的 URL
        # 而且页面中有一些文字解说这个功能

        # 她访问那个 URL, 发现她的待办事项列表还在
        self.fail("Finish the test!")  # 不管怎样, self.fail 都会失败, 生成指定的错误消息。我使用这个方法提醒测试结束了。


if __name__ == "__main__":
    # 调用 unittest.main() 启动 unittest 的测试运行程序, 这个程序会在文件中自动查找测试类和方法, 然后运行。
    # warnings='ignore' 的作用是禁止抛出 ResourceWarning 异常。
    # unittest.main() # 之后都使用 Django 的测试运行程序运行功能测试
    pass
