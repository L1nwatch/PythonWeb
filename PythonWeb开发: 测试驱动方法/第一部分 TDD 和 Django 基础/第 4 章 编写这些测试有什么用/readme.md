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

### 遵守“不测试常量”规则，使用模板解决这个问题

看一下 lists/tests.py 中的单元测试。现在，要查找特定的 HTML 字符串，但这不是测试 HTML 的高效方法。一般来说，**单元测试的规则之一是“不测试常量”**。以文本形式测试 HTML 很大程度上就是测试常量。

换句话说，如果有如下的代码：

```python
wibble = 3
```

在测试中就不太有必要这么写：

```python
from my_program import wibble
assert wibble == 3
```

单元测试要测试的其实是逻辑、流程控制和配置。编写断言检测 HTML 字符串中是否有指定的字符序列，不是单元测试应该做的。

而且，在 Python 代码中插入原始字符串真的不是处理 HTML 的正确方式。我们有更好的方法，那就是使用模板。如果把 HTML 放在一个扩展名为 .html 的文件中，有很多好处，比如句法高亮支持等。Python 领域有很多模板框架，Django 有自己的模板系统，而且很好用。

### 使用模板重构

现在要做的是让视图函数返回完全一样的 HTML，但使用不同的处理方式。这个过程叫做重构，即在功能不变的前提下改进代码。

重构可参考 Martin Fowler 写的[《重构》](http://refactoring.com/)

重构的首要原则是不能没有测试，我们正在做测试驱动开发，测试已经有了。测试能通过才能保证重构前后的表现一致： ``python manage.py test``

测试通过后，先把 HTML 字符串提取出来写入单独的文件。新建用于保存模板的文件夹 lists/templates，然后新建文件 lists/templates/home.html，再把 HTML 写入这个文件。

```html
<html>
  <title>To-Do lists</title>
</html>
```

有些人喜欢使用和应用同名的子文件夹（即 lists/templates/lists），然后使用 lists/home.html 引用这个模板，这叫做“模板命名空间”。对于小型项目来说使用模板命名空间太复杂了，不过在大型项目中可能有用武之地，参见 [Django 教程](https://docs.djangoproject.com/en/1.7/intro/tutorial03/#write- views-that-actually-do-something)

接下来修改视图函数：

```python
from django.shortcuts import render

def home_page(request):
    return render(request, "home.html")
```

现在不自己构建 HttpResponse 对象了，转而使用 Django 中的 render 函数。这个函数的第一个参数是请求对象的，第二个参数是渲染的模板名。Django 会自动在所有的应用目录中搜索名为 templates 的文件夹，然后根据模板中的内容构建一个 HttpResponse 对象。

> 模板是 Django 中一个很强大的功能，使用模板的主要优势之一是能把 Python 变量代入 HTML 文本。这就是为什么使用 render 和 render_to_string，而不用原生的 open 函数手动从硬盘中读取模板文件的缘故。

看一下模板是否起作用了 ``python manage.py test``

发现错误，测试无法找到模板，分析调用跟踪可知是调用 render 函数那段出错了。Django 找不到模板，是因为还没有正式在 Django 中注册 lists 应用。执行 startapp 命令以及在项目文件夹中存放一个应用还不够，你要告诉 Django 确实要开发一个应用，并把这个应用添加到文件 settings.py 中。这么做才能保证万无一失。打开 settings.py，找到变量 INSTALLED_APPS，把 lists 加进去：

```python
# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    "lists"
]
```

可以看出，默认已经有很多应用了。只需把 lists 加到列表的末尾。现在可以再运行测试看看 ``python manage.py test``

> 作者在 ``self.aseertTrue(response.content.endswith(b"</html>"))``出错了，原因是创建 HTML 文件时编辑器自动给末尾加了一个换行

自己的测试是通过的，所以对代码的重构结束了，测试也证实了重构前后的表现一致。现在可以修改测试，不再测试常量，检查是否渲染了正确的模板。Django 中的另一个辅助函数 ``render_to_string`` 可以给些帮助，在 lists/tests.py 文件中进行相应修改：

```python
from django.template.loader import render_to_string

def test_home_page_returns_correct_html(self):
    request = HttpRequest()
    response = home_page(request)
    expected_html = render_to_string("home.html")
    self.assertEqual(response.content.decode(), expected_html)
```

使用 .decode() 把 response.content 中的字节转换成 Python 中的 Unicode 字符串，这样就可以对比字符串，而不用像之前那样对比字节。

> Django 提供了一个测试客户端，其中有用于测试模板的工具。

### 4.4 关于重构

> 重构时，修改代码或者测试，但不能同时修改。

重构后最好做一次提交：

```shell
git status # 会看到 tests.py, views.py, settings.py, 以及新建的 templates 文件夹
git add . # 还会添加尚未跟踪的 templates 文件夹
git diff --staged # 审查我们想提交的内容
git commit -m "Refactor home page view to use a template"
```

### 4.5 接着修改首页

现在功能测试还是失败的。修改代码，让它通过。因为 HTML 现在保存在模板中，可以尽情修改，无需编写额外的单元测试。我们需要一个 ``<h1>`` 元素：

```html
<html>
  <head>
    <title>To-Do lists</title>
  </head>
  <body>
    <h1>
      Your To-Do list
    </h1>
    <input id="id_new_item" placeholder="Enter a to-do item"/>
  </body>
</html>
```

``placeholder`` 为占位文字

得到了错误，找到表格，因此要在页面中加入表格。目前表格是空的：

```html
<input id="id_new_item" placeholder="Enter a to-do item" />
<table id="id_list_table">
  
</table>
```

功能测试的结果依旧是错误，准确地说是 assertTrue，因为没有给它提供明确的失败消息。可以把自定义的错误消息传给 unittest 中的大多数 assertX 方法：

```python
self.assertTrue(
	any(row.text == "1: Buy pen" for row in rows),
    "New to-do item did not appear in table"
)
```

再次运行功能测试，应该会看到我们编写的消息。

现在做个提交吧：

```shell
git diff
git commit -am "Front page HTML now generated from a template"
```

### 4.6 总结：TDD 流程

TDD 流程中涉及的主要概念：

* 功能测试
* 单元测试
* “单元测试/编写代码”循环
* 重构

TDD 的总体流程，参照下图

![TDD 的总体流程](https://github.com/L1nwatch/PythonWeb/blob/master/PythonWeb%E5%BC%80%E5%8F%91:%20%E6%B5%8B%E8%AF%95%E9%A9%B1%E5%8A%A8%E6%96%B9%E6%B3%95/%E7%AC%AC%E4%B8%80%E9%83%A8%E5%88%86%20TDD%20%E5%92%8C%20Django%20%E5%9F%BA%E7%A1%80/%E7%AC%AC%204%20%E7%AB%A0%20%E7%BC%96%E5%86%99%E8%BF%99%E4%BA%9B%E6%B5%8B%E8%AF%95%E6%9C%89%E4%BB%80%E4%B9%88%E7%94%A8/pic_4-3.png?raw=true) 

首先编写一个测试，运行这个测试看着它失败。最后编写最少量的代码取得一些进展，再运行测试。如果不断重复，直到测试通过为止。最后，或许还要重构代码，测试能确保不破坏任何功能。

包含功能测试和单元测试的 TDD 流程，如下图所示

![功能测试 + 单元测试的 TDD 流程](https://github.com/L1nwatch/PythonWeb/blob/master/PythonWeb%E5%BC%80%E5%8F%91:%20%E6%B5%8B%E8%AF%95%E9%A9%B1%E5%8A%A8%E6%96%B9%E6%B3%95/%E7%AC%AC%E4%B8%80%E9%83%A8%E5%88%86%20TDD%20%E5%92%8C%20Django%20%E5%9F%BA%E7%A1%80/%E7%AC%AC%204%20%E7%AB%A0%20%E7%BC%96%E5%86%99%E8%BF%99%E4%BA%9B%E6%B5%8B%E8%AF%95%E6%9C%89%E4%BB%80%E4%B9%88%E7%94%A8/pic_4-4.png?raw=true)

功能测试是应用是否能正常运行的最终判定。单元测试只是整个开发过程中的一个辅助工具。

这种看待事物的方式有时叫做“双循环测试驱动开发”。Emily Bache 写了一篇博客文章，从不同的视角讨论了这个话题，[参考链接](http:// coding-is-like-cooking.info/2013/04/outside-in-development-with-double-loop-tdd/)

> 使用 Git 检查进度
>
> 如果想进一步提升 Git 技能，可以添加作者的仓库，作为一个远程仓库：
>
> ``git remote add harry https://github.com/hjwp/book-example.git``
>
> ``git fetch harry``
>
> 然后可以按照下面的方式查看第 4 章结束时代码之间的差异：
>
> ``git diff harry/chapter_04``
>
> Git 能处理多个远程仓库，因此就算已经把自己的代码推送到 GitHub 或者 Bitbucket，也可以这么做。