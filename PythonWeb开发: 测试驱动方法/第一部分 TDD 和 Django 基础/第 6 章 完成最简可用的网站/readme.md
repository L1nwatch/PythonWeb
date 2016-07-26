## 第 6 章 完成最简可用的网站
### 6.1 确保功能测试之间相互隔离

如何隔离测试？运行功能测试后待办事项一直存在于数据库中，这会影响下次测量的结果。

运行单元测试时，Django 的测试运行程序会自动创建一个全新的测试数据库（和应用真正使用的数据库不同），运行每隔测试之前都会清空数据库，等所有测试都运行完之后，再删除这个数据库。但是功能测试目前使用的是应用真正使用的数据库 db.sqlite3。

这个问题的解决方法之一是自己动手，在 `functional_tests.py` 中添加执行清理任务的代码。这样的任务最适合在 setUp 和 tearDown 方法中完成。

不过从 1.4 版本开始，Django 提供的一个新类，LiveServerTestCase，它可以代我们完成这一任务。这个类会自动创建一个测试数据库（跟单元测试一样），并启动一个开发服务器，让功能测试在其中运行。

LiveServerTestCase 必须使用 manage.py，由 Django 的测试运行程序运行。从 Django 1.6 开始，测试运行程序查找所有名字以 test 开头的文件。为了保持文件结构清晰，要新建一个文件夹保存功能测试，让它看起来就像一个应用。Django 对这个文件夹的要求只有一个——必须是有效的 Python 模块，即文件夹中要有一个 `__init__.py` 文件。

```shell
mkdir functional_tests
touch functional_tests/__init__.py
```

然后要移动功能测试，把独立的 `functional_tests.py` 文件移到 `functional_tests` 应用中，并把它重命名为 tests.py。使用 `git mv` 命令完成这个操作，让 Git 知道文件移动了。

```shell
git mv functional_tests.py functional_tests/tests.py
git status # 显示文件重命名为 functional_tests/tests.py，而且新增了 __init__.py
```

现在，运行功能测试不执行 `python functional_tests.py`，而是使用 `python manage.py test functional_tests` 命令。

> 功能测试可以和 lists 应用测试混在一起，不过作者更倾向于把两种测试分开，因为功能测试检测的功能往往存在不同应用中。功能测试以用户的视角看待事物，而用户并不关心你如何把网站分成不同的应用。

接下来编辑 `functional_tests/tests.py`，修改 `NewVisitorTest` 类，让它使用 LiveServerTestCase：

```python
from django.test import LiveServerTestCase
from selenium import webdriver
from selenium.webdriver.common.keys import keys

class NewVisitorTest(LiveServerTestCase):
    def setUp(self):
        [...]
```

继续往下修改。访问网站时，不用硬编码的本地地址（localhost:8000），可以使用 LiveServerTestCase 提供的 `live_server_url` 属性：

```python
def test_can_start_a_list_and_retrieve_it_later(self):
        # Y 访问在线待办事项应用的首页
        # self.browser.get("http://localhost:8000") # 不用硬编码了
        self.browser.get(self.live_server_url)
```

还可以删除文件末尾的 `if __name__ == "__main__"` 代码块，因为之后都使用 Django 的测试运行程序运行功能测试。

功能测试和重构前一样，能运行到 self.fail。如果再次运行测试，你会发现，之前的测试不再遗留待办事项了，因为功能测试运行完之后把它们清理掉了。

提交这次小改动：

```shell
git status # 重命名并修改了 functional_tests.py， 新增了 __init__.py
git add functional_tests
git diff --staged -M
git commit # 提交消息举例： "make functional_tests an app, use LiveServerTestCase"
```

git diff 命令中的 -M 标志很有用，意思是“检测移动”，所以 git 会注意到 `functional_tests.py` 和 `functional_tests/tests.py` 是同一个文件，显示更合理的差异。

#### 只运行单元测试

现在，如果执行 `python manage.py test` 命令，Django 会运行功能测试和单元测试：`python manage.py test`

如果只想运行单元测试，可以指定只运行 lists 应用中的测试：`python manage.py test lists`

> 有用的命令（更新版）
>
> * 运行功能测试
>
>   `python manage.py test functional_tests`
>
> * 运行单元测试
>
>   `python manage.py test lists`

现在，要让一个用户不能查看另一个用户的清单，而且每个清单都有自己的 URL，以便访问保存的清单。还要多想想怎么实现这个功能。

### 6.2 必要时做少量的设计

TDD 和软件开发中的敏捷运动联系紧密。敏捷运动反对传统软件工程实践中“预先做大量设计”的做法，因为除了要花费大量时间收集需求之外，设计阶段还要用等量的时间在纸上规划软件。敏捷理念则认为，在实践中解决问题比理论分析能学到更多，而且让应用尽早接受真实用户的检验效果更好。要尽早把最简可用的应用放出来，根据实际使用中得到的反馈逐步向前推进设计。

这并不是说要完全禁止思考设计。

现在想让每个用户都能保存自己的清单，至少能保存一个清单。这要把清单和其中的待办事项存入数据库。每个清单都有一个唯一的 URL，而且清单中的每个待办事项都是一些描述性文字，和所在的清单关联。

#### 6.2.1 YAGNI

关于设计的思考一旦开始就很难停下来，或许想给清单添加一个较长的备注和简短的描述，或许想存储某种顺序等。但是，要遵守敏捷理念的另一个信条：YAGNI（读作 yag-knee）。它是 “You aint gonna need it”。作为软件开发者，有时我们冒出一个想法，但大多数情况下最终你都用不到这个功能。应用中会残留很多没用的代码，还增加了应用的复杂度。

#### 6.2.2 REST

怎么处理数据结构，即使用“模型-视图-控制器”中的模型部分。那视图和控制器部分怎么办？

“表现层状态转化”（Representational State Transfer，REST）是 Web 设计的一种方式，经常用来引导基于 Web 的 API 设计。设计面向用户的网站时，不必严格遵守 REST 规则，可是从中能得到一些启发。

REST 建议 URL 结构匹配数据结构，即这个应用中的清单和其中的待办事项。清单有各自的 URL：`/lists/<list identifier>/`

这个 URL 满足了功能测试中提出的需求。若想查看某个清单，我们可以发送一个 GET 请求。若想创建全新的清单，可以向一个特殊的 URL 发送 POST 请求：`/lists/new`

若想在现有的清单中添加一个新待办事项，我们可以向另外一个 URL 发送 POST 请求：`/lists/<list identifier>/add_item`

概括起来，本章的便签如下所示：

* 调整模型，让待办事项和不同的清单关联起来
* 为每个清单添加唯一的 URL
* 添加通过 POST 请求新建清单所需的 URL
* 添加通过 POST 请求在现有的清单中增加新待办事项所需的 URL

### 6.3 使用 TDD 实现新设计

在流程的外层，既要添加新功能（扩展功能测试，再编写新的应用代码），也要重构应用的代码，即重写部分现有的实现，保持应用的功能不变，但使用新的设计方式，在单元测试层，要添加新测试或者修改现有的测试，检查想改动的功能，没改动的测试则用来保证这个过程没有破坏现有的功能。

用户提交第一个待办事项后，我们希望应用创建一个新清单，并在这个清单中添加一个待办事项，然后把她带到显示这个清单的页面。对功能测试进行修改：

```python
input_bnox.send_keys("Buy pen")

input_box.send_keys(Keys.ENTER)
edith_list_url = self.browser.current_url
self.assertRegex(edith_list_url, "/lists/.+") # assertRegex 是 unittest 中的一个辅助函数，检查字符串是否和正则表达式匹配。我们使用这个方法检查是否实现了新的 REST 式设计。具体用法参阅 [unittest 的文档](https://docs.python.org/3/library/unittest.html)
self.check_for_row_in_list_table("1: Buy pen")
```

还要修改功能测试的结尾部分，假设有一个新用户正在访问网站。这个新用户访问首页时，要测试他不能看到其他人的待办事项，而且他的清单有自己的唯一 URL。

从 self.fail 之前的注释开始，把随后的内容都删掉，替换成下述功能测试的新结尾：

```python
# 页面再次更新， Y 的清单中显示了这两个待办事项
self.check_for_row_in_list_table("2: Use pen to take notes")
self.check_for_row_in_list_table("1: Buy pen")

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
```

按照习惯，使用两个 # 号表示“元注释”。元注释的作用是说明测试的工作方式，以及为什么这么做。使用两个井号是为了和功能测试中解说用户故事的常规注释区分开。

运行功能测试后看下情况如下：

```python
AssertionError: Regex didn't match: '/lists/.+' not found in 'http://localhost:8081/'
```

出现了意料之外的错误。先提交一次，然后再编写一些新模型和新视图：

```shell
git commit -a
```

### 6.4 逐步迭代，实现新设计

现在要解决的问题是，为每个清单添加唯一的 URL 和标识符。清单的 URL 出现在重定向 POST 请求之后。在文件 `lists/tests.py` 中，找到 `test_home_page_redirects_after_POST`，修改重定向期望转向的地址：

```python
self.assertEqual(response.status_code, 302)
self.assertEqual(response["location"], "/lists/the-only-list-in-the-world/")
```

我们一次只做一项改动，既然应用现在只支持一个清单，那这就是唯一合理的 URL。

接下来修改 lists/view.spy 中的 `home_page` 视图：

```python
def home_page(request):
    if request.method == "POST":
        Item.objects.create(text=request.POST["item_text"])
        return redirect("/lists/the-only-list-in-the-world")
    
    items = Item.objects.all()
    return render(request, "home.html", {"items": items})
```

这么修改，功能测试显然会失败，因为网站中并没有这个 URL。运行功能测试，会看到测试在尝试提交第一个待办事项后失败，提示无法找到显示清单的表格。出现这个错误的原因是，`/the-only-list-in-the-world/` 这个 URL 还不存在。

### 6.5 使用 Django 测试客户端一起测试视图、模板和 URL

之前使用单元测试检查是否能解析 URL，还调用了视图函数检查它们是否能正常使用，还检查了视图能否正确渲染模板。其实，Django 提供了一个小工具，可以一次完成这三种测试。

#### 6.5.1 一个新测试类

下面使用 Django 测试客户端。打开 lists/tests.py，添加一个新测试类，命名为 ListViewTest。然后把 HomePageTest 类中的 `test_home_page_displays_all_list_items` 方法复制到这个新类中。重命名这个方法，再做些修改：

```python
class ListViewTest(TestCase):
    def test_displays_all_list_items(self):
        """
        测试页面是否能把所有待办事项都显示出来
        :return:
        """
        Item.objects.create(text="itemey 1")
        Item.objects.create(text="itemey 2")

        response = self.client.get("/lists/the-only-list-in-the-world/")  # 现在不直接调用视图函数了

        # 现在不必再使用 assertIn 和 response.content.decode() 了，Django 提供 assertContains 方法，它知道如何处理响应以及响应内容中的字节
        self.assertContains(response, "itemey 1")
        self.assertContains(response, "itemey 2")
```

> 有些人并不喜欢 Django 测试客户端。这些人说测试客户端隐藏了太多细节，而且牵涉了太多本该在真正的单元测试中使用的组件，因此最终写成的测试叫整合测试更合适。他们还抱怨，使用测试客户端的测试运行太慢（以毫秒计）。

尝试运行这个测试，得到 404 错误。

#### 6.5.2 一个新 URL

在 superlists/urls.py 中解决这个问题

> 留意 URL 末尾的斜线，在测试中和 urls.py 中都要小心，因为这个斜线往往就是问题的根源

```python
urlpatterns = patterns("",
	url(r"^$","lists.views.home_page", name="home"),
	url(r"^lists/the-only-list-in-the-word/$","lists.views.view_list", name="view_list")
                      )
```

再次运行测试，报错无法导入对应视图函数。

#### 6.5.3 一个新视图函数

在 lists/views.py 中定义一个新视图函数：

```python
def view_list(request):
	pass
```

测试失败，把 `home_page` 视图的最后两行复制过来，测试应该能通过了。

接下来该重构了，现在我们有两个视图，一个用于首页，一个用于单个清单。目前，这两个视图共用一个模板，而且传入了数据库中的所有待办事项。如果仔细查看单元测试中的方法，或许会发现某些部分需要修改：

```shell
grep -E "class | def" lists/tests.py
```

完全可以把 `test_home_page_displays_all_list_items` 方法删除，因为不需要了。而且不再需要在首页中显示所有的待办事项，首页只显示一个输入框让用户新建清单即可。

#### 6.5.4 一个新模板，用于查看清单

既然首页和清单视图是不同的页面，它们就应该使用不同的 HTML 模板。home.html 可以只包含一个输入框，新模板 list.tml 则在表格中显示现有的待办事项。下面添加一个新测试，检查是否使用了不同的模板：

```python
class ListViewTest(TestCase):
    def test_uses_list_template(self):
        response = self.client.get("/lists/the-only-list-in-the-world/")
        self.assertTemplateUsed(response, "list.html")
        
    def test_displays_all_items(self):
        [...]
```

assertTemplateUsed 是 Django 测试客户端提供的强大方法之一。检查测试结果，发现报出了 `AssertionError` 错误。然后修改视图：

```python
def view_list(request):
    items = Item.objects.all()
    return render(request, "list.html", {"items":items})
```

现在运行单元测试，会报出模板不存在的错误。新建该模板，保存为 lists/templates/list.html：`touch lists/templates/list.html`

接着测试，我们会使用到 home.html 中的很多代码，可以先把其中的内容复制过来：`cp lists/templates/home.html lists/templates/list.html`

这会让测试再次通过。现在继续重构。首页不用显示待办事项，只需一个新建清单的输入框就行了。因此进行修改：

```html
<body>
  <h1>
    Start a new To-Do list
  </h1>
  <form method="POST">
    <input name="item_text" id="id_new_item" placeholder="Enter a to-do item" />{% csrf_token %}
  </form>
</body>
```

在 `home_page` 视图中其实也不用把全部待办事项都传入 home.html 模板，因此可以继续修改：

```python
def home_page(request):
    if request.method == "POST":
        Item.objects.create(text=request.POST["item_text"])
        return redirect("/lists/the-only-list-in-the-world/")
    return render(request, "home.html")
```

再次运行单元测试，它们仍然能够通过。然后运行功能测试，输入第二个待办事项时还是失败。问题的原因是新建的待办事项的表单没有 action= 属性，因此默认情况下，提交地址就是渲染表单的页面地址。表单在首页中可用，因为首页是目前唯一知道如何处理 POST 请求的页面，但在视图函数 view_list 中不能用了，POST 请求会直接被忽略。在 list.html 中修正：

```html
<form method="POST" action="/">
```

然后再运行功能测试，可以发现重新回到了修改前的状态，这就意味着重构结束了。现在清单有唯一的 URL 了。

提交目前取得的进展：

```shell
git status # 会看到 4个改动的文件和 1 个新文件 list.html
git add lists/templates/list.html
git diff
git commit -am "new URL, view and template to display lists"
```

### 6.6 用于添加待办事项的 URL 和 视图

#### 6.6.1 用来测试新建清单的测试类

打开文件 lists/tests.py，把 `test_home_page_can_save_a_POST_request` 和 `test_home_page_redirects_after_POST` 两个方法移到一个新类中，然后再修改这两个方法的名字：

```python
class NewListTest(TestCase):
    def test_saving_a_POST_request(self):
        request = HttpRequest()
        request.method = "POST"
        [...]
    
    def test_redirects_after_POST(self):
        [...]
```

然后使用 Django 测试客户端重写：

```python
class NewListTest(TestCase):
    def test_saving_a_POST_request(self):
        """
        测试页面是否能够保存 POST 请求, 并且能够把用户提交的待办事项保存到表格中
        :return:
        """
        self.client.post("/lists/new", data={"item_text": "A new list item"})

        # 检查是否把一个新 Item 对象存入数据库。objects.count() 是 objects.all().count() 的简写形式。
        self.assertEqual(Item.objects.count(), 1, "希望数据库中现在有 1 条数据, 然而却有 {} 条数据".format(Item.objects.count()))
        new_item = Item.objects.first()  # objects.first() 等价于 objects.all()[0]
        self.assertEqual(new_item.text, "A new list item")  # 检查待办事项的文本是否正确

    def test_redirects_after_POST(self):
        """
        测试在发送 POST 请求后是否会重定向
        :return:
        """
        response = self.client.post("/lists/new", data={"item_text": "A new list item"})

        self.assertEqual(response.status_code, 302, "希望返回 302 代码, 然而却返回了 {}".format(response.status_code))
        self.assertEqual(response["location"], "/lists/the-only-list-in-the-world")
```

运行测试，发现 404 错误。这是因为还没把 /lists/new 添加到 URL 映射中，所以 client.post 得到的是 404 响应。

#### 6.6.2 用于新建清单的 URL 和 视图

下面添加新的 URL 映射：

```python
urlpatterns = [
    # url(r'^admin/', admin.site.urls),
    url(r"^$", "lists.views.home_page", name="home"),
    url(r"^lists/the-only-list-in-the-world/$", "lists.views.view_list", name="view_list"),
    url(r"^lists/new$","lists.view.new_list",name="new_list")
]
```

再运行测试，发现错误。现在既然知道需要的是重定向，那就从 `home_page` 视图中借用一行代码吧。

```python
def new_list(request):
    return redirect("/lists/the-only-list-in-the-world/")
```

现在的测试结果表明没有加入新事物，再次向 `home_page` 借用一行代码即可。

```python
def new_list(request):
    Item.objects.create(text=request.POST["item_text"])
    return redirect("/lists/the-only-list-in-the-world")
```

另外一个错误是作者提到的【自己并没有遇到，可能是版本不同】：

```python
self.assertEqual(response['location'], '/lists/the-only-list-in-the-world/')
     AssertionError: 'http://testserver/lists/the-only-list-in-the-world/' !=
     '/lists/the-only-list-in-the-world/'
```

出现这个失败的原因是，Django 测试客户端的表现和纯正的视图函数有细微差别：测试客户端使用完整的 Django 组件，会在相对 URL 前加上域名。使用 Django 提供的另一个测试辅助函数换掉重定向的两步检查：

```python
    def test_redirects_after_POST(self):
        """
        测试在发送 POST 请求后是否会重定向
        :return:
        """
        response = self.client.post("/lists/new", data={"item_text": "A new list item"})

        self.assertEqual(response.status_code, 302, "希望返回 302 代码, 然而却返回了 {}".format(response.status_code))
        self.assertEqual(response["location"], "/lists/the-only-list-in-the-world/")
        self.assertRedirects(response, "/lists/the-only-list-in-the-world/")  # 等价于上面两条
```

【PS】自己做的时候 self.assertRedirects 反而报错了，说是 301 代码。后来发现是链接最后一个斜杠没加上。。。

#### 6.6.3 删除当前多余的代码和测试

现在要大幅度精简 `home_page` 函数了，比如说，可以删除整个 `if request.method == "POST"` 部分？

```python
def home_page(request):
    return render(request, "home.html")
```

还可以把多余的测试方法 `test_home_page_only_saves_items_when_necessary` 也删掉。

#### 6.6.4 让表单指向刚添加的新 URL

最后，修改两个表单，让它们使用刚添加的新的 URL。在 home.html 和 lists.html 中，把表单改成：

```python
<form method="POST" action="/lists/new">
```

然后运行功能测试，确保一切正常运行，或者至少和修改前的状态一样。

接下来可以作为一次完整的提交：对 URL 映射做了些改动。

```shell
git status # 5 个改动的文件
git diff
git commit -a
```

### 6.7 调整模型 

现在下决心修改模型。先调整模型的单元测试。这次换种方式，以差异的形式表示改动的地方：

```python
@@ -3,7 +3,7 @@ from django.http import HttpRequest
      from django.template.loader import render_to_string
      from django.test import TestCase
     -from lists.models import Item
     +from lists.models import Item, List
      from lists.views import home_page
      class HomePageTest(TestCase):
     @@ -60,22 +60,32 @@ class ListViewTest(TestCase):
     -class ItemModelTest(TestCase):
     +class ListAndItemModelsTest(TestCase):
          def test_saving_and_retrieving_items(self):
     +        list_ = List()
     +        list_.save()
     +
              first_item = Item()
              first_item.text = 'The first (ever) list item'
     +        first_item.list = list_
              first_item.save()
        
              second_item = Item()
              second_item.text = 'Item the second'
     +        second_item.list = list_
    		  second_item.save()
     +        saved_list = List.objects.first()
     +        self.assertEqual(saved_list, list_)
     +
              saved_items = Item.objects.all()
              self.assertEqual(saved_items.count(), 2)
              first_saved_item = saved_items[0]
              second_saved_item = saved_items[1]
              self.assertEqual(first_saved_item.text, 'The first (ever) list item')
     +        self.assertEqual(first_saved_item.list, list_)
              self.assertEqual(second_saved_item.text, 'Item the second')
     +        self.assertEqual(second_saved_item.list, list_)
```

新建了一个 List 对象，然后通过给 .list 属性赋值把两个待办事项归在这个对象名下。要检查这个清单是否正确保存，也要检查是否保存了那两个待办事项与清单之间的关系。还可以直接比较两个清单（`saved_list` 和 `list_` ）——其实比较的是两个清单的主键（.id 属性）是否相同。

> 使用变量名 `list_` 的目的是防止遮盖 Python 原生的 `list` 函数。

在接下来的几次迭代中，只给出每次运行测试时期望看到的错误消息，不会告诉你运行测试前要输入哪些代码，你要自己编写每次所需的最少代码改动。

依次会看到的错误消息是：

```python
ImportError: cannot import name "List"
AttributeError: 'List' object has no attribute 'save'
django.db.utils.OperationalError: no such table: lists_list
```

因此，需要执行一次 `makemigrations` 命令。

之后会看到：

```python
self.assertEqual(first_saved_item.list, list_)
     AttributeError: 'Item' object has no attribute 'list'
```

#### 6.7.1 通过外键实现的关联

Item 的 list 属性实现，先把它当成 text 属性试试。

```python
class Item(models.Model):
    text = modesl.TextField(default="")
    list = modesl.TextField(default="")
```

照例，测试会告诉我们需要做一次迁移。`python manage.py makemigrations`

再看一下测试结果如何：`AssertionError: 'List object' != <List: List object>`

仔细看 `!=` 两边的内容。Django 只保存了 List 对象的字符串形式。若想保存对象之间的关系，要告诉 Django 两个类之间的关系，这种关系使用 ForeignKey 字段表示：

```python
from django.db import models

class List(models.Model):
    pass

class Item(models.Model):
    text = models.TextField(Defualt="")
    list = modes.ForeignKey(List, default=None)
```

修改之后也要做一次迁移，同时之前的迁移没用了，删掉吧：

```shell
rm lists/migrations/0004_item_list.py
python manage.py makemigrations
```

> 删除迁移是种危险操作。如果删除已经用于某个数据库的迁移，Django 就不知道当前状态，因此也就不知道如何运行以后的迁移。只有当你确定某个迁移没被使用时才能将其删除。根据经验，已经提交到 VCS 的迁移绝不能删除。

#### 6.7.2 根据新模型定义调整其他代码

再看测试的结果如何：`python manage.py test lists`

出现这些错误是因为我们在待办事项和清单之间建立了关联，在这种关联中，每个待办事项都需要一个父级清单，但是原来的测试并没有考虑到这一点。

最简单的方法是修改 ListViewTest，为测试中的两个待办事项创建父清单：

```python
class ListViewTest(TestCase):
    def test_displays_all_items(self):
        list_ = List.objects.create()
        Item.objects.create(text="itemey 1", list=list_)
        Item.objects.create(text="itemey 2", list=list_)
```

修改之后，失败测试减少到两个，而且都是向 `new_list` 视图发送 POST 请求引起的。使用惯用的技术分析调用跟踪，由错误消息找到导致错误的测试代码，然后再找出相应的应用代码，最终定位到下面这行。

```python
    Item.objects.create(text=request.POST["item_text"])
```

这行调用跟踪表明创建待办事项时没有指定父清单。因此，要对视图做类似修改：

```python
from lists.models import Item, List

def new_list(request):
    list_ = List.objects.create()
    Item.objects.create(text=request.POST["item_text"], list=list_)
    return redirect("/lists/the-only-list-in-the-world/")
```

修改之后，测试又能通过了。

为了确信一切都能正常运行，要再次运行功能测试。确保测试的结果和修改前一样。现在功能没有破坏，在此基础上还修改了数据库。提交：

```shell
git status
git add lists
git diff -staged
git commit
```

### 6.8 每个列表都应该有自己的 URL

最简单的处理方式是使用数据库自动生成的 id 字段。下面修改 ListViewTest，让其中的两个测试指向新 URL。

还要把 `test_displays_all_items` 测试重命名为 `test_displays_only_items_for_that_list`，然后在这个测试中确认只显示属于这个清单的待办事项。

```python
class ListViewTest(TestCase):
    def test_displays_all_list_items(self):
        """
        测试页面是否能把所有待办事项都显示出来
        :return:
        """
        correct_list = List.objects.create()
        Item.objects.create(text="itemey 1", list_attr=correct_list)
        Item.objects.create(text="itemey 2", list_attr=correct_list)
        other_list = List.objects.create()
        Item.objects.create(text="other item 1", list_attr=other_list)
        Item.objects.create(text="other item 2", list_attr=other_list)

        response = self.client.get("/lists/{unique_url}/".format(unique_url=correct_list.id))  # 现在不直接调用视图函数了
        # 现在不必再使用 assertIn 和 response.content.decode() 了
        # Django 提供 assertContains 方法，它知道如何处理响应以及响应内容中的字节
        self.assertContains(response, "itemey 1")
        self.assertContains(response, "itemey 2")

        self.assertNotContains(response, "other item 1")
        self.assertNotContains(response, "other item 2")

    def test_uses_list_template(self):
        """
        测试是否使用了不同的模板
        :return:
        """
        list_ = List.objects.create()
        response = self.client.get("/lists/{unique_url}/".format(unique_url=list_.id))
        self.assertTemplateUsed(response, "list.html")
```

> 可以阅读 [Dive Into Python](http://www.diveintopython.net/)，这本书对字符串代换做了很好的介绍。

运行这个单元测试，会看到预期的 404，以及另一个相关的错误。

#### 6.8.1 捕获 URL 中的参数

现在要学习如何把 URL 中的参数传入视图：

```python
urlpatterns = [
    # url(r'^admin/', admin.site.urls),
    url(r"^$", "lists.views.home_page", name="home"),
    url(r"^lists/(.+)/$", "lists.views.view_list", name="view_list"),
    url(r"^lists/new$", "lists.views.new_list", name="new_list")
]
```

调整 URL 映射中使用的正则表达式，加入一个“捕获组”（capture group）（.+），它能匹配随后的 / 之前任意个字符。捕获得到的文本会作为参数传入视图。

进行测试，可以发现错误。问题很容易修正，在 views.py 中加入一个参数即可，现在，前面那个预期失败解决了。

接下来要让视图决定把哪些待办事项传入模板：

```python
def view_list(request, list_id):
    list_ = List.objects.get(id = list_id)
    items = Item.objects.filter(list=list_)
    return render(request, "list.html", {"items": items})
```

#### 6.8.2 按照新设计调整 `new_list` 视图

现在得到另一个错误，进行相应修改，可以发现 `NewListTest` 还没有按照清单和待办事项的新设计调整，它应该检查视图是否重定向到新建清单的 URL。

```python
    def test_redirects_after_POST(self):
        """
        测试在发送 POST 请求后是否会重定向
        :return:
        """
        response = self.client.post("/lists/new", data={"item_text": "A new list item"})
        new_list = List.objects.first()

        self.assertEqual(response.status_code, 302, "希望返回 302 代码, 然而却返回了 {}".format(response.status_code))
        self.assertEqual(response["location"], "/lists/{unique_url}/".format(unique_url=new_list.id))
        self.assertRedirects(response, "/lists/{unique_url}/".format(unique_url=new_list.id))  # 等价于上面两条
```

接着修改视图本身，把它改为重定向到有效的地址。

```python
def new_list(request):
    list_ = List.objects.create()
    Item.objects.create(text=request.POST["item_text"], list_attr=list_)
    return redirect("/lists/{unique_url}/".format(unique_url=list_.id))
```

这样修改之后单元测试就可以通过了。进行功能测试，发现了一个回归。现在每个 POST 请求都会新建一个清单，破坏了向一个清单中添加多个待办事项的功能。

### 6.9 还需要一个视图，把待办事项加入现有清单

还需要一个 URL 和视图，把新待办事项添加到现有的清单中。

```python
class NewItemTest(TestCase):
    def test_can_save_a_POST_request_to_an_existing_list(self):
        """
        测试发送一个 POST 请求后能够发送到正确的表单之中
        :return:
        """
        other_list = List.objects.create()
        correct_list = List.objects.create()

        self.client.post("/lists/{unique_url}/add_item".format(unique_url=correct_list.id),
                         data={"item_text": "A new item for an existing list"})

        self.assertEqual(Item.objects.count(), 1)
        new_item = Item.objects.first()
        self.assertEqual(new_item.text, "A new item for an existing list")
        self.assertEqual(new_item.list, correct_list)

    def test_redirects_to_list_view(self):
        """
        测试添加完事项后会回到显示表单的 html
        :return:
        """
        other_list = List.objects.create()
        correct_list = List.objects.create()

        response = self.client.post(
            "/lists/{unique_url}/add_item".format(unique_url=correct_list.id),
            data={"item_text": "A new item for an existing list"}
        )

        self.assertRedirects(response, "/lists/{unique_url}/".format(unique_url=correct_list.id))
```

测试得到两个错误，一个是 `0 != 1`，另一个是 `301 != 302`。

#### 6.9.1 小心霸道的正则表达式

还没在 URL 映射中加入 `/lists/1/add_item`，应该得到 `404 != 302` 错误。怎么会是永久重定向响应（301）？

得到这个错误是因为在 URL 映射中使用了一个非常霸道的正则表达式：

`url(r"^lists/(.+)/$", "lists.views.view_list", name="view_list")`

根据 Django 的内部处理机制，如果访问的 URL 几乎正确，但却少了末尾的斜线，就会得到一个永久重定向响应（301）。在这里，`lists/1/add_item` 符合 `lists/(.+)/` 的匹配模式，其中 `(.+)` 捕获 `1/add_item`，然后 Django 猜测你其实是想访问末尾到斜线的 URL。

这个问题的修正方法是，显示指定 URL 模式只捕获数字，即在正则表达式中使用 `\d`

测试后的结果得到 404 错误了。

#### 6.9.2 最后一个新 URL

下面定义一个新 URL，用于把新待办事项添加到现有清单中：

```python
urlpatterns = [
    # url(r'^admin/', admin.site.urls),
    url(r"^$", "lists.views.home_page", name="home"),
    url(r"^lists/(\d+)/$", "lists.views.view_list", name="view_list"),
    url(r"^lists/(\d+)/add_item$", "lists.views.add_item", name="add_item"),
    url(r"^lists/new$", "lists.views.new_list", name="new_list")
]
```

现在 URL 映射中定义了三个类似的 URL。这三个 URL 看起来需要重构。

#### 6.9.3 最后一个新视图

```python
def add_item(request):
    pass
```

测试有所进展，接着修改：

```python
def add_item(request, list_id):
    pass
```

可以从 `new_list` 视图中复制 redirect，从 `view_list` 视图中复制 List.objects.get：

```python
def add_item(request, list_id):
    list_ = List.objects.get(id=list_id)
    Item.objects.create(text=request.POST["item_text"], list_attr=list_)
    return redirect("/lists/{unique_url}/".format(unique_url=list_id))
```

这样，测试又能通过了。

#### 6.9.4 如何在表单中使用那个 URL

现在只需在 list.html 模板中使用这个 URL。打开模板，修改表单标签：

```html
<form method="POST" action="/lists/{{ list.id }}/add_item">
```

为了能这样写，视图要把清单传入模板。下面在 `ListViewTest` 中新建一个单元测试办法：

```python
def test_passes_correct_list_to_template(self):
    other_list = List.objects.create()
    correct_list = List.objects.create()
    
    response = self.client.get("/lists/{}/".format(correct_list.id))
   	self.assertEqual(response.context["list"], correct_list)
```

response.context 表示要传入 render 函数的上下文——Django 测试客户端把上下文附在 response 对象上，方便测试。增加这个测试后得到的结果如下：

`KeyError: 'list'`

这是因为没把 list 传入模板，趁机简化视图：

```python
def view_list(request, list_id):
    list_ = List.objects.get(id=list_id)
    return render(request, "list.html", {"list": list_})
```

显然这么做会导致测试失败，因为模板期望传入的是 items。

可以在 list.html 中修正这个问题，同时还要修改表单 POST 请求的目标地址，即 action 属性。

```html
<form method="POST" action="/lists/{{ list.id }}/add_item">
  {% for item in list.item_set.all %}
  	<tr><td>{{ forloop.counter }}: {{ item.text }}</td></tr>
  {% endfor %}
</form>
```

`.item_set` 叫做反向查询（reverse lookup），是 Django 提供的非常有用的 ORM 功能，可以在其他表中查询某个对象的相关记录。修改模板之后，单元测试能通过了。功能测试同时也过了。

```shell
git diff
git commmit -am "new URL + view for adding to existing lists. FT passes :-)"
```

### 6.10 使用 URL 引入做最后一次重构

