## 附录 B 基于类的 Django 视图

第 12 章实现了 Django 表单的验证功能，还重构了视图。结束时，视图仍然使用函数实现。

不过 Django 领域现在流行使用基于类的视图（Class-Based View，CBV）。接下来要重构应用，把视图函数改写成基于类的视图。更确切的说，要尝试使用基于类的通用视图（Class-Based Generic View，CBGV）。

### B.1 基于类的通用视图

基于类的视图和基于类的通用视图有个区别。基于类的视图只是定义视图函数的另一种方式，对视图要做的事情没有太多假设，和视图函数相比主要的优势是可以创建子类。不过也要付出一定代价，基于类的视图比传统的基于函数的视图可读性差。普通的 CBV 的作用是让多个视图重用相同的逻辑，因为我们想遵守 DRY 原则。如果使用基于函数的视图，重用逻辑要使用辅助函数或修饰器。理论上，使用类实现更优雅。

基于类的通用视图也是一种基于类的视图，但它尝试为常见操作提供现成的解决方案，例如从数据库中获取对象后传入模板，获取一组对象，使用 ModelForm 保存 POST 请求中用户输入的数据等。

在 Django 应用中有很多地方都非常适合使用 CBGV。但是，只要需求稍微高一点，例如想使用多个模型，就会发现基于类的视图比传统的视图函数难读得多。

不过，因为必须使用基于类的视图提供的几个定制选项，通过这种实现方式能学到很多这种视图的工作方式，以及如何为这种视图编写单元测试。

### B.2 使用 FormView 实现首页

网站的首页只是在模板中显示一个表单：

```python
def home_page(request):
    return render(request, "home.html", {"form": ItemForm()})
```

看过[可选视图](https://docs.djangoproject.com/en/1.6/ref/class-based-views/)之后，发现 Django 提供了一个通用视图，叫 FormView。

```python
# lists/views.py
from django.views.generic import FormView
[...]

class HomePageView(FormView):
    template_name = "home.html"
    form_class = ItemForm
```

指定想使用哪个模板和表单。然后，只需更新 `urls.py`，把含有 `lists.views.home_page` 那行代码改成：

```python
# superlists/urls.py
url(r"^$", HomePageView.as_view(), name="home"),
```

运行所有测试确认。

把一行代码的视图函数转换成有两行代码的类，而且可读性依然不错，可以提交一下。

### B.3 使用 `form_valid` 定制 `CreateView`

下面改写新建清单的视图，也就是 `new_list` 函数。现在这个视图如下所示：

```python
# lists/views.py
def new_list(request):
    from = ItemForm(data=request.POST)
    if form.is_valid():
        list = List.objects.create()
        form.save(for_list = list_)
        return redirect(list_)
    else:
        return render(request, "home.html", {"form": form})
```

浏览可用的 CBGV 列表之后，发现需要的或许是 `CreateView`，而且知道要使用 `ItemForm` 类：

```python
# lists/views.py
from django.views.generic import FormView, CreateView
[...]

class NewListView(CreateView):
    form_class = ItemForm
[...]
```

修改 URL 映射，然后运行测试，根据错误来进行修改。

最终视图如下：

```python
# lists/views.py
class NewListView(CreateView):
    template_name = "home.html"
    form_class = ItemForm
    
    def form_valid(self, form):
        list_ = List.objects.create()
        form.save(for_list=list_)
        return redirect(list_)
```

这样测试就能全部通过了。

而且，为了遵守 DRY 原则，可以使用 CBV 的主要优势之一， 继承：

```python
# lists/views.py
class NewListView(CreateView, HomePageView):
    def form_valid(self, form):
        list = List.objects.create()
        Item.objects.create(text = form.cleaned_data["text"], list=list)
        return redirect("/lists/{}/".format(list.id))
```

 测试应该仍能全部通过。

> 其实在面向对象编程中这么做并不好。继承意味着“是一个什么”这种关系，但是说新建清单视图“是一个”首页视图没什么意义，所以，最好别这么做。

#### 个人实践

原来的视图以及更改后的视图类：

```python
class NewListView(CreateView):
    template_name = "home.html"
    form_class = NewListForm

    def form_valid(self, form):
        list_ = form.save(owner=self.request.user)
        return redirect("/lists/{}/".format(list_.id))


def new_list(request):
    form = NewListForm(data=request.POST)
    if form.is_valid():
        list_ = form.save(owner=request.user)
        return redirect(list_)
    return render(request, "home.html", {"form": form})
```

***

### B.4 一个更复杂的视图，既能查看清单，也能向清单中添加待办事项

大多数情况下都在反复实验，尝试使用 `get_context_data` 和 `get_form_kwargs` 等函数。

编写多个只测试一件事的测试很重要。

#### B.4.1 测试有指引作用，但时间不长

首先，需要使用 DetailView，显示对象的详情：

```python
# lists.views.py
from django.views.generic import FormView, CreateView, DetailView
[...]

class ViewAndAddToList(DetailView):
    model = List
```

进行测试，需要使用正则表达式具名捕获组：

```python
# lists/urls.py
from lists.views import NewListView, ViewAndAddToList

url(r"^(?P<pk>\d+)/$)", ViewAndAddToList.as_view(), name="view_list")
```

然后进行测试，现在测试中出现的错误就相当有帮助了。

```python
# lists/views.py
class ViewAndAddToList(DetailView):
    model = List
    template_name = "list.html"
```

#### B.4.2 现在不得不反复实验

这个视图不仅要显示对象的详情，还要能新建对象，所以这个视图要继承 DetailView 和 CreateView。

```python
# lists/views.py
class ViewAndAddToList(DetailView, CreateView):
    model = List
    template_name = "list.html"
    form_class = ExistingListItemForm
```

可以尝试使用 `get_form_kwargs`，但没什么用，后来发现可以使用 `get_form`：

```python
# lists/views.py
def get_form(self, form_class):
    self.object = self.get_object()
    return form_class(for_list=self.object, data=self.request.POST)
```

#### B.4.3 测试再次发挥作用

实验之后，把 `DetailView` 换成了 `SingleObjectMixin`：

```python
from django.views.generic.detail import SingleObjectMixin
[...]

class ViewAndAddToList(CreateView, SingleObjectMixin):
    [...]
```

这么修改之后，只剩两个错误了。解决办法是在 Item 类中定义 `get_absolute_url` 方法，让待办事项指向所属的清单页面即可。

```python
# lists/models.py
class Item(models.Model):
    [...]
    
    def get_absolute_url(self):
        return reverse("view_list", args=[self.list.id])
```

#### B.4.4 这是最终结果吗？

最终写出的视图类如下所示：

```python
# lists/views.py
class ViewAndAddToList(CreateView, SingleObjectMixin):
    template_name = "list.html"
    model = List
    form_class = ExistingListItemForm
    
    def get_form(self, form_class):
        self.object = self.get_object()
        return form_class(for_list=self.object, data=self.request.POST)
```

### B.5 新旧版对比

```python
# lists/views.py
def view_list(request, list_id):
    list_ = List.objects.get(id=list_id)
    form = ExistingListItemForm(for_list=list_)
    if request.method == "POST":
        form = ExistingListItemForm(for_list=list_, data=request.POST)
        if form.is_valid():
            form.save()
            return redirect(list_)
    return render(request, "list.html", {"list": list_, "form": form})
```

基于函数的视图稍微容易理解一点，因为旧版没隐藏那么多细节。明确表述比含糊其实强，这是 Python 的禅理。

### B.6 为 CBGV 编写单元测试有最佳实践吗？

实现这个视图类之后，可以发现单元测试有点儿太关注高层。因为使用 Django 测试客户端的视图测试后续更应该叫整合测试。

这里有一种编写测试的方法，更贴近实现方式，例如这么编写测试：

```python
def test_cbv_gets_correct_object(self):
    our_list = List.objects.create()
    view = ViewAndAddToList()
    view.kwargs = dict(pk=our_list.id)
    self.assertEqual(view.get_object(), our_list)
```

但这么做有个问题，必须对 Django CBV 的内部机理有一定了解，才能正确设定这种测试。而且最后还是会被复杂的继承体系弄得十分糊涂。

#### 记住：编写多个只有一个断言的隔离测试有所帮助

编写多个简短的单元测试比编写少量含有很多断言的测试有用得多。

因为，对前一种方式来说，如果靠前的断言失败了，后面的断言就不会执行。所以，如果视图不小心把 POST 请求中的无效数据存入数据库，前面的断言会失败，这样就无法确认使用的模板是否正确以及有没有渲染表单。使用后一种方式则能更轻易地分辨出到底哪一部分能用，哪一部分不能用。

> #### 从 CBGV 中学到的经验
>
> * 基于类的通用视图可以做任何事
> * 只有一个断言的单元测试有助于重构

