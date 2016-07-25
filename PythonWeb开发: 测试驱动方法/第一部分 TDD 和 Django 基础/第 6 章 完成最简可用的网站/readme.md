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