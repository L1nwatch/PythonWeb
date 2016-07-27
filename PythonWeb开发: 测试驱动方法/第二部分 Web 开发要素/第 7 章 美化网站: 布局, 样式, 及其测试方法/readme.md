## 第 7 章 美化网站: 布局, 样式, 及其测试方法

本章介绍一些样式基础知识，包括如何集成 Bootstrap 这个 HTML/CSS 框架，还要学习 Django 处理静态文件的方式，以及如何测试静态文件。

### 7.1 如何在功能测试中测试布局和样式

> 执行命令 `manage.py runserver` 启动开发服务器时，可能会看到一个数据库错误：“table lists_item has no column named list_id"（lists_item 表中没有名为 list_id 的列）。此时，需要执行 `manage.py migrate` 命令，更新本地数据库，让 models.py 中的改动生效。

[Python 世界的选丑竞赛](http://grokcode.com/746/dear-python-why-are-you-so- ugly/)

接下来要实现如下效果：

* 一个精美且很大的输入框，用于新建清单，或者把待办事项添加到现有的清单中
* 把这个输入框放在一个更大的居中框体中，吸引用户的注意力

大多数人会说，不要测试外观。他们是对的，这就像是测量常量一样毫无意义。但可以测试装饰外观的方式，确信实现了预期的效果即可。例如，使用层叠样式表(Cascading Style Sheet，CSS）编写样式，样式表以静态文件的形式加载，而静态文件配置起来有点复杂（把静态文件移到主机上，配置起来更麻烦），因此只需做某种”冒烟测试“（smoke test），确保加载了 CSS 即可。无须测试字体、颜色以及像素级位置，而是通过简单的测试，确认重要的输入框在每个页面中都按照预期的方式对齐，由此推断页面中的其他样式或许也都正确应用了。

先在功能测试中编写一个新测试方法：

```python
class NewVisitorTest(LiveServerTestCase):
    [...]
    
    def test_layout_and_styling(self):
        # Y 访问首页
        self.browser.get(self.live_server_url)
        self.browser.set_window_size(1024, 768)
        
        # 她看到输入框完美地居中显示
        input_box = self.browser.find_element_by_id("id_new_item")
        self.assertAlmostEqual(
        	input_box.location["x"] + input_box.size["width"] / 2,
            512,
            delta = 5
        )
```

这里先把浏览器的窗口设为固定大小，然后找到输入框元素，获取它的大小和位置，再做些数学计算，检查输入框是否位于网页的中线上。assertAlmostEqual 的作用是帮助处理舍入误差，这里指定计算结果在正负五像素范围内可接受。

运行功能测试，会得到预料之中的失败。不过，这种功能测试很容易出错，所以要用一种快捷方法确认输入框居中时功能测试能通过。一旦确认功能测试编写正确之后，就把这些代码删掉，下面修改 `home.html` 文件：

```html
<form method="POST" action="/lists/new">
  <p style="text-align: center;">
    <input name="item_text" id="id_new_item" placeholder="Enter a to-do item" />
  </p>
  {% csrf_token %}
</form>
```

修改之后测试能通过，说明功能测试起作用了。下面扩展这个测试，确保新建清单后输入框仍然居中对齐显示：

```python
# 她新建了一个清单，看到输入框仍完美地居中显示
input_box.send_keys("testsing\n")
input_box = self.browser.find_elemeny_by_id("id_new_item")
self.assertAlmostEqual(
	input_box.location["x"] + inputbox.size["width"] / 2,
    512,
    delta = 5
)
```

这会导致测试再次失败。

#### 个人实践

发现自己没有测试失败，寻找原因，发现是运行了另外一个路径下的 `manage.py`。

还有一个，自己手动打开浏览器进行测试的时候发现居然没法正常使用（已经通过的功能测试），后来发现得重建数据库，命令如下：

```shell
# 第一步， 手动删除 db.sqlite3 文件
# 第二步，迁移
python manage.py makemigrations
# 第三步，建库
python manage.py migrate
```

OK，正常了。

现在只提交功能测试：

```shell
git add functional_tests/tests.py
git commit -m "first steps of FT for layout + styling"
git reset --hard # 退回添加 <p style=...> 之前的状态
```

### 7.2 使用 CSS 框架美化网站

使用 CSS 框架解决问题，框架有很多，不过出现最早且最受欢迎的是 Twitter 开发的 Bootstrap。就是用这个框架，[Bootstrap](http://getbootstrap.com/ )获取。

下载 Bootstrap，把它放在 lists 应用中一个新文件夹 static 里：

```shell
wget -O bootstrap.zip https://github.com/twbs/bootstrap/releases/download/\ v3.1.0/bootstrap-3.1.0-dist.zip
unzip bootstrap.zip
mkdir lists/static
mv dist lists/static/bootstrap # 改名为 bootstrap
rm bootstrap.zip
```

dist 文件夹中的内容是未经定制的原始 Bootstrap 框架，现在使用这些内容，但在真正的网站中不能这么做，因为用户能立即看出你使用 Bootstrap 时没有定制。你应该学习如何使用 LESS，至少把字体改了。Bootstrap 文档中有定制的详细说明，或者可以看这篇[指南](http://www. smashingmagazine.com/2013/03/12/customizing-bootstrap/)。

最终得到的 lists 文件夹结构如下：

```t
tree lists
lists
├── __init__.py
├── __pycache__
│   ├── __init__.cpython-34.pyc
│   ├── admin.cpython-34.pyc
│   ├── models.cpython-34.pyc
│   ├── tests.cpython-34.pyc
│   ├── urls.cpython-34.pyc
│   └── views.cpython-34.pyc
├── admin.py
├── apps.py
├── migrations
│   ├── 0001_initial.py
│   ├── __init__.py
│   └── __pycache__
│       ├── 0001_initial.cpython-34.pyc
│       └── __init__.cpython-34.pyc
├── models.py
├── static
│   └── bootstrap
│       ├── css
│       │   ├── bootstrap-theme.css
│       │   ├── bootstrap-theme.css.map
│       │   ├── bootstrap-theme.min.css
│       │   ├── bootstrap-theme.min.css.map
│       │   ├── bootstrap.css
│       │   ├── bootstrap.css.map
│       │   ├── bootstrap.min.css
│       │   └── bootstrap.min.css.map
│       ├── fonts
│       │   ├── glyphicons-halflings-regular.eot
│       │   ├── glyphicons-halflings-regular.svg
│       │   ├── glyphicons-halflings-regular.ttf
│       │   ├── glyphicons-halflings-regular.woff
│       │   └── glyphicons-halflings-regular.woff2
│       └── js
│           ├── bootstrap.js
│           ├── bootstrap.min.js
│           └── npm.js
├── templates
│   ├── home.html
│   └── list.html
├── tests.py
├── urls.py
└── views.py
```

在 Bootstrap 文档中的 ["Getting Started" 部分](http://twitter.github.io/bootstrap/getting-started. html#html-template)，可以发现 Bootstrap 要求 HTML 模板中包含如下代码：

```html
  <!DOCTYPE html>
     <html>
       <head>
         <title>Bootstrap 101 Template</title>
         <meta name="viewport" content="width=device-width, initial-scale=1.0">
         <!-- Bootstrap -->
         <link href="css/bootstrap.min.css" rel="stylesheet" media="screen">
       </head>
       <body>
         <h1>Hello, world!</h1>
         <script src="http://code.jquery.com/jquery.js"></script>
         <script src="js/bootstrap.min.js"></script>
       </body>
     </html>
```

我们已经有两个 HTML 模板了，所以不想在每个模板中都添加大量的样板代码。这似乎是运用”不要自我重复“原则的好时机，可以把通用代码放在一起。Django 使用的模板语言可以轻易做到这一点，这种功能叫做”模板继承“。

### 7.3 Django 模板继承

看一下 home.html 和 list.html 之间的差异，使用 diff 命令。

```shell
diff lists/templates/home.html lists/templates/list.html
```

这两个模板头部显示的文本不一样，而且表单的提交地址也不同。除此之外，list.html 还多了一个 `<table>` 元素。

现在弄清了两个模板之间共通以及有差异的地方，然后就可以让它们继承同一个父级模板了。先复制 `home.html`：

```shell
cp lists/templates/home.html lists/templates/base.html
```

把通用的样板代码写入这个基模板中，而且标记出各个”块“，块中的内容留给子模板定制：

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>To-Do lists</title>
</head>
<body>
<h1>{% block header_text %}{% endblock %}</h1>
<form method="POST" action="{% block form_action %}{% endblock %}">
    <input name="item_text" id="id_new_item" placeholder="Enter a to-do item"/>
    {% cstf_token %}
</form>
{% block_table %}
{% endblock %}
</body>
</html>
```

基模板定义了多个叫做”块“的区域，其他模板可以在这些地方插入自己所需的内容。在实际操作中看一下这种机制的用法。修改 `home.html`，让它继承 `base.html`：

```html
{% extends "base.html" %}
{% block header_text %}Start a new To-Do list{% endblock %}
{% block form_action %}/lists/new{% endblock %}
```

可以看出，很多 HTML 样板代码都不见了，现在只需集中精力编写想定制的部分。然后对 list.html 做同样的修改：

```html
{% extends "base.html" %}

{% block header_text %}Your To-Do list{% endblock %}

{% block form_action %}/lists/{{ list_attr.id }}/add_item{% endblock %}

{% block table %}
    <table id="id_list_table">
        {% for item in list_attr.item_set.all %}
            <tr><td>{{ forloop.counter }}: {{ item.text }}</td></tr>
        {% endfor %}
    </table>
{% endblock %}
```

对模板来说，这是一次重构。再次运行功能测试，确保没有破坏现有功能。

果然，结果和修改前一样。这次改动值得做一次提交：

```shell
git diff -b # -b 的意思是忽略空白
git status
git add lists/templates # 先不添加 static 文件夹
git commit -m "refactor templates to use a base template"
```

### 7.4 集成 Bootstrap

现在集成 Bootstrap 所需的样板代码更容易了，不过暂时不需要 JavaScript，只加入 CSS 即可。

```html
<!DOCTYPE html>
<html lang="en">
  <head>
    <title>To-Do lists</title>
    <meta name="viewport" content="width=device.width, initial-scale=1.0">
    <link href="css/bootstrap.min.css" rel="stylesheet" media="screen">
  </head>
</html>
```

#### 行和列

最后，使用 Bootstrap 中某些真正强大的功能。使用之前你得先阅读 Bootstrap 的文档。可以使用栅格系统和 text-center 类实现所需的效果。

```html
<body>
  <div class="container">
    <div class="row">
      <div class="cl-md-6 col-md-offset-3">
        <div class="text-center">
          <h1>{% block header_text %}{% endblock %}</h1>
          <form method="POST" action="{% block form_action %}{% endblock %}">
            <input name="item_text" id="id_new_item" placeholder="Enter a to-do item"/>
            {% csrf_token %}
          </form>   
        </div>
      </div>
    </div>
    
    <div class="row">
      <div class="col-md-6 col-md-offset-3">
        {% block table %}
        {% endblock %}
      </div>
    </div>
  </div>
</body>
```

> 如果你从未看过 [Bootstarp 文档](http://getbootstrap.com/)，花点时间浏览一下吧。文档中介绍了很多有用的工具，可以运用到你的网站中。

做了修改之后，功能测试还是通不过。

### 7.5 Django 中的静态文件

Django 处理静态文件时需要知道两件事（其实所有 Web 服务器都是如此）

* 收到指向某个 URL 的请求时，如何区分请求的是静态文件，还是需要经过视图函数处理，生成 HTML
* 到哪里去找用户请求的静态文件

其实，静态文件就是把 URL 映射到硬盘中文件上。

DJango 允许我们定义一个 URL 前缀，任何以这个前缀开头的 URL 都被视作针对静态文件的请求。默认的前缀是 /static/，在 settings.py 中定义：

```python
# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.7/howto/static-files/

STATIC_URL = "/static/"
```

后面在这一部分添加的设置都和第二个问题有关，即在硬盘中找到真正的静态文件。

既然用的是 Django 开发服务器 `manage.py runserver`，就可以把寻找静态文件的任务交给 Django 完成。Django 会在各应用中每个名为 static 的子文件夹里寻找静态文件。

为什么现在不起作用呢？因为没在 URL 中加入前缀 /static/。再看一下 base.html 中链接 CSS 的元素：

```html
<link href="css/bootstrap.min.css" rel="stylesheet" media="screen">
```
若想让这行代码起作用，要把它改成：
```html
<link href="/static/bootstrap/css/bootstrap.min.css" rel="stylesheet" media="screen">
```

现在，开发服务器收到这个请求时就知道请求的是静态文件，因为 URL 以 /static/ 开头。然后，服务器在每个应用中名为 static 的子文件夹里搜寻名为 bootstrap/css/bootstrap.min.css 的文件。

#### 换用 StaticLiveServerCase

不过，功能测试还是无法通过。

这是因为，虽然 runserver 启动的开发服务器能自动找到静态文件，但 LiveServerTestCase 找不到。不过，Django 为开发者提供了一个更神奇的测试类，叫 [StaticLiveServerCase](https://docs.djangoproject.com/en/1.7/howto/static-files/#staticfiles-testing-support)。

下面换用这个测试类：

```python
from django.contrib.staticfiles.testing import StaticLiveServerTestCase

__author__ = '__L1n__w@tch'


class NewVisitorTest(StaticLiveServerTestCase):
    pass
```

现在测试能找到 CSS 了，因此测试也能通过了。

```python
python manage.py test functional_tests
```

> Windows 用户在这里可能会看到一些错误消息，这在 tearDown 方法的 self.browser.quit() 之前加上 self.browser.refresh() 就能去掉这些错误。

### 7.6 使用 Bootstrap 中的组件改进网站外观

