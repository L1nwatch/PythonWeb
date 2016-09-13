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

