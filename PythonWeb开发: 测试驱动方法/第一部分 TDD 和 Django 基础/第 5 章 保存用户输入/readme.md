## 5.1 编写表单，发送 POST 请求

接下来要使用标准的 HTML POST 请求，若想让浏览器发送 POST 请求，要给 `<input>` 元素指定 name= 属性，然后把它放在 `<form>` 标签中，并为 `<form>` 标签指定 `method="POST"` 属性，这样浏览器才能向服务器发送 POST 请求。调整一下 home.html 中的模板：

```html
<h1>
  Your To-Do list
</h1>
<form method="POST">
  <input name="item_next" id="id_new_item" placeholder="Enter a to-do item" />
</form>

<table id="id_list_table">
  
</table>
```

现在运行功能测试，发现了预料之外的错误。如果功能测试出乎意外地失败了，可以做下面几件事，找出问题所在：

* 添加 print 语句，输出页面中当前显示的文本是什么
* 改进错误消息，显示当前状态的更多信息
* 亲自手动访问网站
* 在测试执行过程中使用 time.sleep 暂停

下面试一下在错误发生位置的前面加上 time.sleep，更改 functional_tests.py 文件：

```python
input_box.send_keys(Keys.ENTER)

import time
time.sleep(10)
table = self.browser.find_element_by_id("id_list_table")
```

如果 Selenium 运行得很慢，你就可以发现这个问题。现在再次运行功能测试，可以看到页面显示了 Django 提供的很多调试信息。

> 安全
>
> 跨站请求伪造（CSRF）漏洞。
>
> 作者推荐了一本书，Ross Anderson 写的 Security Engineering。

Django 针对 CSRF 的保护措施是在生成的每个表单中放置一个自动生成的令牌，通过这个令牌判断 POST 请求是否来自同一个网站。

之前的模板都是纯粹的 HTML，在这里要使用“模板标签”（template tag）添加 CSRF 令牌。模板标签的句法是花括号和百分号形式，即 `{% ... %}`

在 home.html 中进行修改：

```html
<form method="POST">
  <input name="item_next" id="id_new_item" placeholder="Enter a to-do item" />{% csrf_token %}
</form>
```

渲染模板时，Django 会把这个模板标签替换成一个`<input type="hidden">` 元素，其值是 CSRF 令牌。现在运行功能测试，会看到一个预期失败 `AssertionError`

可以看到，提交表单后新添加的待办事项不见了，页面刷新后又显示了一个空表单。这是因为还没连接服务器让它处理 POST 请求，所以服务器忽略请求，直接显示常规首页。

### 5.2 在服务器中处理 POST 请求

还没为表单指定 action= 属性，因此提交表单后默认返回之前渲染的页面，即 "/"，这个页面由视图函数 home_page 处理。下面修改这个函数，让其能处理 POST 请求。

这意味着要为视图函数 home_page 编写一个新的单元测试。打开 lists/tests.py 文件，在 HomePageTest 类中添加一个新方法。在其中添加 POST 请求，再检查返回的 HTML 中是否有新添加的待办事项文本：

```python
def test_home_page_can_save_a_POST_request(self):
    request = HttpRequest()
    request.method = "POST"
    request.POST["item_text"] = "A new list item"
    
    response = home_page(request)
    self.assertIn("A new list item", response.content.decode())
```

> “设置配置-执行代码-编写断言”是单元测试的典型结构

可以看出，用到了 HttpRequest 的几个特殊属性：.method 和 .POST，可以阅读 Django 关于请求和响应的[文档]( https://docs. djangoproject.com/en/1.7/ref/request-response/)。然后再检查 POST 请求渲染得到的 HTML 中是否有指定的文本。

运行测试后，会看到预期的失败：`python manage.py test`

为了让测试通过，可以故意编写一个符合测试的返回值，更改 lists/views.py：

```python
from django.http import HttpResponse
from django.shortcuts import render

def home_page(request):
    if request.method == "POST":
        return HttpResponse(request.POST["item_text"])
    return render(request, "home.html")
```

这样单元测试就能通过了，但这并不是我们真正想要做的。

### 5.3 把 Python 变量传入模板中渲染

先介绍在模板中使用哪种语法引入 Python 对象。要使用的符号是 {{ ... }}，它会以字符串的形式显示对象：

```html
<body>
  <h1>
    Your To-Do list
  </h1>
  <form method="POST">
    <input name="item_text" id="id_new_item" placeholder="Enter a to-do item" />{% csrf_token %}
  </form>
  
  <table id="id_list_table">
    <tr><td>{{ new_item_text }}</td></tr>
  </table>
</body>
```

在前一个单元测试中已经用到了 render_to_string 函数，用它手动渲染模板，然后拿它的返回值和视图函数返回的 HTML 比较。下面添加想传入的变量：

```python
self.assertIn("A new list item", response.content.decode())
expected_html = render_to_string(
	"home.html",
    {"new_item_text": "A new list item"}
)
self.assertEqual(response.content.decode(), expected_html)
```

可以看出，`render_to_string` 函数的第二个参数是变量名到值的映射。向模板中传入了一个名为 `new_item_text` 的变量，其值是期望在 POST 请求中发送的待办事项文本。

运行这个单元测试时，render_to_string 函数会把 `<td>` 中的`{{ new_item_text }}` 替换成“A new list item”。视图函数目前还无法做到这一点，因此会看到失败。

重写视图函数，把 POST 请求中的参数传入模板：

```python
def home_page(request):
    return render(request, "home.html", {
  		"new_item_text": request.POST["item_text"],
})
```

然后再运行单元测试，发现意料之外的错误。我们让正在处理的测试通过了，但是这个单元测试却导致了一个意想不到的结果，或者称之为“回归”：破坏了没有 POST 请求时执行的那条代码路径。

这次失败的修正方法如下：

```python
def home_page(request):
    return render(request, "home.html", {
  		"new_item_text": request.POST.get("item_text", ""),
})
```

可以查阅 dict.get 的[文档](http://docs.python.org/3/library/stdtypes. html#dict.get)。这个单元测试现在应该可以通过了。

#### 个人实践

自己的单元测试没有通过，原因在于 `{% csrf_token %}` 把这句删除了倒是能通过了。但是这样就无法通过功能测试了，最终[参考](http://stackoverflow.com/questions/34629261/django-render-to-string-ignores-csrf-token)可知把测试里的 `render_to_string` 中给予参数 `request=request` 即可。这样能通过测试了。

接下来看一下功能测试的结果如何：

`AssertionError: False is not true : New to-do item did not appear in table`

错误消息没太大帮助，使用另一种功能测试的调试技术：改进错误消息。修改 `functional_tests.py` 文件中的代码：

```python
self.assertTrue(
	any(row.text == "1: Buy pen" for row in rows),
    "New to-do item did not appear in table -- its text was:\n{}".format(table.text)
)
```

改进后，测试给出了更有用的错误消息。

有一种更简单的实现方式，即把 assertTrue 换成 assertIn：

```python
self.assertIn("1: Buy pen", [row.text for row in rows])
```

让测试通过的最快方法是修改模板：

```html
<tr><td>1: {{ new_item_text }}</td></tr>
```

> “遇红/变绿/重构” 和三角法
>
> * 先编写一个会失败的单元测试（遇红）
> * 编写尽可能简单的代码让测试通过（变绿），就算作弊也行
> * 重构，改进代码，让其更合理
>
> 重构阶段的实现：
>
> * 一种方法是消除重复：如果测试中使用了常量，而应用代码中也应用了这个常量，这就算是重复。此时就应该重构。
>
>
> * 三角法，如果编写无法让你满意的作弊代码就能让测试通过，就再写一个吃，强制自己编写更好的代码。扩充功能测试，检查输入的第二个列表项目中是否包含 "2: "

接下来扩充功能测试，检查表格中添加的第二个待办事项。

```python
        # 页面中又显示了一个文本框, 可以输入其他的待办事项
        # Y 输入了 Use pen to take notes
        # Y 做事很有条理
        input_box = self.browser.find_element_by_id("id_new_item")
        input_box.send_keys("Use pen to take notes")
        input_box.send_keys(Keys.ENTER)

        # 页面再次更新, 她的清单中显示了这两个待办事项
        table = self.browser.find_element_by_id("id_list_table")
        rows = table.find_elements_by_tag_name("tr")
        self.assertIn("1: Buy pen", [row.text for row in rows])
        self.assertIn("2: Use pen to take notes", [row.text for row in rows])

        # Y 想知道这个网站是否会记住她的清单
        self.fail("Finish the test!")  # 不管怎样, self.fail 都会失败, 生成指定的错误消息。我使用这个方法提醒测试结束了。
```

运行功能测试，很显然会返回一个错误：

```python
AssertionError: '1: Buy pen' not found in ['1: Use pen to take notes']
```

### 5.4 事不过三，三则重构

看一下功能测试中的代码异味（表明一段代码需要重写）。检查清单表格中新添加的待办事项时，用了三个几乎一样的代码块。编程中有个原则叫做“不要自我重复”。

要提交目前已编写的代码，重构之前一定要提交：

```shell
git diff
git commit -a
```

然后重构功能测试。可以定义一个行间函数，不过这样会搅乱测试流程。记住只有名字以 `test_` 开头的方法才会作为测试运行，可以根据需求使用其他方法。

```python
def check_for_row_in_list_table(self, row_text):
    table = self.browser.find_element_by_id("id_list_table")
    rows = table.find_elements_by_tag_name("tr")
    self.assertIn(row_text, [row.text for row in rows])
```

作者喜欢把辅助方法放在类的顶部，置于 tearDown 和第一个测试之间。接下来在 `functional_tests.py` 中使用这个辅助方法：

```python
        # Y 按下回车键后, 页面更新了
        # 待办事项表格中显示了 "1: Buy pen"
        input_box.send_keys(Keys.ENTER)
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

        # Y 想知道这个网站是否会记住她的清单
        self.fail("Finish the test!")  # 不管怎样, self.fail 都会失败, 生成指定的错误消息。我使用这个方法提醒测试结束了。
```

再次运行功能测试，看重构前后的表现是否一致，之后提交这次针对功能测试的重构：

```shell
git diff # 查看 functional_tests.py 中的改动
git commit -a
```

### 5.5 Django ORM 和第一个模型

“对象关系映射器”（Object-Relational Mapper，ORM）是一个数据抽象层，描述存储在数据库中的表、行和列。处理数据库时，可以使用熟悉的面向对象方式，写出更好的代码。在 ORM 的概念中，类对应数据库中的表，属性对应列，类的单个实例表示数据库中的一行数据。

Django 对 ORM 提供了良好的支持，学习 ORM 的绝佳方法是在单元测试中使用它，因为单元测试能按指定方式使用 ORM。

下面在 lists/tests.py 文件中新建一个类：

```python
from lists.models import Item

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
```

由上述代码可以看出，在数据库中创建新纪录的过程很简单：先创建一个对象，再为一些属性赋值，然后调用 .save() 函数。Django 提供了一个查询数据库的 API，即类属性 .objects。再使用可能是最简单的查询方法 .all()，取回这个表中的全部记录。得到的结果是一个类似列表的对象，叫 QuerySet。从这个对象中可以提取出单个对象，然后还可以再调用其它函数，例如 .count()。接着，检查存储在数据库中的对象，看保存的信息是否正确。

Django 中的 ORM 有很多有用且直观的功能。略读 [Django](https://docs. djangoproject.com/en/1.7/intro/tutorial01/) 教程，这个教程很好地介绍了 ORM 的功能。

> 单元测试和集成测试的区别以及数据库
>
> 真正的单元测试绝不能涉及数据库操作。刚编写的测试叫做“整合测试”（Integrated Test）更确切，因为它不仅测试代码，还依赖于外部系统，即数据库

试着运行单元测试，接下来要进入另一次“单元测试/编写代码”循环：

```python
ImportError: cannot import name "Item"
```

下面在 lists/models.py 中写入一些代码，让它有内容可导入。直接跳过 ``Item=None`` 这一步，直接创建类：

```python
from django.db import models

class Item(object):
    pass
```

这些代码让测试向前进展了，为了给 Item 类提供 save 方法，要让它继承 Model 类。

#### 5.5.1 第一个数据库迁移

再次运行测试，会看到一个数据库错误：

```python
django.db.utils.OperationalError: no such table: lists_item
```

在 Django 中，ORM 的任务是模型化数据库。创建数据库其实是由另一个系统负责的，叫做“迁移”（migration）。迁移的任务是，根据你对 models.py 文件的改动情况，添加或删除表和列。

可以把迁移想象成数据库使用的版本控制系统。把应用部署到线上服务器升级数据库时，迁移十分有用。

现在只需要知道如何创建第一个数据库迁移——使用 makemigrations 命令创建迁移：``python manage.py makemigrations``

#### 5.5.2 测试向前走得挺远

``python manage.py test lists``

可以发现这次离上次失败的位置整整八行。在这八行代码中，保存了两个待办事项，检查它们是否存入了数据库。

继承 models.Model 的类映射到数据库中的一个表。默认情况下，这种类会得到一个自动生成的 id 属性，作为表的主键，但是其他列都要自行定理。定义文本字段的方法如下：

```python
class Item(models.Model):
    text = models.TextField()
```

Django 提供了很多其他字段类型，例如 IntegerField、CharField、DateField 等。使用 TextField 而不用 CharField，是因为后者需要限制长度，但是就目前而言，这个字段的长度是随意的。关于字段类型的介绍可以阅读 Django [教程](https://docs.djangoproject. com/en/1.7/intro/tutorial01/#creating-models)和[文档](https://docs.djangoproject.com/en/1.7/ ref/models/fields/)。

#### 5.5.3 添加新字段就要创建新迁移

运行测试，会看到另一个数据库错误：

```python
django.db.utils.OperationalError: no such column: lists_item.text
```

出现这个错误的原因是在数据库中添加了一个新字段，所以要再创建一个迁移。

创建迁移试试：``python manage.py makemigrations``

会提示一个选项，这里选择选项 2：`2) Quit, and let me add a default in models.py`

这个命令不允许添加没有默认值的列，选择完第二个选项后，在 models.py 中设定一个默认值。

```python
class Item(models.Model):
    text = models.TextField(default="")
```

现在应该可以顺利创建迁移了：`python manage.py makemigrations`

在 models.py 中添加了两行新代码，创建了两个数据库迁移，由此得到的结果是，模型对象上的 .text 属性能被识别为一个特殊属性了，因此属性的值能保存到数据库中，测试也能通过了。

下面提交创建的第一个模型：

```shell
git status # 看到 tests.py 和 models.py, 以及两个没跟踪的迁移文件
git diff # 审查 tests.py 和 modesl.py 中的改动
git add lists
git commit -m "Model for list Items and associated migration"
```

### 5.6 把 POST 请求中的数据存入数据库

接下来，要修改针对首页中的 POST 请求的测试。希望视图把新添加的待办事项存入数据库，而不是直接传给响应。为了测试这个操作，要在现有的测试方法中添加三行新代码：

```python
def  test_home_page_can_save_a_POST_requests(self):
    ...
    
    self.assertEqual(Item.objects.count(), 1) # 检查是否把一个新 Item 对象存入数据库。objects.count() 是 objects.all().count() 的简写形式。
    new_item = Item.objects.first() # objects.first() 等价于 objects.all()[0]
    self.assertEqual(new_item.text, "A new list item") # 检查待办事项的文本是否正确
```

这个测试变得有点儿长，看起来要测试很多不同的东西。这也是一种代码异味。

再次运行测试，会看到一个预期失败。修改一下视图：

```python
from django.shortcuts import render
from lists.models import Item

def home_page(request):
    item = Item()
    item.text = request.POST.get("item_text", "")
    item.save()
    
    return render(request, "home.html", {
  		"new_item_text": request.POST.get("item_text", ""),
	})
```

这里有个很明显的问题，每次请求首页都保存一个无内容的待办事项。稍后再解决。

看一下单元测试的进展如何，发现通过了，现在可以做些重构了：

```python
return render(request, "home.html", {
  	"new_item_text": item.text
})
```

现在有几个待解决的问题：

* 不要每次请求都保存空白的待办事项
* 代码异味：POST 请求的测试太长
* 在表格中显示多个待办事项
* 支持多个清单！

现在为第一个问题定义一个新的测试方法：

```python
class HomePageTest(TestCase):
    def test_home_page_only_saves_items_when_necessary(self):
        request = HttpRequest()
        home_page(request)
        self.assertEqual(Item.objects.count(), 0)
```

测试得到预期的失败，下面对视图函数进行改动：

```python
def home_page(request):
    if request.method == "POST":
        new_item_text = request.POST["item_text"] # 使用一个名为 new_item_text 的变量，其值是 POST 请求中的数据，或者是空字符串
        Item.objects.create(text=new_item_text) # .objects.create 是创建新 Item 对象的简化方式，无需再调用 .save() 方法
    else:
        new_item_text = ""
        
    return render(request, "home.html", {
 		"new_item_text": new_item_text    
	})
```

### 5.7 处理完 POST 请求后重定向

`new_item_text = ""` 不太合适，幸好第二个问题有机会可以顺带解决这个问题。[人们都说处理完 POST 请求之后一定要重定向](https://en.wikipedia.org/ wiki/Post/Redirect/Get)。再次修改针对保存 POST 请求数据的单元测试，不让它渲染包含待办事项的响应，而是重定向到首页：

```python
def test_home_page_can_save_a_POST_request(self):
    request = HttpRequest()
    request.method = "POST"
    request.POST["item_text"] = "A new list item"
    
    response = home_page(request)
    
    self.assertEqual(Item.objects.count(), 1)
    new_item = Item.objects.first()
    self.assertEqual(new_item.text, "A new list item")
    
    self.assertEqual(response.status_code, 302)
    self.assertEqual(response["location"], "/")
```

re，因此把相应的断言删掉了。现在，响应是 HTTP 重定向，状态码是 302，让浏览器指向一个新地址。

修改之后运行测试，得到的结果是 `200 != 302` 错误。现在可以大幅度清理视图函数了：

```python
from django.shortcuts import redirect, render
from lists.models import Item

def home_page(request):
    if request.method == "POST":
        Item.objects.create(text=request.POST["item_text"])
        return redirect("/")
    
    return render(request, "home.html")
```

#### 更好的单元测试实践方法：一个测试只测试一件事

现在视图函数处理完 POST 请求后会重定向，这是习惯做法，而且单元测试也一定程度上缩短了，不过还可以做得更好。良好的单元测试实践方法要求，一个测试只能测试一件事。更改代码如下：

```python
def test_home_page_can_save_a_POST_request(self):
    request = HttpRequest()
    request.method = "POST"
    request.POST["item_text"] = "A new list item"
    
    response = home_page(request)
    
    self.assertEqual(Item.objects.count(), 1)
    new_item = Item.objects.first()
    self.assertEqual(new_item.text, "A new list item")
    
def test_home_page_redirects_after_POST(self):
    request = HttpRequest()
    request.method = "POST"
    request.POST["item_text"] = "A new list item"
    
    response = home_page(request)
    
    self.assertEqual(response.status_code, 302)
    self.assertEqual(response["location"], "/")
```

### 5.8 在模板中渲染待办事项

接下来要解决的问题是在表格中显示多个待办事项。要编写一个新单元测试，检查模板是否也能显示多个待办事项：

```python
class HomePageTest(TestCase):
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
```

这个测试和预期一样会失败，Django 的模板句法中有一个用于遍历列表的标签，即 `{% for .. in .. %}` 。可以按照下面的方式使用这个标签：

```html
<table id="id_list_table">
  {% for item in items %}
  	<tr><td>1: {{ item.text }}</td></tr>
  {% endfor %}
</table>
```

这是模板系统的主要优势之一。现在模板会渲染多个 `<tr>` 行，每一行对应 items 变量中的一个元素。可以阅读 [Django 文档](https://docs.djangoproject.com/en/1.7/topics/templates/)，学习模板的其他用法。

只修改模板还不能让测试通过，还要在首页的视图把待办事项传入模板：

```python
def home_page(request):
    if request.method == "POST":
        Item.objects.create(text=request.POST["item_text"])
        return redirect("/")
    
	items = Item.objects.all()
	return render(request, "home.html", {"items": items})
```

单元测试是能通过了，关键是功能测试能通过吗？`python functional_tests.py`

很显然不能，要使用另一种功能测试调试技术，手动访问网站。可以看到提示“no such table: lists_item”（没有这个表：lists_item）。

### 5.9 使用迁移创建生产数据库

又是一个 Django 生成的很有帮助的错误消息，大意是说没有正确设置数据库。为什么在单元测试中一切都运行良好呢？这是因为 Django 为单元测试创建了专用的测试数据库。

为了设置好真正的数据库，要创建一个数据库。SQLite 数据库只是硬盘中的一个文件。你会在 Django 的 settings.py 文件中发现，默认情况下，Django 把数据库保存为 db.sqlite3，放在项目的基目录中。

我们已经在 models.py 文件和后来创建的迁移文件中告诉 Django 创建数据库所需的一切信息，为了创建真正的数据库，要使用 Django 中另一个强大的 manage.py 命令——migrate：`python manage.py migrate`

创建时需要回答一个关于超级用户的问题，暂时回答”no“，因为现在还不需要(PS: 自己咋没遇到这个选项)。现在，可以刷新 localhost 上的页面了，可以发现错误页面不见了。然后再运行功能测试。

发现快成功了，只需要让清单显示正确的序号即可。另一个出色的 Django 模板标签 for loop.counter 能帮助解决这个问题：

```html
{% for item in items %}
	<tr><td>{{ forloop.counter }}: {{ item.text }}</td></tr>
{% endfor %}
```

再试一次，应该会看到功能测试运行到最后了。

不过运行测试时，可以注意到每一次运行测试时都会在数据库中遗留了数据，这需要一种自动清理机制。你可以手动清理，方法是先删除数据库再执行 migrate 命令 新建。

```shell
rm db.sqlite3
python manage.py migrate --noinput
```

清理之后要确保功能测试仍能通过。先做一次提交吧。

```shell
git add lists
git commit -m "Redirect after POST, and show all items in template"
```

> 你可能会觉得在每一章结束时做个标记很有用，例如在本章结束时可以这么做：`git tag end-of-chapter-05`

这一章做的内容总结：

* 编写了一个表单，使用 POST 请求把新待办事项添加到清单中
* 创建了一个简单的数据库模型，用来存储待办事项
* 使用了至少三种功能测试调试技术

> 有用的 TDD 概念
>
> * 回归
>   * 新添加的代码破坏了应用原本可以正常使用的功能
> * 意外失败
>   * 测试在意料之外失败了。这意味着测试中有错误，或者测试帮我们发现了一个回归，因此要在代码中修正。
> * 遇红/变绿/重构
>   * 描述 TDD 流程的另一种方式。先编写一个测试看着它失败（遇红），然后编写代码让测试通过（变绿），最后重构，改进实现方式。
> * 三角法
>   * 添加一个测试，专门为某些现有的代码编写用例，以此推断出普适的实现方式
> * 事不过三，三则重构
>   * 判断何时删除重复代码时使用的经验法则。如果两段代码很相似，往往还要等到第三段相似代码出现，才能确定重构时哪一部分是真正共通、可重用的。
> * 记在便签上的待办事项清单
>   * 在便签上记录编写代码过程中遇到的问题，等手头的工作完成后再回过头来解决
