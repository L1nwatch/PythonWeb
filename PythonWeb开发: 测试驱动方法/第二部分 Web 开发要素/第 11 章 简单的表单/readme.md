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

