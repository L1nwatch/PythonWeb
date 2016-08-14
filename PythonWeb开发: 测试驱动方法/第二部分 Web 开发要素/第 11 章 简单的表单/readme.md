## 第 11 章 简单的表单

Django 鼓励使用表单类验证用户的输入，以及选择显示错误消息。

### 11.1 把验证逻辑移到表单中

> 在 Django 中，视图很复杂就说明有代码异味。你要想，能否把逻辑移到表单或模型类的方法中，或者把业务逻辑移到 Django 之外的模型中？

Django 中的表单功能很多很强大：

* 可以处理用户输入，并验证输入值是否有错误
* 可以在模板中使用，用来渲染 HTML input 元素和错误消息
* 某些表单甚至还可以把数据存入数据库

你可以自己编写表单的 HTML，或者自己处理数据存储，但表单是放置验证逻辑的绝佳位置。

#### 11.1.1 使用单元测试探索表单 API

我们要在一个单元测试中实验表单的用法。计划是逐步迭代，最终得到一个完整的解决方案。

首先，新建一个文件，用于编写表单的单元测试。先编写一个测试方法，检查表单的 HTML：

```python
# test_forms.py
from django.test import TestCase
from lists.forms import ItemForm

class ItemFormTest(TestCase):
    def test_form_renders_item_text_input(self):
        form = ItemForm()
        self.fail(form.as_p())
```

`form.as_p()` 的作用是把表单渲染成 HTML。这个单元测试用 `self.fail` 探索性编程。在 `manage.py shell` 会话中探索编程也很容易，不过每次修改代码之后都要重新加载。

下面编写一个极简的表单，继承自基类 Form，只有一个字段 `item_text`：

```python
# forms.py
from django import forms

class ItemForm(forms.Form):
    item_text = forms.CharField()
```

运行测试后会看到一个失败消息，告诉我们自动生成的表单 HTML 是什么样的。

自动生成的 HTML 已经和 base.html 中的表单 HTML 很接近了，只不过没有 placeholder 属性和 Bootstrap 的 CSS 类。再编写一个单元测试方法，检查 placeholder 属性和 CSS 类：

```python
# test_forms.py
class ItemFormTest(TestCase):
    def test_form_item_input_has_placeholder_and_css_classes(self):
        form = ItemForm()
        self.assertIn('placeholder="Enter a to-do item"', form.as_p())
        self.assertIn('class="form-control input-lg"', form.as_p())
```

这个测试会失败，表明我们需要真正地编写一些代码了。使用 widget 参数，加入 placeholder 属性的方法如下：

```python
class ItemForm(forms.Form):
    item_text = forms.CharField(widget=forms.fields.TextInput(attrs={"placeholder":"Enter a to-do item","class":"form-control input-lg"}))
```

如果表单中的内容很多或者很复杂，使用 widget 参数定制很麻烦，此时可以借助 `django-crispy-forms` 和 `django-floppyforms`。

> 开发驱动测试：使用单元测试探索性编程
>
> 探索新 API 时，可以完全先抛开规则的束缚，然后再回到严格的 TDD 流程中。你可以使用交互式终端，或者编写一些探索性代码。现在我们只是使用单元测试试验表单 API，这是学习如何使用 API 的好方法。

#### 11.1.2 换用 Django 中的 ModelForm 类

我们希望表单重用已经在模型中定义好的验证规则。Django 提供了一个特殊的类，用来自动生成模型的表单，这个类是 ModelForm。我们要使用一个特殊的属性 Meta 配置表单：

```python
# forms.py
from django import forms
from list.models import Item

class ItemForm(forms.models.ModelForm):
    class Meta:
        model = Item
        fields = ("text")
```

我们在 Meta 中指定这个表单用于哪个模型，以及要使用哪些字段。

ModelForm 很智能，能完成各种操作，例如为不同类型的字段生成合适的 input 类型，以及应用默认的验证。详情参见[文档](https://docs.djangoproject.com/en/1.7/topics/forms/modelforms/)。

现在表单的 HTML 不一样了，placeholder 属性和 CSS 类都不见了，而且 `name="item_text" 变成了 name="text"`。这些变化能接受，但普通的输入框变成了 `textarea`，这可不是应用 UI 想要的效果。ModelForm 的字段也能使用 widget 参数定制：

```python
# forms.py
class ItemForm(forms.model.ModelForm):
    class Meta:
        model = Item
        fields = ("text", )
        widgets = {
          "text": forms.fields.TextInput(attrs={
            "placeholder": "Enter a to-do item",
              "class": "form-control input-lg"
          })
        }
```

定制后测试通过了。

#### 11.1.3 测试和定制表单验证

现在看一下 ModelForm 是否应用了模型中定义的验证规则。

```python
# test_forms.py
def test_form_validation_for_blank_items(self):
    form = ItemForm(data={"text":""})
    form.save()
```

测试的结果为 `ValueError`。

这样，如果提交空待办事项，表单不会保存数据。

现在看一下表单是否能显示指定的错误消息。在尝试保存数据之前检查验证是否通过的 API 是 `is_valid` 函数：

```python
# test_forms.py
    def test_form_validation_for_blank_items(self):
        form = ItemForm(data={"text": ""})
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors["text"], ["You can't have an empty list item"])
```

调用 `form.is_valid()` 得到的返回值是 `True 或 False`，不过还有个附带效果，即验证输入的数据，生成 erros 属性。erros 是个字典，把字段的名字映射到该字段的错误列表上（一个字段可以有多个错误）。

测试结果为：

```python
AssertionError: ['This field is required.'] != ["You can't have an empty list item"]
```

Django 已经为显示给用户查看的错误消息提供了默认值。急着开发 Web 应用的话，可以直接使用默认值。不过我们比较在意，想让错误消息特殊一些。定制错误消息可以修改 Meta 的另一个变量，`error_messages`：

```python
# forms.py
class Meta:
    model = Item
    fileds = ("text", )
    widgets = {"text": forms.fields.TextInput(attrs={"placeholder": "Enter a to-do item", "class":"form-control input-lg"})}
    error_messages = {
      "text" : {"required": "You can't have an empty list item"}
    }
```

然后测试即可通过。为了避免让这些错误消息搅乱代码，使用常量：

```python
# forms.py
EMPTY_LIST_ERROR = "You can't have an empty list item"
[...]

error_messages = {
  "text": {"required": EMPTY_LIST_ERROR}
}
```

再次运行测试，确认能通过。然后修改测试：

```python
# test_forms.py
from lists.forms import EMPTY_LIST_ERROR, ItemForm
[...]

def test_form_validation_for_blank_items(self):
    form = ItemForm(data={"text":""})
    self.assertFalse(form.is_valid())
    self.assertEqual(form.errors["text"], [EMPTY_LIST_ERROR])
```

修改之后测试仍能通过，就可以提交了：

```shell
git status
git add lists
git commit -m "new form for list items"
```

### 11.2 在视图中使用这个表单

精益理论中的“尽早部署”有个推论，即“尽早合并代码”。也就是说，编写表单可能要花很多时间，不断添加各种功能——做了各种工作，得到一个功能完善的表单类，但发布应用后才发现大多数功能实际并不需要。

因此，要尽早使用新编写的代码。这么做能避免编写用不到的代码，还能尽早在现实的环境中检验代码。

编写一个表单类，它可以渲染一些 HTML，而且至少能验证一种错误。既然可以在 base.html 模板中使用这个表单，那么在所有视图中都可以使用。

#### 11.2.1 在处理 GET 请求的视图中使用这个表单

首先修改视图的单元测试，使用 Django 测试客户端编写两个新测试代替原来的 `test_home_page_returns_correct_html` 和 `test_root_url_resolves_to_home_page_view`。但先不删除这两个旧测试方法，以便确保新编写的测试和旧测试等效：

```python
# test_views.py
from lists.forms import ItemForm

class HomePageTest(TestCase):
    def test_root_url_resolves_to_home_page_view(self):
        [...]
        
    def test_home_page_returns_correct_html(self):
        request = HttpRequest()
        [...]
        
    def test_home_page_renders_home_template(self):
        response = self.client.get("/")
        self.assertTemplateUsed(response, "home.html") # 使用辅助方法 assertTemplateUsed 替换之前手动测试模板的 diamante
        
    def test_home_page_uses_item_form(self):
        response = self.client.get("/")
        self.assertIsInstance(response.context["form"], ItemForm) # 使用 assertIsInstance 确认视图使用的是正确的表单类
```

测试结果为 `KeyError`。

因此，要在首页视图中使用这个表单：

```python
# views.py
from lists.forms import ItemForm
from lists.models import Item, List

def home_page(request):
    return render(request, "home.html", {"form": ItemForm()})
```

下面尝试在模板中使用这个表单——把原来的 `<input ..>` 替换成 `{{ form.text }}`：

```html
<!-- base.html -->
<form method="POST" action="{% block form_action %}{% endblock %}">
  {{ form.text }}
  {% csrf_token %}
  <div class="form-group has-error">
    ...
  </div>
</form>
```

`{{ form.text }}` 只会渲染这个表单中的 text 字段，生成 HTML input 元素。

现在，那两个旧测试过时了。但是失败消息不易读，把它变得清晰一些：

```python
# test_views.py
class HomePageTest(TestCase):
    maxDiff = None # 默认情况下会解决较长的差异，需要进行设置
    [...]
    def test_home_page_returns_correct_html(self):
        request = HttpRequest()
        response = home_page(request)
        expected_html = render_to_string("home.html")
# 对比长字符串时 assertMultiLineEqual 很有用，它会以差异的格式显示输出
        self.assertMultiLineEqual(response.content.decode(), excepted_html)
```

再次测试，可以看到测试失败的原因是 `render_to_string` 函数不知道怎么处理表单。

可以修正这个问题：

```python
# test_views.py
def test_home_page_returns_correct_html(self):
    request = HttpRequest()
    response = home_page(request)
    expected_html = render_to_string("home.html", {"form": ItemForm()})
    self.assertMultiLineEqual(response.content.decode(), expected_html)
```

修改之后测试又能通过了。确定添加新测试前后的表现一致后，可以删除那两个旧测试方法了。

新测试方法中的 `assertTemplateUsed` 和 `response.context` 对一个处理 GET 请求的简单视图而言足够了。

现在 HomePageTest 类中只有两个测试方法了。

#### 11.2.2 大量查找和替换

前面修改了表单，id 和 name 属性的值变了。运行功能测试时会看到，首次尝试查找输入框时测试失败了。

得修正这个问题，为此需要大量查找和替换。在此之前先提交，把重命名和逻辑变动区分开。

```shell
git diff 
git commit -am "use new form in home_page, simplify tests. NB breaks stuff"
```

下面来修正功能测试。通过 grep 命令可以得知，有很多地方都使用了 `id_new_item`。

```shell
grep id_new_item functional_tests/test*
```

这表明我们要重构。在 `base.py` 中定义一个新辅助办法：

```python
# base.py
class FunctionalTest(StaticLiveServerCase):
    [...]
    def get_item_input_box(self):
        return self.browser.find_element_by_id("id_text")
```

然后所有需要替换的地方都使用这个辅助方法——`test_simple_list_creation.py` 修改三处，`test_layout_and_styling.py` 修改两处，`test_list_item_validation.py` 修改四处。

第一步完成了，接下来还要修改应用代码。要找到所有旧的 id(`id_new_item`) 和 name(`item_text`)，分别替换成 `id_text` 和 text：

```shell
grep -r id_new_item lists/
```

只要改动一处，使用类似的方法查看 name 出现的位置：

```shell
grep -Ir item_text lists
```

改完之后再运行单元测试及功能测试，确保一切仍能正常运行。

不能通过功能测试，确认一下发生错误的位置——查看其中一个失败所在的行号，会发现，每次提交第一个待办事项后，清单页面都不会显示输入框。

查看 views.py 和 `new_list` 视图后找到了原因——如果检测到有验证错误，根本就不会把表单传入 `home.html` 模板：

```python
# views.py
except ValidationError:
    error = "You can't have an empty list item"
    return render(request, "home.html", {"error":error})
```

我们也想在这个视图中使用 ItemForm 表单。继续修改之前，先提交：

```shell
git status
git commit -am "rename all item input ids and names. still broken"
```

### 11.3 在处理 POST 请求的视图中使用这个表单

现在要调整 `new_list` 视图的单元测试，更确切地说，要修改针对验证的那个测试方法。

```python
# test_views.py
class NewListTest(TestCase):
    [...]
    
    def test_validation_errors_are_sent_back_to_home_page_template(self):
        response = self.client.post("/lists/new", data={"text":""})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "home.html")
        expected_error = escape("You can't have an empty list item")
        self.assertContains(response, expected_error)
```

#### 11.3.1 修改 `new_list` 视图的单元测试

首先，这个测试方法测试的内容太多了。我们应该把这个测试方法分成两个不同的断言：

* 如果有验证错误，应该渲染首页模板，并且返回 200 响应
* 如果有验证错误，响应中应该包含错误信息

此外，还可以添加一个新断言：

* 如果有验证错误，应该把表单对象传入模板

不用硬编码错误消息字符串，而要使用一个常量：

```python
# test_views.py
from lists.forms import ItemForm, EMPTY_LIST_ERROR
[...]

class NewListTest(TestCase):
    [...]
    
    def test_for_invalid_input_renders_home_template(self):
        response = self.client.post("/lists/new", data={"text": ""})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "home.html")

    def test_validation_errors_are_shown_on_home_page(self):
        response = self.client.post("/lists/new", data={"text": ""})
        self.assertContains(response, escape(EMPTY_LIST_ERROR))

    def test_for_invalid_input_passes_form_to_template(self):
        response = self.client.post("/lists/new", data={"text": ""})
        self.assertIsInstance(response.context["form"], ItemForm)
```

现在好多了，每个测试方法只测试一件事。如果幸运的话，只有一个测试会失败，而且会告诉我们接下来做什么：

```shell
python3 manage.py test lists
```

#### 11.3.2 在视图中使用这个表单

```python
# views.py
def new_list(request):
    # 把 request.POST 中的数据传给表单的构造方法
    form = ItemForm(data=request.POST)

    # 使用 form.is_valid() 判断提交是否成功
    if form.is_valid():
        list_ = List.objects.create()
        Item.objects.create(text=request.POST["text"], list_attr=list_)
        return redirect(list_)
    else:
        # 如果提交失败，把表单对象传入模板，而不显示一个硬编码的错误消息字符串
        return render(request, "home.html", {"form": form})
```

#### 11.3.3 使用这个表单在模板中显示错误消息

测试失败的原因是模板还没使用这个表单显示错误消息：

```html
<!-- base.html -->
<form method="POST" action="{% block form_action %}{% endblock %}">
  {{ form.text }}
  {% csrf_token %}
  {% if form.erros %} <!-- form.errors 是一个列表，包含这个表单中的所有错误 -->
  <div class="form-group has-error"> 
    <div class="help-block">
      {{ form.text.errors }}<!-- form.text.erros 也是一个列表，但只包含 text 字段的错误 -->
    </div>
  </div>
  {% endif %}
</form>
```

这样修改之后，失败发生在针对最后一个视图 `view_list` 的测试中。因为我们修改了错误在模板中显示的方式，不再显示手动传入模板的错误。

因此，还要修改 `view_list` 视图才能重新回到可运行状态。

### 11.4 在其他视图中使用这个表单

`view_list` 视图既可以处理 GET 请求也可以处理 POST 请求。先测试 GET 请求，为此，可以编写一个新测试方法：

```python
# test_views.py
class ListViewTest(TestCase):
    [...]
    
    def test_displays_item_form(self):
        list_ = List.objects.create()
        response = self.client.get("/lists/{}/".format(list_.id))
        self.assertIsInstance(response.context["form"], ItemForm)
        self.assertContains(response, 'name="text"')
```

解决这个问题最简单的方法如下：

```python
# views.py
def view_list(request, list_id):
    [...]
    
    form = ItemForm()
    return render(request, "list.html", {
      "list":list_, "form":form, "error":error
    })
```

接下来要在另一个视图中使用这个表单的错误消息，把当前针对表单提交失败的测试（`test_validation_errors_end_up_on_lists_page`）分成多个测试方法：

```python
class ListViewTest(TestCase):
    [...]
    
    def post_invalid_input(self):
        list_ = List.objects.create()
        return self.client.post("/lists/{}/".format(list_.id), data={"text": ""})

    def test_for_invalid_input_nothing_saved_to_db(self):
        self.post_invalid_input()
        self.assertEqual(Item.objects.count(), 0)

    def test_for_invalid_input_renders_list_template(self):
        response = self.post_invalid_input()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "list.html")

    def test_for_invalid_input_passes_form_to_template(self):
        response = self.post_invalid_input()
        self.assertIsInstance(response.context["form"], ItemForm)

    def test_for_invalid_input_shows_error_on_page(self):
        response = self.post_invalid_input()
        self.assertContains(response, escape(EMPTY_LIST_ERROR))
```

我们定义了一个辅助方法 `post_invalid_input`，这样就不用在分拆的四个测试中重复编写代码了。

现在，试试能否使用 ItemForm 表单重写视图。第一次尝试：

```python
# views.py
def view_list(request, list_id):
    list_ = List.objects.get(id=list_id)
    form = ItemForm()
    if request.method == "POST":
        form = ItemForm(data=request.POST)
        if form.is_valid():
            Item.objects.create(text=request.POST["text"], list=list_)
            return redirect(list_)
    return render(request, "list.html", {"list_attr":list_, "form":form})
```

重写后，单元测试和功能测试都通过了。

现在是提交的绝佳时刻：

```shell
git diff
git commit -am "use form in all views, back to working state"
```

### 11.5 使用表单自带的 save 方法

我们还可以进一步简化视图。表单可以把数据存入数据库。我们遇到的情况并不能直接保存数据，因为需要知道把待办事项保存到哪个清单中。

先编写测试，先看一下如果直接调用 `form.save()` 会发生什么：

```python
# test_forms.py
def test_form_save_handles_saving_to_a_list(self):
    form = ItemForm(data={"text":"do me"})
    new_item = form.save()
```

Django 报错了，因为待办事项必须隶属于某个清单。

这个问题的解决办法是告诉表单的 save 方法，应该把待办事项保存到哪个清单中：

```python
from lists.models import Item, List
[...]

    def test_form_save_handles_saving_to_a_list(self):
        list_ = List.objects.create()
        form = ItemForm(data={"text":"do me"})
        new_item = form.save(for_list=list_)
        self.assertEqual(new_item, Item.objects.first())
        self.assertEqual(new_item.text, "do me")
        self.assertEqual(new_item.list_attr, list_)
```

然后，要保证待办事项能顺利存入数据库，而且各个属性的值都正确，可以定制 save 方法，实现方式如下：

```python
# forms.py
    def save(self, for_list):
        self.instance.list_attr = for_list
        return super().save()
```

 表单的 `.instance` 属性是将要修改或创建的数据库对象。此外还有很多方法，例如自己手动创建数据库对象，或者调用 `save()` 方法时指定参数 `commit=False`，但作者觉得使用 `.instance` 属性最简洁。

最后，要重构视图。先重构 `new_list`：

```python
# views.py
def new_list(request):
    form = ItemForm(data=request.POST)
    if form.is_valid():
        list_ = List.objects.create()
        form.save(for_list=list_)
        return redirect(list_)
   	else:
        return render(request, "home.html", {"form": form})
```

然后运行测试，确保都能通过。接着重构 `view_list`：

```python
# views.py
def view_list(request, list_id):
    list_ = List.objects.get(id=list_id)
    form = ItemForm()

    if request.method == "POST":
        form = ItemForm(data=request.POST)
        if form.is_valid():
            form.save(for_list=list_)
            return redirect(list_)
    return render(reuqest, "list.html", {"list":list_, "form":form})
```

修改之后，单元测试和功能测试都能通过。

现在这两个视图更像是“正常的” Django 视图了：从用户的请求中读取数据，结合一些定制的逻辑或 URL 中的信息(`list_id`)，然后把数据传入表单进行验证，如果通过验证就能保存数据，最后重定向或者渲染模板。

> 小贴士
>
> * 简化视图
>
>   如果发现视图很复杂，要编写很多测试，这时候就应该考虑是否能把逻辑移到其他地方。可以移到表单中。或者可以移到模型类的自定义方法中。如果应用本身就很复杂，可以把核心业务逻辑移到 Django 专属的文件之外，编写单独的类和函数
>
> * 一个测试只测试一件事
>
>   如果一个测试中不止一个断言，你就要怀疑这么写是否合理。有时候断言之间联系紧密，可以放在一起。不过第一次编写测试时往往都会测试很多表现，其实应该把它们分成多个测试。辅助函数有助于简化拆分后的测试。