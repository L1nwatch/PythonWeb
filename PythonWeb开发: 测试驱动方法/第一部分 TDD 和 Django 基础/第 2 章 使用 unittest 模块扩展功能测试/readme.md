## 第 2 章 使用 unittest 模块扩展功能测试

### 2.1 使用功能测试驱动开发一个最简可用的应用

使用 Selenium 实现的测试可以驱动真正的网页浏览器，让我们能从用户的角度查看应用是如何运作的。因此，这类测试叫做“功能测试”。

功能测试的作用是跟踪“用户故事”（User Story），模拟用户使用某个功能的过程，以及应用应该如何响应用户的操作。

> 功能测试 = 验收测试 = 端到端测试
>
> > 功能测试，有些人喜欢称之为验收测试（Acceptance Test）或者端到端测试（End-to-End Test）。这类测试最重要的作用是从外部观察整个应用是如何运作的。另一个术语是黑箱测试（Black Box Test），因为这种测试对所要测试的系统内部一无所知。

编写新功能测试时，可以先写注释，勾勒出用户故事的重点。这样写出的测试人类可读，甚至可以作为一种讨论应用需求和功能的方式分享给非程序员看。

TDD 常与敏捷软件开发方法结合在一起使用，经常提到的一个概念是“最简可用的应用”，即我们能开发出来的最简单的而且可以使用的应用。

最简可用的待办事项清单其实只要能让用户输入一些待办事项，并且用户下次访问应用时这些事项还在即可。

打开 functional_tests.py，编写一个类似下面的故事：

```Python
from selenium import webdriver

__author__ = '__L1n__w@tch'

if __name__ == "__main__":
    browser = webdriver.Firefox()

    # Y 访问在线待办事项应用的首页
    browser.get("http://localhost:8000")

    # Y 注意到网页的标题和头部都包含 "To-Do" 这个词
    assert "To-Do" in browser.title

    # 应用邀请 Y 输入一个待办事项

    # Y 在一个文本框中输入了 Buy pen
    # Y 的爱好是读书

    # Y 按下回车键后, 页面更新了
    # 待办事项表格中显示了 "1: Buy pen"

    # 页面中又显示了一个文本框, 可以输入其他的待办事项
    # Y 输入了 Use pen to take notes
    # Y 做事很有条理

    # 页面再次更新, 她的清单中显示了这两个待办事项

    # Y 想知道这个网站是否会记住她的清单

    # 她看到网站为她生成了一个唯一的 URL
    # 而且页面中有一些文字解说这个功能

    # 她访问那个 URL, 发现她的待办事项列表还在

    # 她很满意, 去睡觉了
   	browser.quit()

```

> 我们有个词来形容注释
>
> > 注释有其作用，可以添加上下文，说明代码的目的。简单重复代码意图的注释毫无意义，例如：
> >
> > > \# 把 wibble 的值增加1
> > >
> > > wibble += 1
> >
> > 我们要努力做到让代码可读，使用有意义的变量名和函数名，保持代码结构清晰，这样就不再需要通过注释说明代码做了什么，只要偶尔写一些注释说明为什么这么做。
> >
> > 有些情况下注释很重要。Django 在其生成的文件中用到了很多注释，这是解说 API 的一种方式。而且还在功能测试中使用注释描述用户故事——把测试提炼成一个连贯的故事，确保我们始终从用户的角度测试。
>
> 这个领域中还有许多有趣的知识，比如行为驱动开发（Behaviour Driven Development）和测试 DSL（Domain Specific Language，领域特定语言）。

除了在测试加入注释之外，还添加了 assert 这行代码，让其查找单词“To-Do”，这意味着我们现在期望测试失败。运行这个测试。

首先，启动服务器：

```shell
python3 manage.py runserver
```

然后在另一个 Shell 中运行测试，可以发现测试失败了。

### 2.2 Python 标准库中的 unittest 模块

首先，AssertionError 消息没什么用，如果测试能指出在浏览器的标题中到底找到了什么就好了。解决办法是利用 assert 关键字的第二个参数，写成：

```Python
assert "To-Do" in browser.title, "Browser title was " + browser.title
```

其次，Firefox 窗口一直停留在桌面上，Firefox 窗口可以在 try/finally 语句中关闭。但这种问题在测试中很常见，标准库中的 unittest 模块已经提供了现成的解决办法。

在 functional_tests.py 中写入如下代码：

```Python
import unittest
from selenium import webdriver

__author__ = '__L1n__w@tch'


class NewVisitorTest(unittest.TestCase):
    def setUp(self):
        """
        setUp 是特殊的方法, 在各个测试方法之前运行。
        使用这个方法打开浏览器。
        :return:
        """
        self.browser = webdriver.Firefox()

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
        self.fail("Finish the test!")  # 不管怎样, self.fail 都会失败, 生成指定的错误消息。我使用这个方法提醒测试结束了。

        # 应用邀请 Y 输入一个待办事项

        # Y 在一个文本框中输入了 Buy pen
        # Y 的爱好是读书

        # Y 按下回车键后, 页面更新了
        # 待办事项表格中显示了 "1: Buy pen"

        # 页面中又显示了一个文本框, 可以输入其他的待办事项
        # Y 输入了 Use pen to take notes
        # Y 做事很有条理

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

> 如果你阅读 Django 关于测试的文档，可能会看到有个名为 LiveServerTestCase 的类。目前来说，LiveServerTestCase 有点复杂，但后面的章节会用到。

来试一下这个测试：

```shell
python3 functional_tests.py
```

这几个测试清理了 Firefox 窗口，显示了一个排版精美的报告，指出运行了几个测试，其中有几个测试失败了，而且 assertIn 还显示了一个有利于调试的错误消息。

### 2.3 隐式等待

现阶段还有一件事要做——在 setUp 方法中加入 implicitly_wait：

```Python
def setUp(self):
    self.browser = webdriver.Firefox()
	self.browser.implicitly_wait(3)
```

这是 Selenium 测试中经常使用的方法。Selenium 在操作之前等待页面完全加载方面的表现尚可，但不够完美。implicitly_wait 的作用是告诉 Selenium，如果需要就等待几秒钟。加入上述代码后，当我们要在页面中查找内容时，Selenium 会等待三秒钟，让内容出现。

> 不要依赖 implicitly_wait，它并不适用所有情况。在简单的应用中可以使用 implicitly_wait，但当应用超过某种复杂度后，需要在测试中编写更复杂的显示等待规则。

### 2.4 提交

现在是提交代码的好时机，因为已经做了一次完整的修改。我们扩展了功能测试，加入注释说明我们要在最简可用的待办事项清单应用中执行哪些操作。还使用 Python 中的 unittest 模块及其提供的各种测试辅助函数重写了测试。

执行`git status`命令，会发现只有 functional_tests.py 文件的内容变化了。然后执行`git diff`命令，查看上一次提交和当前硬盘中保存内容之间的差异。

现在执行下述命令：

```shell
git commit -a
```

-a 的意思是：自动添加已跟踪文件（即已经提交的各文件）中的改动。上述命令不会添加全新的文件（需要自己使用`git add`命令手动添加这些文件）。

弹出编辑器后，写入一个描述性的提交消息，比如“使用注释编写规格的首个功能测试，而且使用了 unittest”

