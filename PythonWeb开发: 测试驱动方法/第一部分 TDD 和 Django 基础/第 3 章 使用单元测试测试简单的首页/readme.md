## 第 3 章 使用单元测试测试简单的首页

### 3.1 第一个 Django 应用，第一个单元测试

Django 鼓励以”应用“的形式组织代码，一个项目中可以放多个应用，而且可以使用其他人开发的第三方应用，也可以重用自己在其他项目中开发的应用。

为待办事项清单创建一个应用`python3 manage.py startapp lists`

这个命令会在 superlists 文件夹中创建子文件夹 lists，与 superlists 子文件夹相邻，并在 lists 中创建一些占位文件，用来保存模型、视图以及目前最关注的测试：

> superlists/
>
> > db.sqlite3
> >
> > functional_tests.py
> >
> > lists
> >
> > > admin.py
> > >
> > > \_\_init\_\_.py
> > >
> > > migrations
> > >
> > > > \_\_init\_\_.py
> > >
> > > models.py
> > >
> > > tests.py
> > >
> > > views.py
> >
> > manage.py
> >
> > superlists
> >
> > > \_\_init\_\_.py
> > >
> > > \_\_pycache\_\_
> > >
> > > settings.py
> > >
> > > urls.py
> > >
> > > wsgi.py

### 3.2 单元测试及其与功能测试的区别

单元测试和功能测试之间有个基本区别：功能测试站在用户的角度从外部测试应用，单元测试则站在程序员的角度从内部测试应用。

作者遵从的 TDD 方法同时使用这两种类型测试应用。采用的工作流程大致如下：

1. 先写功能测试，从用户的角度描述应用的新功能。
2. 功能测试失败后，想办法编写代码让它通过。此时，使用一个或多个单元测试定义希望代码实现的效果，保证为应用中的每一行代码（至少）编写一个单元测试。
3. 单元测试失败后，编写最小量的应用代码，刚好让单元测试通过。 不断循环第 2 步和第 3 步，直到功能测试有一点进展为止。
4. 然后，再次运行功能测试，看能否通过，或者有没有进展。这一步可能促使我们编写一些新的单元测试和代码等。

功能测试站在高层驱动开发，而单元测试则从底层驱动。

> 功能测试的作用是帮助你开发具有所需功能的应用，还能保证你不会无意中破话这些功能。单元测试的作用是帮助你编写简洁无错的代码。

### 3.3 Django 中的单元测试

为首页视图编写单元测试，打开新生成的文件 lists/tests.py，可以看到

```Python
from django.test import TestCase

# Create your tests here.
```

Django 建议我们使用 TestCase 的一个特殊版本。这个版本由 Django 提供，是标准版 unittest.TestCase 的增强版，添加了一些 Django 专用的功能。

先故意编写一个失败的测试：

```Python
from django.test import TestCase

__author__ = '__L1n__w@tch'


class SmokeTest(TestCase):
    def test_bad_maths(self):
        self.assertEqual(1 + 1, 3)
```

现在，启动 Django 测试运行程序，命令`python3 manage.py test`

能运行单元测试，则可以提交了：

```shell
git status # 会显示一个消息，说没跟踪 lists/
git add lists
git diff --staged # 会显示将要提交的内容差异
git commit -m "Add app for lists, with deliberately failing unit test"
```

-m 标志的作用是让你在命令行中编写提交消息，这样就不需要使用编辑器了。

### 3.4 Django 中的 MVC、URL 和视图函数

Django 遵守了经典的 ”模型-视图-控制器“（Model-View-Controller，MVC）模式，但并没严格遵守。Django 确实有模型，但视图更像是控制器，模板其实才是视图。不过，MVC 的思想还在。可以看下 [Django 常见问题解答中的详细说明](https://docs.djangoproject.com/en/1.7/faq/general/)。

Django 和任何一种 Web 服务器一样，其主要任务是决定用户访问网站中的某个 URL 时做些什么。Django 的工作流程有点类似下述过程：

1. 针对某个 URL 的 HTTP 请求进入
2. Django 使用一些规则决定由哪个视图函数处理这个请求（这一步叫做解析 URL）
3. 选中的视图函数处理请求，然后返回 HTTP 响应。

因此要测试两件事：

* 能否解析网站根路径（”/"）的 URL，将其对应到我们编写的某个视图函数上
* 能否让视图函数返回一些 HTML，让功能测试通过？

先编写第一个测试，打开 lists/tests.py，更改代码：

```python
from django.core.urlresolvers import resolve
from django.test import TestCase
from lists.views import home_page  # 这是接下来要定义的视图函数，其作用是返回所需的 HTML。要把这个函数保存在文件 lists/views.py

__author__ = '__L1n__w@tch'


class HomePageTest(TestCase):
    def test_root_url_resolves_to_home_page_view(self):
        found = resolve("/")  # resolve 是 Django 内部使用的函数，用于解析 URL，并将其映射到对应的视图函数上。
        self.assertEqual(found.func, home_page)  # 检查解析网站根路径"/"时，是否能找到名为 home_page 的函数
```

运行测试`python3 manage.py test`，结果出现了 ImportError 错误，我们视图导入还未定义的函数。

### 3.5 终于可以编写一些应用代码了

在学习和起步阶段，一次只能修改（或添加）一行代码。每一次修改的代码要尽量少，让失败的测试通过即可。

在 lists/views.py 中写入下面的代码：

```python
from django.shortcus import render

# 在这儿编写视图
home_page = None
```

再次运行测试`python3 manage.py test`会报另一个 Resolver404 错误。

> 阅读调用跟踪
>
> 在 TDD 中经常需要阅读调用跟踪，找出解决问题的线索。

### 3.6 urls.py

Django 在 urls.py 文件中定义如何把 URL 映射到视图函数上。在文件夹 superlists/superlists 中有个主 urls.py 文件，这个文件应用于整个网站。看下默认的内容：

```Python
from django.conf.urls import patterns, include, url
from django.contrib import admin

urlpatterns = patterns("",
                       # Examples:
                       # url(r"^$","superlists.views.home",name="home")),
                       # url(r"^blog/",include("blog.urls")),
                       url(r"^admin/", include(admin.site.urls)),
                       )
```

这个文件中也有很多 Django 生成的辅助注释和默认建议。

url 条目的前半部分是正则表达式，定义适用于哪些 URL。后半部分说明把请求发往何处：使用点号表示的函数，例如 superlists.views.home，或者使用 include 引入的另一个 urls.py 文件。

可以看到，默认情况下有一个用于后台的条目。

urlpatterns 中第一个条目使用的正则表达式是 ^&，表示空字符串。这和网站的根路径，即我们要测试的“/”一样。

可以试着在这个文件里添加这么一句话：

```Python
from django.conf.urls import url
from django.contrib import admin

urlpatterns = [
    url(r"^$", "todo_app.views.home", name="home")
]
```

接着执行测试`python manage.py test`，可以发现不再显示 404 错误了。现在 Django 抱怨点号形式的 todo_app.views.home 指向的视图不存在。

修正这个问题，让它指向占位用的 home_page 对象。这个对象不在 superlists 中，而在 lists 中。

```python
from django.conf.urls import url

__author__ = '__L1n__w@tch'

urlpatterns = [
    # url(r'^admin/', admin.site.urls),
    url(r"^$", "lists.views.home_page", name="home")
]
```

然后再次运行测试，可以发现单元测试把地址 "/" 和文件 lists/views.py 中的 home_page = None 连接起来了，现在测试抱怨 home_page 无法调用，即不是函数。调整一下，把 home_page 从 None 变成真正的函数。

回到文件 lists/views.py，把内容改成：

```python
def home_page():
    pass
```

测试通过了。提交：

```shell
git diff # 会显示 urls.py、tests.py 和 views.py 中的变动
git commit -am "First unit test and url mapping, dummy view"
```

把 a 和 m 标志放在一起使用，意思是添加所有已跟踪文件中的改动，而且使用命令行中输入的提交信息。

> git commit -am 是最快捷的方式，但关于提交内容的反馈信息最少，所以在此之前要先执行 git status 和 git diff

### 3.7 为视图编写单元测试

该为视图编写测试了。我们要定义一个函数，向浏览器返回真正的 HTML 响应。打开 lists/tests.py，添加一个新测试方法。

```python
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
```

运行单元测试，看看进展如何。

#### “单元测试/编写代码”循环

现在可以开始适应 TDD 中的“单元测试/编写代码”循环了：

1. 在终端里运行单元测试，看它们是如何失败的
2. 在编辑器中改动最少量的代码，让当前失败的测试通过
3. 不断重复

想保证编写的代码无误，每次改动的幅度就要尽量小。这样才能确保每一部分代码都有对应的测试监护。

* 小幅代码改动：

  ```python
  def home_page(request):
      pass
  ```

* 运行测试

* 测试出错，使用 django.http.HttpResponse：

  ```python
  def home_page(request):
      return HttpResponse()
  ```

* 再次运行测试

* 测试出错，AssertionError。

* 再次编写代码：

  ```python
  def home_page(request):
      return HttpResponse("<html><title>To-Do lists</title></html>")
  ```

* 进行测试`python manage.py test`发现测试通过了。接下来要运行功能测试。

* `python functional_tests.py`，功能测试失败了（卡在了自己的一个提醒那里），现在要做一次提交了：

  ```shell
  git diff # 会显示 tests.py 中的新测试方法，以及 views.py 中的视图
  git commit -am "Basic view now returns minimal HTML"
  git log --online
  ```

  `git log`命令回顾了我们取得的进展。

本章介绍了以下知识：

* 新建 Django 应用
* Django 的单元测试运行程序
* 功能测试和单元测试之间的区别
* Django 解析 URL 的方法，urls.py 文件的作用
* Django 的视图函数，请求和响应对象
* 如何返回简单的 HTML

> 有用的命令和概念
>
> * 启动 Django 的开发服务器
>
>   python manage.py runserver
>
> * 运行功能测试
>
>   python functional_tests.py
>
> * 运行单元测试
>
>   python manage.py test
>
> * "单元测试/编写代码" 循环
>
>   1. 在终端里运行单元测试
>   2. 在编辑器中改动最少量的代码
>   3. 重复上两步
