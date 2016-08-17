## 第 12 章 高级表单

### 12.1 针对重复待办事项的功能测试

在 `ItemValidationTest` 类中再添加一个测试方法：

```python
# test_list_item_validation.py
def test_cannot_add_duplicate_items(self):
    # Y 访问首页，新建一个清单
    self.browser.get(self.server_url)
    self.get_item_input_box().send_keys("Buy wellies\n")
    self.check_for_row_in_list_table("1: Buy wellies")
    
    # 她不小心输入了一个重复的待办事项
    self.get_item_input_box().send_keys("Buy wellies\n")
    
    # 她看到一条有帮助的错误消息
    self.check_for_row_in_list_table("1: Buy wellies")
    error = self.browser.find_element_by_css_selector(".has-error")
    self.assertEqual(error.text, "You've already got this in your list")
```

接下来运行测试：

```python
python3 manage.py test functional_tests.test_list_item_validation
```

可以看到两个测试中的第一个现在可以通过。如果只运行那个失败的测试，可以这么做：

```shell
python3 manage.py test functional_tests.test_list_item_validation.ItemValidationTest.test_cannot_add_duplicate_items
```

#### 12.1.1 在模型层禁止重复

编写一个新测试，检查同一个清单中有重复的待办事项时是否抛出异常：

```python
# test_models.py
    def test_duplicate_items_are_invalid(self):
        list_ = List.objects.create()
        Item.objects.create(list_attr=list_, text="bla")
        with self.assertRaises(ValidationError):
            item = Item(list_attr=list_, text="bla")
            item.full_clean()
```

此外，还要再添加一个测试，确保完整性约束不要做过头了

```python
# test_models.py
    def test_CAN_save_same_item_to_different_lists(self):
        list1 = List.objects.create()
        list2 = List.objects.create()
        Item.objects.create(list_attr=list1, text="bla")
        item = Item(list_attr=list2, text="bla")
        item.full_clean()  # 不该抛出异常
```

如果想故意出错，可以这么做：

```python
# models.py
class Item(models.Mode):
    text = models.TextField(default="", unique=True)
    list = models.ForeignKey(List, default=None)
```

这么做可以确认第二个测试确实能检测到这个问题。

> * 何时测试开发者犯下的错误	
>   * 测试时要判断何时应该编写测试确认我们没有犯错。一般而言，做决定时要谨慎。
>   * 这里，编写测试确认无法把重复的待办事项存入同一个清单。目前，让这个测试通过最简单的办法（即编写的代码量最少）是，让表单无法保存任何重复的待办事项。此时，就要编写另一个测试，因为我们编写的代码可能有错。
>   * 但是，不可能编写测试检查出所有可能出错的方式。

模型和 ModelForm 一样，也能使用 class Meta。在 Meta 类中可以实现一个约束，要求清单中的待办事项必须是唯一的。也就是说，text 和 list 的组合必须是唯一的。

```python
# models.py
class Item(models.Model):
    text = models.TextField(default="")
    list = modesl.ForeignKey(List, default=None)
    
    class Meta:
        unique_together = ("list", "text")
```

此时，你可能想快速浏览一遍 Django 文档中对模型属性 Meta 的[说明](https://docs.djangoproject/)。

#### 12.1.2 题外话：查询集合排序和字符串表示形式

运行测试，会看到一个意料之外的测试。

> 根据所用系统和 SQLite 版本的不同，你可能看不到这个错误。

失败消息有点晦涩，可以通过输出一些信息来方便调试：

```python
first_saved_item = saved_items[0]
print(first_saved_item.text)
second_saved_item = saved_items[1]
print(second_saved_item.text)
self.assertEqual(first_saved_item.text, "The first (ever) list item")
```

分析测试结果，可以知道唯一性约束干扰了查询（例如 Item.objects.all()）的默认排序。虽然现在仍有测试失败，但最好添加一个新测试明确测试排序：

```python
# test_models.py
def test_list_ordering(self):
    list1 = List.objects.create()
    item1 = Item.objects.create(list=list1, text="i1")
    item2 = Item.objects.create(list=list1, text="item 2")
    item3 = Item.objects.create(list=list1, text="3")
    self.assertEqual(
    	Item.objects.all(),
        [item1, item2, item3]
    )
```

测试的结果多了一个失败，而且也不易读。

我们的对象需要一个更好的字符串表示形式。下面再添加一个单元测试：

> 如果已经有测试失败，还要再添加更多的失败测试，通常都要三思而后行，因为这么做会让测试的输出变得更复杂，而且往往你都会有所担心回不去正常运行的状态。

```python
# test_models.py
def test_string_representation(self):
    item = Item(text="some text")
    self.assertEqual(str(item), "some text")
```

连同另外两个失败，现在开始一并解决：

```python
# models.py
class Item(models.Model):
    [...]
    
    def __str__(self):
        return self.text
```

现在只剩两个测试失败了，而且排序测试的失败消息更易读了。

可以在 class Meta 中解决这个问题：

```python
# models.py
    class Meta:
        ordering = ("id",)
        unique_together = ("text", "list_attr")
```

从测试结果中可以看到，顺序是一样的，只不过测试没分清。因为 Django 中的查询集合不能喝列表正确比较。可以在测试中把查询集合转换成列表，解决这个问题：

```python
# test_models.py
        # 也可以考虑使用 unittest 中的 assertSequenceEqual, 以及 Django 测试工具箱中的 assertQuerysetEqual
        self.assertEqual(
            list(Item.objects.all()),
            [item1, item2, item3]
        )
```

这样就可以了，整个测试组件都能通过。

#### 12.1.3 重写旧模型测试

现在要重写模型测试。借此机会介绍 Django ORM。删除 `test_saving_and_retrieving_items`，换成：

```python
# test_models.py
class ListAndItemModelsTest(TestCase):
    def test_default_text(self):
        item = Item()
        self.assertEqual(item.text, "")

    def test_item_is_related_to_list(self):
        list_ = List.objects.create()
        item = Item()
        item.list_attr = list_
        item.save()
        self.assertIn(item, list_.item_set.all())
    
    [...]
```

初始化一个全新的模型对象，检查属性的默认值，这么做足以确认 models.py 中是否正确设定了一些字段。`test_item_is_related_to_list` 其实是双重保险，确认外键关联是否正常。

顺便，还要把这个文件中的内容分成专门针对 Item 和 List 的测试。

```python
# test_models.py
class ItemModelTest(TestCase):
    def test_default_text(self):
        [...]

class ListModelTest(TestCase):
    def test_get_absolute_url(self):
        [...]
```

修改之后单元测试全部通过了。

#### 12.1.4 保存时确实会显示完整性错误

保存数据时会出现一些数据完整性错误，是否出现完整性错误完全取决于完整性约束是否由数据库执行。

执行 `makemigrations` 命令试试，你会看到，Django 除了把 `unique_together` 作为应用层约束之外，还想把它加到数据库中：

```python
python3 manage.py makemigrations
```

现在，修改检查重复待办事项的测试，把 `.full_clean` 改成 `.save`。

```python
    def test_duplicate_items_are_invalid(self):
        list_ = List.objects.create()
        Item.objects.create(list_attr=list_, text="bla")
        with self.assertRaises(ValidationError):
            item = Item(list_attr=list_, text="bla")
            # item.full_clean()
            item.save()
```

可以发现测试出错了。错误是由 SQLite 导致的，而且错误类型也和我们期望的不一样，我们想得到的是 ValidationError，实际却是 IntegrityError。

把改动改回去，让测试全部通过。然后提交对模型层的修改：

```shell
git status
mv lists/migrations/0005_auto* lists/migrations/0005_list_item_unique_together.py
git add lists
git diff --staged
git commit -am "Implement duplicate item validation at model layer"
```

### 12.2 在视图层试验待办事项重复验证

运行功能测试，看到浏览器窗口一闪而过，网站现在处于 500 状态之中（服务器错误）。简单地修改视图单元测试应该能解决这个问题：

```python
# test_views.py
class ListViewTest(TestCase):
    [...]
    
    def test_for_invalid_input_shows_error_on_page(self):
        [...]
        
    def test_duplicate_item_validation_errors_end_up_on_lists_page(self):
        list1 = List.objects.create()

        item1 = Item.objects.create(list_attr=list1, text="textey")
        response = self.client.post("/lists/{}".format(list1.id), data={"text": "textey"})

        expected_error = escape("You've already got this in your list")
        self.assertContains(response, expected_error)
        self.assertTemplateUsed(response, "list.html")
        self.assertEqual(Item.objects.all().count(), 1)
```

测试结果出现完整性错误，理想情况下，希望在尝试保存数据之前调用 `is_valid` 时，已经注意到有重复。不过，在此之前，表单必须知道待办事项属于哪个清单。

现在暂时为这个测试加上 @skip 修饰器。

### 12.3 处理唯一性验证的复杂表单

新建清单的表单只需要知道一件事，即新待办事项的文本。验证清单中的待办事项是否唯一，表单需要知道使用哪个清单以及待办事项的文本。这一次要重定义表单的构造方法，让它知道待办事项属于哪个清单。

复制前一个表单的测试，稍微做些修改：

```python
# test_forms.py
from lists.forms import (
	DUPLICATE_ITEM_ERROR, EMPTY_LIST_ERROR,
    ExistingListItemForm, ItemForm
)
[...]

class ExistingListItemFormTest(TestCase):
    def test_form_renders_item_text_input(self):
        list_ = List.objects.create()
        form = ExistingListItemForm(for_list=list_)
        self.assertIn('placeholder="Enter a to-do item"', form.as_p())

    def test_form_validation_for_blank_items(self):
        list_ = List.objects.create()
        form = ExistingListItemForm(for_list=list_, data={"text": ""})
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors["text"], [EMPTY_LIST_ERROR])

    def test_form_validation_for_duplicate_items(self):
        list_ = List.objects.create()
        Item.objects.create(list_attr=list_, text="no twins!")
        form = ExistingListItemForm(for_list=list_, data={"text": "no twins!"})
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors["text"], [DUPLICATE_ITEM_ERROR])
```

要经历几次 TDD 循环，最终得到了这么一个构造方法：

```python
# forms.py
DUPLICATE_ITEM_ERROR = "You've already got this in your list"
[...]
class ExistingListItemForm(forms.models.ModelForm):
    def __init__(self, for_list, *args, **kwargs):
        super().__init__(*args, **kwargs)
```

测试的结果为：

```python
ValueError: ModelForm has no model class specified.
```

现在，让这个表单继承现有的表单，看测试能不能通过：

```python
class ExistingListItemForm(ItemForm):
    def __init__(self, for_list, *args, **kwargs):
        super().__init__(*args, **kwargs)
```

现在只剩下一个测试失败了。接下来了解一点 Django 内部运作机制。你可以阅读 Django 文档中对[模型验证](https://docs.djangoproject.com/en/1.7/ref/models/instances/#validating-objects)和[表单验证](https://docs.djangoproject.com/en/1.7/ref/forms/validation/)的介绍了解。

Django 在表单和模型中都会调用 `validate_unique` 方法，借助 instance 属性在表单的 `validate_unique` 方法中调用模型的 `validate_unique` 方法：

```python
# forms
from django.core.exceptions import ValidationError
[...]

class ExistingListItemForm(ItemForm):
    def __init__(self, for_list, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.instance.list = for_list

    def validate_unique(self):
        try:
            self.instance.validate_unique()
		except ValidationError as e:
                e.error_dict = {"text":[DUPLICATE_ITEM_ERROR]}
                self._update_errors(e)
```

这段代码先获取验证错误，修改错误消息之后再把错误传回表单。任务完成，做个简单的提交：

```shell
git diff
git commit -a
```

### 12.4 在清单视图中使用 `ExistingListItemForm`

现在看一下能否在视图中使用这个表单。要删掉测试方法的 `@skip` 修饰器，与此同时还要使用常量清理测试。

```python
# test_views.py
from lists.forms import (
	DUPLICATE_ITEM_ERROR, EMPTY_LIST_ERROR,
    ExistingListItemForm, ItemForm,
)
[...]

def test_duplicate_item_validation_errors_end_up_on_lists_page(self):
    [...]
    expected_error = escape(DUPLICATE_ITEM_ERROR)
```

修改之后完整性错误又出现了：

```python

```









