## 第 10 章 输入验证和测试的组织方式

### 10.1 针对验证的功能测试：避免提交空待办事项

下面是一个功能测试的大纲：

```python
# functional_tests/tests.py
def test_cannot_add_empty_list_items(self):
    # Y 访问首页，不小心提交了一个空待办事项
    # 输入框中没输入内容，她就按下了回车键
    
    # 首页刷新了，显示一个错误消息
    # 提示待办事项不能为空
    
    # 她输入一些文字，然后再次提交，这次没问题了
    
    # 她有点儿调皮，又提交了一个空待办事项
    
    # 在清单页面她看到了一个类似的错误消息
    
    # 输入文字之后就没问题了
    self.fail("write me!")
```

在继续之前，要把功能测试分成多个文件，每个文件只放一个测试方法。

还要编写一个测试基类，让所有测试类都继承这个基类。

#### 10.1.1 跳过测试

重构时最好能让整个测试组件都通过。刚才故意编写了一个失败测试，现在要使用 unittest 提供的修饰器 @skip 临时禁止这个测试方法：

```python
# functional_tests/tests.py
from unittest import skip
[...]

@skip
def test_cannot_add_empty_list_items(self):
    [...]
```

这个修饰器告诉测试运行程序，忽略这个测试。再次运行功能测试就会看到这么做起作用了，因为测试组件仍能通过：

```shell
python manage.py test functional_tests
```

> 跳过测试很危险，把改动提交到仓库之前需要删掉 @skip 修饰器。这就是逐行审查差异的目的。

#### 10.1.2 把功能测试拆分到多个文件中

先把各个测试方法放在单独的类中，但仍然保存在同一文件里：

```python
# functional_tests/tests.py
class FunctionTest(StaticLiveServerCase):
    @classmethod
    def setUpClass(cls):
        [...]
    
    @classmethod
    def tearDownClass(cls):
        [...]
        
    def setUp(self):
        [...]
        
    def tearDown(self):
        [...]
        
    def check_for_row_in_list_table(self, row_text):
        [...]
        
class NewVisitorTest(FunctionalTest):
    def test_can_start_a_list_and_retrieve_it_later(self):
        [...]
        
class LayoutAndStylingTest(FunctionalTest):
    def test_layout_and_styling(self):
        [...]
        
class ItemValidationTest(FunctionalTest):
    @skip
    def test_cannot_add_empty_list_items(self):
        [...]
```

然后运行功能测试，看是否仍能通过。

现在分拆这个测试文件，一个类写入一个文件，而且还有一个文件用来保存所有测试类都继承的基类。

```shell
base.py
test_simple_list_creation.py
test_layout_and_styling.py
test_list_item_validation.py
```

base.py 只需保留 FunctionalTest 类，其他代码全部删掉。留下基类中的辅助方法，因为在新的功能测试中会用到。

```python
# base.py
import sys
from selenium import webdriver
from django.contrib.staticfiles.testing import StaticLiveServerTestCase

class FunctionalTest(StaticLiveServerTestCase):
    @classmethod
    def setUpClass(cls):
		[...]

    def setUp(self):
		[...]

    def tearDown(self):
		[...]

    def check_for_row_in_list_table(self, row_text):
		[...]
```

```python
# test_simple_list_creation.py
from .base import FunctionalTest # .base 居然还有这样的
from selenium import webdriver
from selenium.webdriver.common.keys import Keys

class NewVisitorTest(FunctionalTest):
    def test_can_start_a_list_and_retrieve_it_later(self):
        [...]
```

用到了相对导入（from .base），有些人喜欢在 Django 应用中大量使用这种导入方式（例如，视图可能会使用 from .models import List 导入模型，而不用 from list.models）。只有十分确定要导入的文件位置不会变化时，才使用相对导入。

针对布局和样式的功能测试：

```python
# test_layout_and_styling.py
from .base import FunctionalTest

class LayoutAndStylingTest(FunctionalTest):
    [...]
```

针对用户输入的测试：

```python
# test_list_item_validation.py
from unittest import skip
from .base import FunctionalTest

class ItemValidationTest(FunctionalTest):
    @skip
    def test_cannot_add_empty_list_items(self):
        [...]
```

可以再次执行 `manage.py test functional_tests` 命令，确保一切偶读正常，还要确认所有三个测试都运行了。

#### 个人实践

自己跑测试的时候报了这么一个错误：

`SystemError: Parent module '' not loaded, cannot perform relative import`

结果[网上一搜](https://www.google.com/url?sa=t&rct=j&q=&esrc=s&source=web&cd=1&cad=rja&uact=8&ved=0ahUKEwj4yIj-zLnOAhUCkZQKHbkQCu8QFgghMAA&url=http%3A%2F%2Fstackoverflow.com%2Fquestions%2F16981921%2Frelative-imports-in-python-3&usg=AFQjCNEK5T_myZBBgUFgcdL9sYrdvQ4KGQ)还是不要这样写了，还是自己设置源路径吧。

#### 10.1.3 运行单个测试文件

拆分之后有个附带的好处——可以运行单个测试文件，如下所示：

```python
python3 manage.py test functional_tests.test_list_item_validation
```

#### 10.1.4 填充功能测试

```python
    def test_cannot_add_empty_list_items(self):
        # Y 访问首页，不小心提交了一个空待办事项
        # 输入框中没输入内容，她就按下了回车键
        self.browser.get(self.server_url)
        self.browser.find_element_by_id("id_new_item").send_keys("\n")

        # 首页刷新了，显示一个错误消息
        # 提示待办事项不能为空
        # 指定使用 Bootstrap 提供的 CSS 类 .has-error 标记错误文本。Bootstrap 为这种消息提供了很多有用的样式。
        error = self.browser.find_element_by_css_selector(".has-error")
        self.assertEqual(error.text, "You can't have an empty list item")

        # 她输入一些文字，然后再次提交，这次没问题了
        self.browser.find_element_by_id("id_new_item").send_keys("Buy milk\n")
        self.check_for_row_in_list_table("1: Buy milk")

        # 她有点儿调皮，又提交了一个空待办事项
        self.browser.find_element_by_id("id_new_item").send_keys("\n")

        # 在清单页面她看到了一个类似的错误消息
        self.check_for_row_in_list_table("1: Buy milk")
        error = self.browser.find_element_by_css_selector(".has-error")
        self.assertEqual(error.text, "You can't have an empty list item")

        # 输入文字之后就没问题了
        self.browser.find_element_by_id("id_new_item").send_keys("Make tea\n")
        self.check_for_row_in_list_table("1: Buy milk")
        self.check_for_row_in_list_table("2: Make tea")
```

### 10.2 使用模型层验证

在 Django 中有两个地方可以执行验证：一个是模型层；另一个是表单层。只要可能，作者更倾向于使用地层验证。一方面是数据库和数据库完整性规则，另一方面是因为在这一层执行验证更安全——有时你会忘记使用哪个表格验证输入，但使用的数据库不会变。

#### 10.2.1 重构单元测试，分拆成多个文件

要为模型编写一个新测试，但在此之前，先要使用类似于功能测试的整理方法整理单元测试。两者之间有个区别，因为 lists 应用中既有应用代码也有测试代码，所以要把测试放到单独的文件夹中：

```shell
mkdir lists/tests
touch lists/tests/__init__.py
git mv lists/tests.py lists/tests/test_all.py
git status
git add lists/tests
python3 manage.py test lists
git commit -m "Move unit tests into a folder with single file"
```

```
**个人实践**
移动之后我的 PyCharm 自己产生了 `__init__.py` 文件，然后运行测试失败了。后来发现得把 `todo_app` 中的 `__init__.py` 删除才能成功，否则会报这么一个错误：`ImportError: No module named 'todo_app.lists'`。话说 `tests/__init__.py` 这个文件是要存在的，别乱删了。

另外，由于自己修改了 settings.py，需要重写自动化部署的脚本。现在发现这么一个问题：
start: Job is already running: gunicorn-watch0.top
说是已经在运行了，所以要杀死这个进程：
ps -ef | grep gunicron
sudo kill pid
之后再尝试重新部署，发现这东西居然会自动运行啊，杀完之后马上就又开始运行了。解决思路是删掉 /etc/init/gunicorn-watch0.top 文件后重启，果然可以了，然后测试自动化部署，居然直接就成功了。
```

现在把 `test_all.py` 分成两个文件：一个名为 `test_views.py`，只包含视图测试，另一个名为 `test_models.py`。

```shell
git mv lists/tests/tests_all.py lists/tests/test_views.py
cp lists/tests/test_views.py lists/tests/test_models.py
```

然后清理 `test_models.py`，只留下一个测试方法，所以导入的模块也更少了：

```python
from django.test import TestCase
from lists.models import Item, List

class ListAndItemModelsTest(TestCase):
    [...]
```

而 `test_views.py` 只减少了一个类。

再次运行测试，确保一切正常。之后就可以提交了。

```shell
git add lists/tests
git commit -m "Split out unit tests into two files"
```

> 有些人喜欢项目一开始就把单元测试放在一个测试文件夹中，而且还多建一个文件，`test_forms.py`。这种做法很棒。

#### 10.2.2 模型验证的单元测试和 `self.assertRaises` 上下文管理器

要在 ListAndItemModelsTest 中添加一个新测试方法，尝试创建一个空待办事项：

```python
    def test_cannot_save_empty_list_items(self):
        list_ = List.objects.create()
        item = Item(list_attr=list_, text="")
        # 这是一个新的单元测试技术，如果想检查做某件事是否会抛出异常，可以使用 self.assertRaises 上下文管理器。
        # 此处还可写成：
        # try:
        #     item.save()
        #     self.fail("The save should have raised an exception")
        # except ValidationError:
        #     pass
        with self.assertRaises(ValidationError):
            item.save()
```

不过使用 with 语句更简洁。现在运行测试，看着它失败。

#### 10.2.3 Django 怪异的表现：保存时不验证数据

遇到了一个 Django 的一个怪异表现。测试本来应该通过的。阅读 [Django 模型字段的文档](https://docs.djangoproject.com/en/1.7/ref/models/fields/#blank)之后，发现 TextField 的默认设置是 `blank=False`，也就是说文本字段应该拒绝空值。

但是为什么测试失败？由于[历史原因](https://groups.google.com/forum/ #!topic/django-developers/uIhzSwWHj4c)，保存数据时 Django 的模型不会运行全部验证。在数据库中实现的约束，保存数据时都会抛出异常，但 SQLite 不支持文本字段上的强制控制约束，所以我们调用 save 方法时无效值悄无声息地通过了验证。

有种方法可以检查约束是否会在数据层执行：如果在数据层制定约束，需要执行迁移才能应用约束。但是，Django 知道 SQLite 不支持这种约束，所以如果运行 makemigrations，会看到消息说没事可做：

```python
python3 manage.py makemigrations
No changes detected
```

不过，Django 提供了一个方法用于运行全部验证，即 `full_clean`。下面把这个方法加入测试，看看是否有用：

```python
with self.assertRaises(ValidationError):
    item.save()
    item.full_clean()
```

加入之后，测试就通过了。

如果忘了需求，把 text 字段的约束条件设为 `blank=True`，测试可以提醒我们。

### 10.3 在视图中显示模型验证错误

下面尝试在视图中处理模型验证，并把验证错误传入模板，让用户看到。在 HTML 中有选择地显示错误可以使用这种方法——检查是否有错误变量传入模板，如果有就在表单下方显示出来：

```html
<!-- base.html -->
<form method="POST" action="{% block form_action %}{% endblock %}">
  <input name="item_text" id="id_new_item" class="form-control input-lg" placeholder="Enter a to-do item"/>
  {% csrf_token %}
  {% if error %}
  <div class="form-group has-error">
    <span class="help-block">{{ error }}</span>
  </div>
  {% endif %}
</form>
```

关于表单控件的更多信息可以[参阅 Bootstrap 文档](http://getbootstrap.com/css/#forms)。

把错误传入模板是视图函数的任务。这里有两种稍微不同的错误处理模式。

在第一种情况中，新建清单视图有可能渲染首页所用的模板，而且还会显示错误消息。单元测试如下：

```python
class NewListTest(TestCase):
    [...]
    
    def test_validation_errors_are_sent_back_to_home_page_template(self):
        response = self.client.post("/lists/new", data={"item_text": ""})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "home.html")
        excepted_error = "You can't have an empty list item"
        self.assertContains(response, excepted_error)
```

编写这个测试时，我们手动输入了字符串形式的地址 `/lists/new`，你可能有点反感。我们之前在测试、视图和模板中硬编码了多个地址，这么做有违 DRY 原则。稍后会重构这些地址。

再看测试，现在测试无法通过，因为现在视图返回 302 重定向，而不是正常的 200 响应。我们在视图中调用 `full_clean()` 试试：

```python
# views.py
def new_list(request):
    list_ = List.objects.create()
    item = Item.objects.create(text=request.POST["item_text"], list=list_)
    item.full_clean()
    return redirect("/lists/{}/".format(list_.id,))
```

现在模型验证会抛出异常，并且传到了视图中：

```python
django.core.exceptions.ValidationError: {'text': ['This field cannot be blank.']}
```

下面使用第一种错误处理方案：使用 `try/except` 检测错误。加入 `try/except` 之后，测试结果又变成了 `302 != 200` 错误。

下面把 pass 改成渲染模板，这么改还兼具检查模板的功能：

```python
# views.py
except ValidationError:
    return render(request, "home.html")
```

现在测试告诉我们，要把错误消息写入模板。为此，可以传入一个新的模板变量：

```python
# views.py
except ValidationError:
    error = "You can't have an empty list item"
    return render(request, "home.html", {"error": error})
```

不过，看样子没什么用，可以让视图输出一些信息以便调试：

```python
excepted_error = "You can't have an empty list item"
print(response.content.decode())
self.assertContains(response, excepted_error)
```

从输出的信息中可以知道，失败的原因是 [Django 转义了 HTML 中的单引号](https://docs. djangoproject.com/en/1.7/topics/templates/#automatic-html-escaping)。

所以可以在测试中硬编码写入：

`excepted_error = "You can&#39;t have an empty list item"`

但是使用 Django 提供的辅助函数更好一些：

```python
# test_views.py
from django.utils.html import escape
[...]
	expected_error = escape("You can't have an empty list item")
    self.assertContains(response, expected_error)
```

测试通过了。

#### 确保无效的输入值不会存入数据库

继续做其他事情之前，注意我们之前存在逻辑错误。就是即使验证失败仍会创建对象：

```python
# views.py
def new_list(request):
    list_ = List.objects.create()
    item = Item.objects.create(text=request.POST["item_text"], list_attr=list_)
    try:
        item.full_clean()
    except ValidationError:
        [...]
```

要添加一个新单元测试，确保不会保存空待办事项：

```python
# test_views.py
    def test_invalid_list_items_arent_saved(self):
        self.client.post("/lists/new", data={"item_text": ""})
        self.assertEqual(List.objects.count(), 0)
        self.assertEqual(List.objects.count(), 0)
```

修正的方法如下：

```python
# views.py
try:
    item.full_clean()
    item.save()
except ValidationError:
    list_.delete()
    error = "..."
    return render ...
[...]
```

单元测试过了，但是通能测试却失败了。

```shell
python3.4 manage.py test functional_tests.test_list_item_validation
```

注意分析测试结果，可以看出，功能测试的第一部分通过了，但是第二次提交空待办事项也要显示错误消息才行。

可以做个提交了：

```shell
git commit -am "Adjust new list view to do model validation"
```

### 10.4 Django 请求：在渲染表单的视图中处理 POST 请求

这一次要使用的处理方式，是 Django 中十分常用的模式：在渲染表单的视图中处理该视图接收到的 POST 请求。这么做虽然不太符合 REST 架构的 URL 规则，却有个很大的好处：同一个 URL 既可以显示表单，又可以显示处理用户输入过程中遇到的错误。

现在的状况是，显示清单用一个视图和 URL，处理新建清单中的待办事项用另一个视图和 URL。要把这两种操作合并到一个视图和 URL 中。所以，在 list.html 中，表单的提交目标地址要改一下：

```html
{% block form_action %}/lists/{{ list.id }}/{% endblock %}
```

不小心又硬编码了一个 URL，回想一下，在 home.html 中也有一个。

修改之后功能测试随即失败，因为 `view_list` 视图还不知道如何处理 POST 请求。

> 本节要进行一次应用层的重构。在应用层中重构时，要先修改或增加单元测试，然后再调整代码。使用功能测试检查重构是否完成，以及一切能否像重构前一样正常运行。

#### 10.4.1 重构：把 `new_item` 实现的功能移到 `view_list` 中

NewItemTest 类中的测试用于检查把 POST 请求中的数据保存到现有的清单中，把这些测试全部移到 ListViewTest 类中，还要把原来的请求目标地址 `/lists/%d/add_item` 改成显示清单的 URL：

```python
# test_views.py
class ListViewTest(TestCase):
    [...]
    
    def test_can_save_a_POST_request_to_an_existing_list(self):
        """
        测试发送一个 POST 请求后能够发送到正确的表单之中
        :return:
        """
        other_list = List.objects.create()
        correct_list = List.objects.create()

        self.client.post("/lists/{unique_url}/".format(unique_url=correct_list.id),
                         data={"item_text": "A new item for an existing list"})

        self.assertEqual(Item.objects.count(), 1)
        new_item = Item.objects.first()
        self.assertEqual(new_item.text, "A new item for an existing list")
        self.assertEqual(new_item.list_attr, correct_list)

    def test_POST_redirects_to_list_view(self):
        """
        测试添加完事项后会回到显示表单的 html
        :return:
        """
        other_list = List.objects.create()
        correct_list = List.objects.create()

        response = self.client.post(
            "/lists/{unique_url}/".format(unique_url=correct_list.id),
            data={"item_text": "A new item for an existing list"}
        )

        self.assertRedirects(response, "/lists/{unique_url}/".format(unique_url=correct_list.id))
```

注意，整个 NewItemTest 类都没有了。而且还修改了重定向测试方法的名字，明确表明只适用于 POST 请求。

然后修改 `view_list` 函数，处理两种请求类型：

```python
# views.py
def view_list(request, list_id):
    list_ = List.objects.get(id=list_id)
    if request.method == "POST":
        Item.objects.create(text=request.POST["item_text"], list_attr=list_)
        return redirect("/lists/{}/".format(list_.id))
    return render(request, "list.html", {"list_attr": list_})
```

修改之后测试通过了，现在可以删除 `add_item` 视图了，因为不再需要了。删除之后，还要在 urls.py 中删除引用。这样单元测试就能通过了。

接下来运行功能测试，可以看到仍然是重构之前的失败。说明重构 `add_item` 功能的任务完成了。此时应该提交代码了：

```shell
git commit -am "Refactor list view to handle new item POSTs"
```

> 这里破坏了“有测试失败时不重构“这个规则。不过这里是因为若想使用新功能必须重构。如果有单元测试失败，决不能重构。如果喜欢看到一个干净的测试结果，可以在这个功能测试方法加上 @skip 修饰器。

#### 10.4.2 在 `view_list` 视图中执行模型验证

把待办事项添加到现有清单时，我们希望保存数据时仍能遵守制定好的模型验证规则。为此要编写一个新单元测试，和首页的单元测试差不多：

```python
class ListViewTest(TestCase):
    [...]
    
    def test_validation_erros_end_up_on_lists_page(self):
        """
        测试在一个清单上添加一个空项目
        :return:
        """
        list_ = List.objects.create()
        response = self.client.post("/lists/{}/".format(list_.id), data={"item_text": ""})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "list.html")
        expected_error = escape("You can't have an empty list item")
        self.assertContains(response, expected_error)
```

这个测试应该失败，因为视图现在还没做任何验证，只是重定向所有 POST 请求。

在视图中执行验证的方法如下：

```python
# views.py
def view_list(request, list_id):
    list_ = List.objects.get(id=list_id)
    error = None

    if request.method == "POST":
        try:
            # 注意这里不是 Item.objects.create()
            item = Item(text=request.POST["item_text"], list_attr=list_)
            item.full_clean()
            item.save()
            return redirect("/lists/{}/".format(list_.id))
        except ValidationError:
            error = "You can't have an empty list item"
    return render(request, "list.html", {"list_attr": list_, "error": error})
```

这里确实有一些重复的代码，views.py 中出现了两次 `try/except` 语句，一般来说不好看。

进行测试，测试通过了。

> 制定“事不过三，三则重构”这个规则的原因之一是，只有遇到三次且每次都稍有不同时，才能更好地提炼出通用功能。如果过早重构，得到的代码可能并不适用于第三次。

这里功能测试又可以通过了。

又回到了可正常运行的状态，因此可以提交了。

```shell
git commit -am "enforce model validation in list view"
```

### 10.5 重构：去除硬编码的 URL

还记得 urls.py 中 name= 参数的写法么？直接从 Django 生成的默认 URL 映射中复制过来，然后又给它们起了有意义的名字。现在要查明这些名字有什么用。

```python
# urls.py
url(r"^(\d+)/$", "lists.views.view_list", name="view_list"),
url(r"^new$", "lists.views.new_list", name="new_list")
```

#### 10.5.1 模板标签 `{% url %}`

可以把 home.html 中硬编码的 URL 换成一个 Django 模板标签，再引用 URL 的“名字”：

```html
{% block form_action %}{% url "new_list" %}{% endblock %}
```

然后确认改动之后不会导致单元测试失败。

继续修改其他模板。传入了一个参数的这个：

```html
{% block form_action %}{% url "view_list" list_attr.id %}{% endblock %}
```

详情阅读 Django 文档中对 URL 反向解析的[介绍](https://docs.djangoproject.com/en/1.7/ topics/http/urls/#reverse-resolution-of-urls)。再次运行测试，确保都能通过。

之后就做次提交吧：

```shell
git commit -am "Refactor hard-coded URLs out of templates"
```

#### 10.5.2 重定向时使用 `get_absolute_url`

下面处理 views.py。在这个文件中去除硬编码的 URL，可以使用和模板一样的方法——写入 URL 的名字和一个位置参数。

```python
def new_list(request):
    [...]
    return redirect("view_list", list_.id)
```

修改之后单元测试和功能测试仍能通过，但是 redirect 函数的作用远比这强大。在 Django 中，每个模型对象都对应一个特定的 URL，因此可以定义一个特殊的函数，命名为 `get_absolute_url`，其作用是获取显示单个模型对象的页面 URL。这个函数在这里很有用，在 Django 管理后台也很有用：在后台查看一个对象时可以直接跳到前台显示该对象的页面。如果有必要，总是建议在模型中定义 `get_absolute_url` 函数。

先在 `test_models.py` 中编写一个单元测试：

```python
# test_models.py
def test_get_absolute_url(self):
    list_ = List.objects.create()
    self.assertEqual(list_.get_absolute_url(), "/lists/{}".format(list_.id))
```

测试失败。

实现这个函数时要使用 Django 中的 reverse 函数。reverse 函数的功能和 Django 对 urls.py 所做的操作相反，[参见文档](https://docs.djangoproject.com/en/1.7/topics/http/ urls/#reverse-resolution-of-urls)。

```python
# models.py
from django.core.urlresolvers import reverse

class List(models.Model):
    def get_absolute_url(self):
        return reverse("view_list", args=[self.id])
```

现在可以在视图中使用 `get_absolute_url` 函数了，只需把重定向的目标对象传给 `redirect` 函数即可，`redirect` 函数会自动调用 `get_absolute_url` 函数（**个人实践：函数名固定得是 `get_absolute_url`，要不然测试通不过**）。

```python
# views.py
def new_list(request):
    [...]
    return redirect(list_)
```

更多信息参见 [Django 文档](https://docs.djangoproject.com/en/1.7/topics/http/shortcuts/#redirect)。可以确认一下单元测试是否仍能通过。

然后使用同样的方法修改 `view_list` 视图：

```python
# views.py
def view_list(request, list_id):
    [...]
    
    	item.save()
        return redirect(list_)
    except ValidationError:
        error = "..."
```

分别运行全部单元测试和工嗯呢该测试，确保一切仍能正常工作。

之后就可以做一次提交了：

```shell
git commit -am "Use get_absolute_url on List model to DRY urls in views"
```

> 关于组织测试和重构的小贴士
>
> * 把测试放在单独的文件夹中
>
>   就像使用多个文件保存应用代码一样，也应该把测试放到多个文件中。
>
>   * 使用一个名为 tests 的文件夹，在其中添加 `__init__.py` 文件，导入所有测试类。
>   * 对功能测试来说，按照特定功能或用户故事的方式组织。
>   * 对单元测试来说，针对一个源码文件的测试放在一个单独的文件中。在 Django 中，往往有 `test_models.py`、`test_views.py` 和 `test_forms.py`。
>   * 每个函数和类都至少有一个占位测试。
>
> * 别忘了 “遇红/变绿/重构” 中的 “重构”
>
>   编写测试的主要目的是让你重构代码！一定要重构，尽量把代码变得简洁。
>
> * 测试失败时别重构
>
>   * 一般情况下如此
>   * 不算正在处理的功能测试
>   * 如果测试的对象还没实现，可以先在测试方法加上 @skip 修饰器
>   * 更一般的做法是，记下想重构的地方，完成手头上的活，等应用处于可正常运行的状态时再重构
>   * 提交代码之前别忘了删掉所有 @skip 修饰器！你应该始终逐行审查差异，找出这种问题。

