## 第 19 章 测试隔离和 "倾听测试的心声"

在复杂的应用中，选择放任失败单元测试不管进入下一层是很危险的。尚未确定高层是否真正完成之前就进入低层是一种冒险行为。

确保各层之间相互隔离确实需要投入更多的经历（以及更多可怕的驭件），可是这么做能促使我们得到更好的设计。

### 19.1 重温抉择时刻：视图层依赖于尚未编写的模型代码

回到以前的代码，看一下使用隔离性更好的测试效果如何：

```shell
git checkout -b more-isolation # 为这次实验新建一个分支
git reset --hard revisit_this_point_with_isolated_tests
```

回到原来那个错误，接下来尝试使用解决办法如下：

```python
# lists/views.py
def new_list(request):
    form = ItemForm(data=request.POST)
    if form.is_valid():
        list_ = List()
        list_.owner = request.user
        list_.save()
        form.save(for_list=list_)
        return redirect(list_)
    else:
        return render(request, "home.html", {"form": form})
```

此时，这个视图测试是失败的，因为还没有编写模型层。

### 19.2 首先尝试使用驭件实现隔离

清单还没有属主，但可以使用一些模拟技术让视图测试认为有属主：

```python
# lists/tests/test_views.py
from unittest.mock import Mock, patch
from django.http import HttpRequest
from django.test import TestCase

@patch("lists.views.List") # 模拟 List 模型的功能，获取视图创建的任何一个清单
def test_list_owner_is_saved_if_user_is_authenticated(self, mockList):
    mock_list = List.objects.create() # 为视图创建一个真实的 List 对象。List 对象必须真实，否则视图尝试保存 Item 对象时会遇到外键错误(表明这个测试只是部分隔离)
    mock_list.save = Mock()
    mockList.return_value = mock_list
    request = HttpRequest()
    request.user = User.objects.create() # 给 requests 对象赋值一个真实的用户
    request.POST["text"] = "new list item"
    new_list(request)
    self.assertEqual(mock_list.owner, request.user) # 现在可以声明断言，判断清单对象是否设定了 .owner 属性
```

现在运行测试，可以通过了。

> 使用驭件有个局限，必须按照特定的方式使用 API。这是使用驭件对象要作出的妥协之一。

#### 使用驭件的 `side_effect` 属性检查事件发生的顺序

这个测试的问题是，无意中把代码写错也可能侥幸通过测试。所以，不仅要检查指定了属主，还要确保在清单对象上调用 save 方法之前就已经指定了。

使用驭件检查事件发生顺序的方法如下，可以模拟一个函数，作为侦件，检查调用这个侦件时周围的状态：

```python
# lists/tests/test_views.py
@patch("lists.views.List")
def test_list_owner_is_saved_if_user_is_authenticated(self, mockList):
    mock_list = List.objects.create()
    mock_list.save = Mock()
    mockList.return_value = mock_list
    request = HttpRequest()
    request.user = Mock()
    request.user.is_authenticated.return_value = True
    request.POST["text"] = "new list item"
    
	def check_owner_assigned(): # 定义一个函数，在这个函数中就希望先发生的事件声明断言，即检查是否设定了清单的属主
    	self.assertEqual(mock_list.owner, request.user)
    mock_list.save.side_effect = check_owner_assigned # 把这个检查函数赋值给后续事件的 side_effect 属性。当视图在驭件上调用 save 方法时，才会执行其中的断言。要保证在测试的目标函数调用前完成此次赋值
    new_list(request)
    mock_list.save.assert_called_once_with() # 最后，要确保设定了 side_effect 属性的函数一定会被调用，也就是要调用 .save() 方法。否则断言永远不会运行
```

> 使用驭件的副作用时有两个常见错误：第一，side_effect 属性赋值太晚，也就是在调用测试目标函数之后才赋值；第二，忘记检查是否调用了引起副作用的函数。

现在，如果使用有错误的代码，即指定属主和调用 save 方法的顺序不对，就会看到失败消息，它先尝试保存，然后才执行 `side_effect` 属主对应的函数。

### 19.3 倾听测试的心声：丑陋的测试表明需要重构

这个测试视图告诉我们，视图做的工作太多了，既要创建表单，又要创建清单对象，还要决定是否保存清单的属主。

可以把一部分工作交给表单类完成，把视图变得简单且易于理解一些。

### 19.4 以完全隔离的方式重写视图测试

首次尝试为这个视图编写的组件集成度太高，数据库层和表单层的功能完成之后才能通过。现在使用另一种方式，提高测试的隔离度。

#### 19.4.1 为了新测试的健全性，保留之前的整合测试组件

把 NewListTest 类重命名为 NewListViewIntegratedTest，再把尝试使用驭件保存属主的测试代码删掉，换成整合版本，而且暂时为这个测试方法加上 skip 修饰器：

```python
# lists/tests/test_views.py
import unittest

class NewListViewIntegratedTest(TestCase):
    def test_saving_a_POST_request(self):
        [...]

    @unittest.skip
    def test_list_owner_is_saved_if_user_is_authenticated(self):
        request = HttpRequest()
        request.user = User.objects.create(email="a@b.com")
        request.POST["text"] = "new list item"
        new_list(request)
        list_ = List.objects.first()
        self.assertEqual(list_.owner, request.user)
```

> 集成测试（integration test)

从头开始编写测试，看看隔离测试能否驱动新写出来的 `new_list` 视图的替代版本。

#### 19.4.3 站在协作者的角度思考问题

重写测试时若想实现完全隔离，必须丢掉以前对测试的认识。视图的主要协作者是表单对象。所以，为了完全掌握表单，以及按照想要的方式定义表单的功能，使用驭件模拟表单。

```python
# lists/tests/test_views.py
from lists.views import new_list, new_list2

@patch("lists.views.NewListForm")  # 模拟 NewListForm 类。类中的所有测试方法都会用到这个驭件，所以在类上模拟
# 使用 Django 提供的 TestCase 类太容易写成整合测试。为了确保写出纯粹隔离的单元测试，只能使用 unittest.TestCase
class NewListViewUnitTest(unittest.TestCase):
    def setUp(self):
        self.request = HttpRequest()
        self.request.POST["text"] = "new list item"  # 在 setUp 方法中手动创建了一个简单的 POST 请求，没有使用(太过整合的) Django 测试客户端

    def test_passes_POST_data_to_NewListForm(self, mockNewListForm):
        new_list2(self.request)
        # 然后检查视图要做的第一件事：在视图中使用正确的构造方法初始化它的协作者，即 NewListForm，传入的数据从请求中读取
        mockNewListForm.assert_called_once_with(data=self.request.POST)
```

在这个测试的结果中首先会看到一个失败消息，报错视图中还没有 NewListForm。

于是先编写一个占位表单类。

```python
# lists/views.py
from lists.forms import NewListForm
[...]

# lists/forms.py
class NewListForm:
    pass
```

接下来根据失败消息进行代码编写：

```python
# lists/views.py
def new_list2(request):
    NewListForm(data=request.POST)
```

测试通过了，接下来继续编写测试。如果表单中的数据有效，要在表单对象上调用 save 方法：

```python
# lists/tests/test_views.py
@patch("lists.views.NewListForm")
class NewListViewUnitTest(unittest.TestCase):
    def setUp(self):
        self.request = HttpRequest()
        self.request.POST["text"] = "new list item"
        self.request.user = Mock()
        
	def test_passes_POST_data_to_NewListForm(self, mockNewListForm):
        new_list2(self.request)
        mockNewListForm.assert_called_once_with(data=self.request.POST)
        
	def test_saves_form_with_owner_if_form_valid(self, mockNewListForm):
        mock_form = mockNewListForm.return_value
        mock_form.is_valid.return_value = True
        new_list2(self.request)
        mock_form.save.assert_called_once_with(owner=self.request.user)
```

据此，可以写出如下视图：

```python
# lists/views.py
def new_list2(request):
    form = NewListForm(data=request.POST)
    form.save(owner=request.user)
```

如果表单中的数据有效，让视图做一个重定向，可以把我们带到一个页面，查看表单刚刚创建的对象。所以，要模拟视图的另一个协作者——redirect 函数：

```python
# lists/tests/test_views.py
@patch("lists.views.redirect") # 模拟 redirect 函数，这次直接在方法上模拟
def test_redirects_to_form_returned_object_if_form_valid(self, mock_redirect, mockNewListForm): # patch 修饰器先应用最内层的那个，所以这个驭件在 mockNewListForm 之前传入方法
    mock_form = mockNewListForm.return_value
    mock_form.is_valid.return_value = True # 指定测试的是表单中数据有效的情况
    
    response = new_list2(self.request)

    self.assertEqual(response, mock_redirect.return_value) # 检查视图的响应是否为 redirect 函数的结果
    mock_redirect.assert_called_once_with(mock_form.save.return_value) # 然后检查调用 redirect 函数时传入的参数是否为在表单上调用 save 方法得到的对象
```

据此，可以编写如下视图：

```python
# lists/views.py
def new_list2(request):
    form = NewListForm(data=request.POST)
    list_ = form.save(owner=request.user)
    return redirect(list_)
```

然后测试表单提交失败的情况——如果表单中的数据无效，渲染首页的模板：

```python
# lists/tests/test_views.py
@patch("lists.views.render")
def test_renders_home_template_with_form_if_form_invalid(self, mock_render, mockNewListForm):
    mock_form = mockNewListForm.return_value
    mock_form.is_valid.return_value = False
    response = new_list2(self.request)
    self.assertEqual(response, mock_render.return_value)
    mock_render.assert_called_once_with(self.request, "home.html", {"form": mock_form})
```

> 在驭件上调用断言方法时一定要运行测试，确认它会失败。因为输入断言函数时太容易出错，会导致调用的模拟方法没有任何作用

但是这里测试并不全面，如下的代码却可以通过测试：

```python
# lists/views.py
def new_list2(request):
    form = NewListForm(data=request.POST)
    list_ = form.save(owner=request.user)
    if form.is_valid():
        return redirect(list_)
    return render(request, "home.html", {"form": form})
```

于是再写一个测试来确保：

```python
# lists/tests/test_views.py
def test_does_not_save_if_form_invalid(self, mockNewListForm):
    mock_form = mockNewListForm.return_value
    mock_form.is_valid.return_value = False
    new_list2(self.request)
    self.assertFalse(mock_form.save.called)
```

最后可以得到一个精简的视图：

```python
# lists/views.py
def new_list2(request):
    form = NewListForm(data=request.POST)
    if form.is_valid():
        list_ = form.save(owner=request.user)
        return redirect(list_)
    return render(request, "home.html", {"form": form})
```

测试结果可以通过了。

### 19.5 下移到表单层

已经写好了视图函数，这个视图基于设想的表单 NewListForm，而且这个表单现在还不存在。

需要在表单对象上调用 save 方法创建一个新清单，还要使用通过验证的 POST 数据创建一个新待办事项。如果直接使用 ORM，save 方法可以写成这样：

```python
class NewListForm(models.Form):
    def save(self, owner):
        list_ = List()
        if owner:
            list_.owner = owner
        list_.save()
        item = Item()
        item.list = list_
        item.text = self.cleaned_data["text"]
        item.save()
```

这种实现方式依赖于模型层的两个类，即 Item 和 List。

隔离性好的测试应该这样写：

```python
class NewListFormTest(unittest.TestCase):
    # 为表单模拟两个来自下部模型层的协作者
    @patch("lists.forms.List") 
    @patch("lists.forms.Item")
    def test_save_creates_new_list_and_item_from_post_data(self, mockItem, mockList):
        mock_item = mockItem.return_value
        mock_list = mockList.return_value
        user = Mock()
        form = NewListForm(data={"text": "new item text"})
        form.is_valid() # 必须调用 is_valid 方法，这样表单才会把通过验证的数据存储到 .cleaned_data 字典中
        
        def check_item_text_and_list():
            self.assertEqual(mock_item.text, "new item text")
            self.assertEqual(mock_item.list, mock_list)
            self.assertTrue(mock_list.save.called)
		mock_item.save.side_effect = check_item_text_and_list # 使用 side_effect 方法确保保存新待办事项对象时，使用已经保存的清单，而且待办事项中的文本正确
		form.save(owner=user)
        self.assertTrue(mock_item.save.called) # 再次确认调用了副作用函数
```

但是这个测试写得好丑，需要优化。

#### 始终倾听测试的心声：从应用中删除 ORM 代码

Django ORM 很难模拟，而且表单类需要较深入地了解 ORM 的工作方式。

在 List 类中定义一个辅助函数，封装保存新清单及对象相关的第一个待办事项这一部分逻辑。先为这个想法写个测试：

```python
# lists/tests/test_forms.py
import unittest
from unittest.mock import patch, Mock
from django.test import TestCase
from lists.forms import (
	DUPLICATE_ITEM_ERROR, EMPTY_LIST_ERROR,
    ExistingListItemForm, ItemForm, NewListForm
)
from lists.models import Item, List
[...]

class NewListFormTest(unittest.TestCase):
    @patch("lists.forms.List.create_new")
    def test_save_creates_new_list_from_post_data_if_user_not_authenticated(self, mock_List_create_new):
        user = Mock(is_authenticated=lambda: False)
        form = NewListForm(data={"text": "new item text"})
        form.is_valid()
        form.save(owner=user)
        mock_List_create_new.assert_called_once_with(
        	first_item_text = "new item text"
        )
```

既然已经测试了这种情况，再写个测试检查用户已经通过认证的情况：

```python
# lists/tests/test_forms.py
@patch("lists.forms.List.create_new")
def test_save_creates_new_list_with_owner_if_user_authenticated(self, mock_List_create_new):
    user = Mock(is_authenticated=lambda: True)
    form = NewListForm(data={"text": "new item text"})
    form.is_valid()
    form.save(owner=user)
    mock_List_create_new.assert_called_once_with(
    	first_item_text="new item text", owner=user
    )
```

可以看出，这个测试易读多了。接下来开始实现：

```python
# lists/forms.py
from lists.models import Item, List
```

此时驭件说要定义一个占位的 `create_new` 方法。

```python
# lists/models.py
class List(models.Model):
    def get_absolute_url(self):
        return reverse("view_list", args=[self.id])
    
    def create_new():
        pass
```

接下来按照失败测试编写代码，最终代码：

```python
# lists/forms.py
class NewListForm(ItemForm):
    def save(self, owner):
        if owner.is_authenticated():
            List.create_new(first_item_text=self.cleaned_data["text"], owner=owner)
        else:
            List.create_new(first_item_text=self.cleaned_data["text"])
```

而且测试也通过了。

> #### 把 ORM 代码放到辅助方法中
>
> 从编写隔离测试的过程中，了解到“ORM 辅助方法”。
>
> 使用 Django 的 ORM 可以通过十分易读的句法（肯定比纯 SQL 好得多）快速完成工作。但有些人喜欢尽量减少应用中使用的 ORM 代码量，尤其不喜欢在视图层和表单层使用 ORM 代码。
>
> 一个原因是，测试这几层时更容易。另一个原因是，必须定义辅助方法，这样能更清晰地表示域逻辑。
>
> 辅助方法同样可用于读写查询。
>
> 定义辅助方法时，可以起个适当的名字，表明它们在业务逻辑中的作用。使用辅助方法不仅可以让代码的条理变得更清晰，还能把所有 ORM 调用都放在模型层，因此整个应用不同部分之间的耦合更松散。

### 19.6 下移到模型层

在模型层不用再编写隔离测试了，因为模型层的目的就是与数据库结合在一起工作，所以编写整合测试更合理：

```python
# lists/tests/test_models.py
class ListModelTest(TestCase):
    def test_get_absolute_url(self):
        list_ = List.objects.create()
        self.assertEqual(list_.get_absolute_url(), "/lists/{}/".format(list_.id))
	
    def test_create_new_creates_list_and_first_item(self):
        List.create_new(first_item_text="new item text")
        new_item = Item.objects.first()
        self.assertEqual(new_item.text, "new item text")
        new_list = List.objects.first()
        self.assertEqual(new_item.list_attr, new_list)
```

根据测试结果，可以编写实现方式如下：

```python
# lists/models.py
class List(models.Model):
    def get_absolute_url(self):
        return reverse("view_list", args=[self.id])
    
    @staticmethod
    edf create_new(first_item_text):
        list_ = List.objects.create()
        Item.objects.create(text=first_item_text, list_attr=list_)
```

 注意，一路走下来，直到模型层，由视图层和表单层驱动，得到了一个设计良好的模型，但是 List 模型还不支持属主。

现在，测试清单应该有一个属主。添加如下测试：

```python
# lists/tests/test_models.py
from django.contrib.auth import get_user_model
User = get_user_model()
[...]

def test_create_new_optionally_saves_owner(self):
    user = User.objects.create()
    List.create_new(first_item_text="new item text", owner=user)
    new_list = List.objects.first()
    self.assertEqual(new_list.owner, user)
```

再为 owner 属性编写一些测试：

```python
# lists/tests/test_models.py
class ListModelTest(TestCase):
    [...]
    
    def test_lists_can_have_owners(self):
        List(owner=User()) # 不该抛出异常
        
    def test_list_owner_is_optional(self):
        List().full_clean() # 不该抛出异常
```

这两个测试并没有保存对象，因为对这个测试而言，内存中有这些对象就行了。

> 尽量多用内存中（未保存）的模型对象，这样测试运行得更快。

依照测试结果，实现模型：

```python
# lists/models.py
from django.conf import settings
[...]

class List(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, blank=True, null=True)
    [...]
```

此时，测试的结果中有各种完整性失败，执行迁移后才能解决这些问题。

先处理由 `create_new` 方法导致的失败：

```python
# lists/models.py
@staticmethod
def create_new(first_item_text, owner=None):
    list_ = List.objects.create(owner=owner)
    Item.objects.create(text=first_item_text, list=list_)
```

#### 回到视图层

现在视图层以前的两个整合测试失败了。

原因是因为以前的视图没有分清谁才是清单的属主，修正这个问题：

```python
# lists/views.py
def new_list(request):
    form = ItemForm(data=request.POST)
    if form.is_valid():
        list_ = List()
        if request.user.is_authenticated():
            list_.owner = request.user
        list_.save()
        form.save(for_list=list_)
        return redirect(list_)
    else:
        return render(request, "home.html", {"form": form})
```

> 整合测试的好处之一，可以捕获这种无法轻易预测的交互。这里忘记编写测试检查用户没有通过验证的情况，可是整合测试会由上而下使用整个组件，最终模型层出现了错误。

现在测试全部通过。

### 19.7 关键时刻，以及使用模拟技术的风险

换掉以前的视图，使用新视图试试。调换视图可以在 `urls.py` 中完成：

```python
# lists/urls.py
url(r"^new$", "lists.views.new_list2", name="new_list")
```

还得删除整合测试类上的 `unittest.skip` 修饰器，而且在这个类中要使用新视图 `new_list2`，看看为清单属主编写的新代码是否真的可用：

```python
# lists/tests/test_views.py
# unittest.skip
    def test_list_owner_is_saved_if_user_is_authenticated(self):
        request = HttpRequest()
        request.user = User.objects.create(email="a@b.com")
        request.POST["text"] = "new list item"
        new_list2(request)
        list_ = List.objects.first()
        self.assertEqual(list_.owner, request.user)
```

测试结果很不妙。

测试隔离有个很重要的知识点：虽然它有可能帮助你为单独各层作出好的设计，但无法自动验证各层之间的集成情况。

上述结果表明，视图期望表单返回一个待办事项，但我们刚刚的代码没让表单返回任何值。 

### 19.8 把层与层之间的交互当做“合约”

除了隔离的单元测试之外，功能测试最终也能发现这个失误。但理想情况下，我们希望尽早得到反馈——功能测试可能要运行好几分钟。

理论上讲，有办法：把层与层之间的交互看成一种“合约”。只要模拟一层的行为，就要在心里记住，层与层之间现在有了隐形合约，这一层的驭件或许可以转移到下一层的测试中。

遗忘的合约如下所示：

```python
# lists/tests/test_views.py
@patch("lists.views.redirect")
def test_redirects_to_form_returned_object_if_form_valid(self, mock_redirect, mockNewListForm):
    mock_form = mockNewListForm.return_value
    mock_form.is_valid.return_value = True
    
    response = new_list2(self.request)
    
    self.assertEqual(response, mock_redirect.return_value)
    mock_redirect.assert_called_once_with(mock_form.save.return_value) # 模拟的 form.save 方法返回一个对象，我们希望在视图中使用这个对象。
```

#### 19.8.1 找出隐性合约

现在要审查 `NewListViewUnitTest` 类中的每隔测试，看看各驭件在隐性合约中表述了什么：

```python
# lists/tests/test_views.py
def test_passes_POST_data_to_NewListForm(self, mockNewListForm):
    [...]
    mockNewListForm.assert_called_once_with(data=self.request.POST) # 需要传入 POST 请求中的数据，以便初始化表单
def test_saves_form_with_owner_if_form_valid(self, mockNewListForm):
    mock_form = mockNewListForm.return_value
    mock_form.is_valid.return_value = True # 表单对象要能响应 is_valid() 方法，而且要根据输入值判断返回 True 还是 False
    new_list2(self.request)
    mock_form.save.assert_called_once_with(owner=self.request.user) # 表单对象要能响应 .save 方法，而且传入的参数值是 request.user，然后根据用户是否登录做相应处理
    
def test_does_not_save_if_form_invalid(self, mockNewListForm):
    [...]
    mock_forms.is_valid.return_value = False # 表单对象要能响应 is_valid() 方法，而且要根据输入值判断返回 True 还是 False
    [...]
    
@patch("lists.views.redirect")
def test_redirects_to_form_returned_object_if_form_valid(self, mock_redirect, mockNewListForm):
    [...]
    mock_redirect.assert_called_once_with(mock_form.save.return_value) # 表单对象的 .save 方法应该返回一个新清单对象，以便视图把用户重定向到显示这个对象的页面

def test_renders_home_template_with_form_if_form_invalid(
[...])
```

仔细分析表单测试，可以看出，其实只明确测试了第三点。第一点和第二点是 Django 中 ModelForm 的默认特性，而且针对父类 ItemForm 的测试涵盖了这两点。

> 使用由外而内的 TDD 技术编写隔离测试时，要记住每个测试在合约中对下一层应该实现的功能做出的隐含假设，而且记得稍后要回来测试这些假设。可以在便签上记下来，也可以使用 self.fail 编写占位测试。

#### 19.8.2 修正由于疏忽导致的问题

下面添加一个新测试，确保表单返回刚刚保存的清单：

```python
# lists/tests/test_forms.py
@patch("lists.forms.List.create_new")
def test_save_returns_new_list_object(self, mock_List_create_new):
    user = Mock(is_authenticated=lambda: True)
    form = NewListForm(data={"text": "new item text"})
    form.is_valid()
    response = form.save(owner=user)
    self.assertEqual(response, mock_List_create_new.return_value)
```

这是个和 List.create_new 之间有隐藏合约，希望这个方法会犯刚创建的清单对象。下面为这个需求添加一个占位测试：

```python
# lists/tests/test_models.py
class ListModelTest(TestCase):
    [...]
    
    def test_create_returns_new_list_object(self):
        self.fail()
```

得到失败测试，告诉我们要修正表单对象的 save 方法。

修正方法如下：

```python
# lists/forms.py
class NewListForm(ItemForm):
    def save(self, owner):
        if owner.is_authenticated():
            return List.create_new(first_item_text=self.cleanned_data["text"],owner=owner)
        else:
            return List.create_new(first_item_text=self.cleaned_data["text"])
```

下面应该看一下占位测试：

```python
# lists/tests/test_models.py
def test_create_returns_new_list_object(self):
    returned = List.create_new(first_item_text="new item text")
    new_list = List.objects.first()
    self.assertEqual(returned, new_list)
```

然后加上返回值：

```python
# lists/models.py
@staticmethod
def create_new(first_item_text, owner=None):
    list_ = List.objects.create(owner=owner)
    Item.objects.create(text=first_item_text, list_attr=list_)
    return list_
```

现在整个测试组件都可以通过了。

### 19.9 还缺一个测试

以上就是由测试驱动开发出来的保存清单属主功能，这个功能可以正常使用。不过，功能测试却无法通过：

```python
python3 manage.py test functional_tests.test_my_lists
```

失败的原因是有一个功能没实现，即清单对象的 `.name` 属性。这里还可以使用前一章的测试和代码：

```python
# lists/tests/test_models.py
def test_list_name_is_first_item_text(self):
    list_ = List.objects.create()
    Item.objects.create(list_attr=list_, text="first item")
    Item.objects.create(list_attr=list_, text="second item")
    self.assertEqual(list_.name, "first item")
```

这是模型层测试，所以使用 ORM 没问题（`Item.objects.create()` 就是 ORM）。

```python
# lists/modesl.py
@property
def name(self):
    return self.item_set.first().text
```

现在功能测试可以通过了。

### 19.10 清理：保留哪些整合测试

现在一切都可以正常运行了，要删除一些多余的测试，还要决定是否保留以前的测试。

#### 19.10.1 删除表单层多余的代码

可以把以前针对 ItemForm 类中 save 方法的测试删掉：

```python
# lists/tests/test_form.py
class ItemFormTest(TestCase)::
    @unittest.skip
    def test_form_save_handles_saving_to_a_list(self):
        [....]
```

对应用的代码而言，可以把 `forms.py` 中两个多余的 `save` 方法删掉：

```python
# lists/forms.py
class ItemForm(forms.models.ModelForm):
    # def save(self, for_list):
    # [...]

class ExistingListItemForm(ItemForm):
    # def save(self):
    #     return forms.models.ModelForm.save(self)
```

#### 19.10.2 删除以前实现的视图

现在，可以把以前的 `new_list` 视图完全删掉，再把 `new_list2` 重命名为 `new_list`:

```python
# lists/tests/test_views.py
# lists/urls.py
# lists/views.py
# 所有 new_list2 改为 new_list
```

然后检查所有测试是否仍能通过。

#### 19.10.3 删除视图层多余的代码

最后决定要保留哪些整合测试。一种方法是全部删除，让功能测试捕获集成问题。不过，如果在集成各层时犯了小错误，整合测试可以提醒你。可以保留部分测试，作为完整性检查，以便得到快速反馈。

```python
# lists/tests/test_views.py
# 只保留三个测试：
class NewListViewIntegratedTest(TestCase):
    def test_saving_a_POST_request(self):
        [...]
    def test_for_invalid_input_doesnt_save_but_shows_errors(self):
        [...]
    def test_saves_list_owner_if_user_logged_in(self):
        [...]
```

如果最终决定保留中间层的测试，这三个不错，涵盖了大部分集成操作：它们测试了整个组件，从请求直到数据库，而且覆盖了视图最重要的三个用例。

### 19.11 总结：什么时候编写隔离测试，什么时候编写整合测试

Django 提供的测试工具为快速编写整合测试提供了便利。测试运行程序能帮助我们创建一个存在于内存中的数据库，运行速度很快，而且在两次测试之间还能重建数据库。使用 TestCase 类和测试客户端测试视图很简单，可以检查是否修改了数据库中的对象，确认 URL 映射是否可用，还能检查渲染模板的情况。这些工具降低了测试的门槛，而且对整个组件也能获得不错的覆盖度。

#### 19.11.1 以复杂度为准则

处理复杂问题时才能体现隔离测试的优势。

#### 19.11.2 两种测试都要写吗

功能测试组件能告诉我们集成各部分代码时是否有问题。隔离测试能帮助我们设计出更好的代码，还能验证细节的处理是否正确。

集成测试的优势之一是，它在调用跟踪中提供的调试信息比功能测试详细。

甚至还可以把各组件分开——可以编写一个速度快、隔离的单元测试组件，完全不用 `manage.py`，因为这些测试不需要 Django 测试运行程序提供的任何数据库清理操作。然后使用 Django 提供的工具编写中间层测试，最后使用功能测试检查与过渡服务器交互的各层。如果各层提供的功能循序渐进，或许就可以采用这种方案。

#### 19.11.3 继续前行

将新版代码合并到主分支上：

```shell
git add .
git commit -m"add list owner via forms. more isolated tests"
git checkout master
git checkout -b master_backup # 为主分支做个备份
git checkout master
git reset --hard more-isolation # 把主分支重设到这个分支
```

现在，运行功能测试要花很长时间，我们需要改善一下这种情况。

> #### 不同测试类型以及解耦 ORM 代码的利弊
>
> * 功能测试
>   * 从用户的角度出发，最大程度上保证应用可以正常运行
>   * 但是，反馈循环用时长
>   * 无法帮助我们写出简洁的代码
> * 整合测试（依赖于 ORM 或 Django 测试客户端等）
>   * 编写速度快
>   * 易于理解
>   * 发现任何集成问题都会提醒你
>   * 但是，并不总能得到好的设计
>   * 一般运行速度比隔离测试慢
> * 隔离测试（使用驭件）
>   * 涉及的工作量最大
>   * 可能难以阅读和理解
>   * 但是，这种测试最能引导你实现更好的设计
>   * 运行速度最快
> * 解耦应用代码和 ORM 代码
>   * 钟情于隔离测试导致我们不得不从视图和表单等处删除 ORM 代码，把它们放到辅助函数或者辅助方法中。如果从解耦应用代码和 ORM 代码的角度看，这么做有好处，还能提高代码的可读性。