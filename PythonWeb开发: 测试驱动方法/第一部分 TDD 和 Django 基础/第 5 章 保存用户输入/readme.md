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

看一下功能测试中的代码异味。检查清单表格中新添加的待办事项时，用了三个几乎一样的代码块。编程中有个原则叫做“不要自我重复”。

要提交目前已编写的代码，重构之前一定要提交：

```shell
git diff
git commit -a
```



