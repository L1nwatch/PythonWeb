## 第 4 章 编写这些测试有什么用
### 4.1 编程就像从井里打水 

Kent Beck（TDD 里面基本上就是他发明的）。TDD 里面好比是一个棘轮，使用它你可以保存当前的进度，休息一会儿，而且能保证进度绝不倒退。这样你就没必要一直那么聪明了。

> **细化测试每个函数的好处**
>
> 作者赞成为简单的函数编写细化的简单测试。
>
> 首先，既然测试那么简单，写起来就不会花很长时间。
>
> 其次，占位测试很重要。先为简单的函数写好测试，当函数变复杂后，这道心理障碍就容易迈过去。你可能会在函数中添加一个 if 语句，几周后再添加一个 for 循环，不知不觉间就将其变成一个基于元类（meta-class）的多态树状结构解析器了。因为从一开始你就编写了测试，每次修改都会自然而然地添加新测试，最终得到的是一个测试良好的函数。相反，如果你试图判断函数什么时候才复杂到需要编写测试的话，那就太主观了，而且情况会变得更糟糕。因为没有占位测试，此时开始编写测试需要投入很多精力。
>
> 不要试图找一些不靠谱的主观规则。

### 4.2 使用 Selenium 测试用户交互 

重新运行测试找一下之前进展到哪里了 ``python functional_tests.py``

> TDD 的优点之一就是，永远不会忘记接下来该做什么——重新运行测试就知道要做的事了。

失败消息说“Finish the test”（结束这个测试），所以接着就是扩充其中的功能测试了：

```python
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
```

我们使用了 Selenium 提供的几个用来查找网页内容的方法：``find_element_by_tag_name``，``find_element_by_id`` 和 ``find_elements_by_tag_name``（注意有个 s，也就是说这个方法会返回多个元素）。还使用了 send_keys，这是 Selenium 在输入框输入内容的方法。还会看到使用了 Keys 类，它的作用是发送回车键等特殊的按键，还有 Ctrl 等修改键。

> 小心 Selenium 中 find_element_by... 和 find_elements_by... 这两类函数的区别。前者返回一个元素，如果找不到就抛出异常；后者返回一个列表，这个列表可能为空。

留意一下 any 函数，它是 Python 中的原生函数。any 函数的参数是个生成器表达式，类似于列表推到，但比它更出色。这个概念可以参考 [Guido 的精彩解释](http://python-history.blogspot.co.uk/2010/06/ from-list-comprehensions-to-generator.html)

看一下测试进展如何 ``python functional_tests.py``

测试报错在页面找不到 `<h1>` 元素。

大幅修改功能测试后往往有必要提交一次，如下：

```shell
git diff # 会显示对 functional_tests.py 的改动
git commit -am "Functional test now checks we can input a to-do item"
```



