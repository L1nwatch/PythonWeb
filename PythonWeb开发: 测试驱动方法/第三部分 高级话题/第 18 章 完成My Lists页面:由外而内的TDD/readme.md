## 第 18 章 完成 "My Lists" 页面:由外而内的 TDD

## 18.1 对立技术：“由内而外”

大多数人都凭直觉选择后者。提出一个设计想法之后，有时会自然而然地从最内部、最低层的组件开始实现。

这么做感觉更自然，因为所用的代码从来不会依赖尚未实现的功能。内层的一切都是构建外层的坚实基础。

### 18.2 为什么选择使用 “由外而内”

由内而外的技术最明显的问题是它迫使我们抛开 TDD 流程。

我们可能已经在脑海中构思好了内层的模样，而且这些想法往往都很好，不过这些都是对真实需求的推测，因为还未构造内层组件的外层组件。

这么做可能会导致内层组件太笼统，或者比真实需求功能更强——不仅浪费了时间，还把项目变得更为复杂。另一种常见的问题是，创建内层组件使用的 API 乍看起来对内部设计而言很合适，但之后会发现并不适用于外层组件。更糟的是，最后你可能会发现内层组件完全无法解决外层组件需要解决的问题。

由此相反，使用由外而内的工作方式，可以在外层组件的基础上构思想从内层组件获取的最佳 API。

## 18.3 "My Lists" 页面的功能测试

编写下面这个功能测试时，我们从能接触到的最外层开始（表现层），然后是视图函数（或叫“控制器”），最后是内层，比如模型代码。

既然 `create_pre_authenticated_session` 函数可以正常使用，那么久可以直接用来编写针对 "My Lists" 页面的功能测试：

```python
# functional_tests/test_my_lists.py
    def test_logged_in_users_lists_are_saved_as_my_lists(self):
        email = "edith@mockmyid.com"  # 这个邮箱成功了, 我自己的邮箱好像还要密码所以就失败了?

        self.browser.get(self.server_url)
        self.wait_to_be_logged_out(email)

        # Y 是已登录用户
        self.create_pre_authenticated_session(email)

        # self.browser.get(self.server_url)
        # self.wait_to_be_logged_in(email)

        # 她访问首页，新建一个清单
        self.browser.get(self.server_url)
        self.get_item_input_box().send_keys("Reticulate splines\n")
        self.get_item_input_box().send_keys("Immanentize eschaton\n")
        first_list_url = self.browser.current_url

        # 她第一次看到 My Lists 链接
        self.browser.find_element_by_link_text("My Lists").click()

        # 她看到这个页面中有她创建的清单
        # 而且清单根据第一个待办事项命名
        self.browser.find_element_by_link_text("Reticulate splines").click()
        self.assertEqual(self.browser.current_url, first_list_url)

        # 她决定再建一个清单试试
        self.browser.get(self.server_url)
        self.get_item_input_box().send_keys("Click cows\n")
        second_list_url = self.browser.current_url

        # 在 My Lists 页面，这个新建的清单也显示出来了
        self.browser.find_element_by_link_text("My Lists").click()
        self.browser.find_element_by_link_text("Click cows").click()
        self.assertEqual(self.browser.current_url, second_list_url)

        # 她退出后, My Lists 链接不见了
        self.browser.find_element_by_id("id_logout").click()
        self.assertEqual(self.browser.find_elements_by_link_text("My Lists"), [])
```

运行这个测试，可以看到预期的错误。

```shell
python3.4 manage.py test functional_tests.test_my_lists.MyListsTest.test_logged_in_users_lists_are_saved_as_my_lists
```

### 18.4 外层：表现层和模板

目前，这个测试失败，报错无法找到 "My Lists" 链接。这个问题可以在表现层，即 `base.html` 模板里的导航条中解决。最少量的代码改动：

```html
<!-- lists/templates/base.html -->
{% if user.email %}
	<ul class="nav navbar-nav">
      <li><a href="#">My Lists</a></li>
	</ul>
	<a class="btn navbar-btn navbar-right" id="id_logout" [...]
```

显然，这个链接没指向任何页面，不过却能解决问题，得到下一个失败消息。

失败消息指出要构建一个页面，用标题列出一个用户的所有清单。

可以再次使用由外而内技术，先从表现层开始，只写上地址，其他什么都不做：

```html
<!-- lists/templates/base.html -->
<ul class="nav navbar-nav">
  <li><a href="{% url 'my_lists' user.email %}">My Lists</a></li>
</ul>
```

### 18.5 下移一层到视图函数（控制器）

这样改还是会得到模板错误，所以要从表现层和 URL 层下移，进入控制器层，即 Django 中的视图函数。

先写测试：

```python
# lists/tests/test_views.py
class MyListsTest(TestCase):
    def test_my_lists_url_renders_my_lists_template(self):
        response = self.client.get("/lists/users/a@b.com")
        self.assertTemplateUsed(response, "my_lists.html")
```

 得到预期的失败测试结果。

然后修正这个问题，不过还在表现层，更准确地说是 `urls.py`：

```python
# lists/urls.py
urlpatterns = [
    url(r"^(\d+)/$", lists.views.view_list, name="view_list"),
    url(r"^new$", lists.views.new_list, name="new_list"),
    url(r"^users/(.+)/$", "lists.views.my_lists", name="my_lists")
]
```

修改之后会得到另一个测试失败消息。

从表现层移到视图层，再定义一个最简单的占位视图：

```python
# lists/views.py
def my_lists(request, email):
    return render(request, "my_lists.html")
```

以及一个最简单的模板：

```html
<!-- lists/templates/my_lists.html -->
{% extends "base.html" %}
{% block header_text %}My Lists{% endblock %}
```

现在单元测试通过了，但功能测试毫无进展。

### 18.6 使用由外而内技术，再让一个测试通过

再次从外层开始，编写模板代码，让" My Lists"页面实现设想的功能。现在，要指定希望从低层获取的 API。

#### 18.6.1 快速重组模板的继承层级

基模板目前没有地方放置新内容了，而且" My Lists"页面不需要新建待办事项清单，所以把表单放到一个块中，需要时才显示：

```html
<!-- lists/templates/base.html -->
<div class="text-center">
  <h1>
    {% block header_text %}{% endblock %}
  </h1>
  
  {% block list_form %}
  <form method="POST" action="{% block form_action %}{% endblock %}">
    {{ form. text }}
    {% csrf_token %}
    {% if form.erros %}
    <div class="form-group has-error">
      <div class="help-block">
        {{ form.text.errors }}
      </div>
    </div>
    {% endif %}
  </form>
  {% endblock %}
</div>
[...]
    <div class="row">
        <div class="col-md-6 col-md-offset-3">
            {% block table %}
            {% endblock %}
        </div>
    </div>

    <div class="row">
        <div class="col-md-6 col-md-offset-3">
            {% block extra_content %}
            {% endblock %}
        </div>
    </div>
</div>
```

#### 18.6.2 使用模板设计 API

同时，在 `my_lists.html` 中覆盖 `list_form` 块，把块中的内容清空：

```html
<!-- lists/templates/my_lists.html -->
{% extends "base.html" %}
{% block header_text %}My Lists{% endblock %}
{% block list_form %}{% endblock %}
```

然后只在 `extra_content` 块中编写代码：

```html
<!-- lists/templates/my_lists.html -->
[...]
{% block list_form %}{% endblock %}

{% block extra_content %}
    <h2>
        <!-- 需要一个名为 owner 的变量，在模板中表示用户 -->
        {{ owner.email }}'s lists
    </h2>
    <ul>
        <!-- 想使用 owner.list_set.all 遍历用户创建的清单(ORM 提供了这个属性) -->
        {% for list in owner.list_set.all %}
            <!-- 想使用 list.name 获取清单的名字，目前清单以其中的第一个待办事项命名 -->
            <li><a href="{{ list.get_absolute_url }}">{{ list.name }}</a></li>
        {% endfor %}
    </ul>
{% endblock %}
```

再次运行功能测试，确认没有造成任何破坏，或者是有所进展：

```python
python3 manage.py test functional_tests
```

该提交了：

```shell
git add lists
git diff --staged
git commit -m "url, placehodler view, and first-cut templates for my_lists"
```

#### 18.6.3 移到下一层：视图向模板中传入什么

```python
# lists/tests/test_views.py
from django.contrib.auth import get_user_model
User = get_user_model()
[...]
class MyListsTest(TestCase):
    def test_my_lists_url_renders_my_lists_template(self):
        [...]
        
	def test_passes_correct_owner_to_template(self):
        User.objects.create(email="wrong@owner.com")
        correct_user = User.objects.create(email="a@b.com")
        response = self.client.get("/lists/users/a@b.com/")
        self.assertEqual(response.context["owner"], correct_user)
```

视图没有传入 owner，于是：

```python
# lists/views.py
from django.contrib.auth import get_user_model
User = get_user_model()
[...]

def my_lists(request, email):
    owner = User.objects.get(email=email)
    return render(request, "my_lists.html", {"owner": owner})
```

这样修改之后，新测试通过了，但还是能看到前一个测试导致的错误。只需要在这个测试中添加一个用户即可：

```python
# lists/tests/test_views.py
def test_my_lists_url_renders_my_lists_template(self):
    User.objects.create(email="a@b.com")
    [...]
```

### 18.7 视图层的下一个需求：新建清单时应该记录属主

下移到模型层之前，视图层还有一部分代码要用到模型：如果当前用户已经登录网站，需要一种方式把新建的清单指派给一个属主。

初期编写的测试如下所示：

```python
# lists/tests/test_views.py
from django.http import HttpRequest
[...]
from lists.views import new_list
[...]

class NewListTest(TestCase):
    [...]
    
    def test_list_owner_is_saved_if_user_is_authenticated(self):
        request = HttpRequest()
        request.user = User.objects.create(email="a@b.com")
        request.POST["text"] = "new list item"
        new_list(request)
        list_ = List.objects.first()
        self.assertEqual(list_.owner, request.user)
```

这个测试直接调用视图函数，而且手动构造了一个 HttpRequest 对象，因为这么写测试稍微简单些。虽然 Django 测试客户端提供了辅助函数 login，但在外部认证系统中用起来并不顺手。此外，还可以手动创建会话对象，或者使用驭件。不过这两种方式写出来的代码并不好看。

按照测试失败的消息来改进代码，首先尝试如下编写：

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

但这个视图解决不了问题，因为还不知道怎么保存清单的属主。

#### 抉择时刻：测试失败时是否要移入下一层

为了让这个测试通过，要下移到模型层。

可以采用另一种策略，使用驭件把测试和下层组件更明显地隔离开。

一方面，使用驭件要做的工作更多，而且驭件会让测试代码更难读懂。另一方面，如果应用更复杂，外部和内部之间的分层更多，测试就会涉及多层。

这里先走捷径，放任测试失败不管。

下面做次提交，并且为这次提交打上标签。

```shell
git commit -am "new_list view tries to assign owner bat cant"
git tag revisit_this_point_with_isolated_tests
```

### 18.8 下移到模型层

使用由外而内技术得出了两个需求，需要在模型层实现：其一，想使用 `.owner` 属性为清单指派一个属主；其二，想使用 `API owner.list_set.all` 获取清单的属主。

针对这两个需求，先编写一个测试：

```python
# lists/tests/test_models.py
from django.contrib.auth import get_user_model
User = get_user_model()
[...]

class ListModelTest(TestCase):
    def test_get_absolute_url(self):
        [...]

    def test_lists_can_have_owners(self):
        user = User.objects.create(email="a@b.com")
        list_ = List.objects.create(owner=user)
        self.assertIn(list_, user.list_set.all())
```

得到了一个失败的单元测试，接着把模型写成下面这样：

```python
from django.conf import settings
[...]

class List(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL)
```

可是我们希望属主可有可无，所以再编写一个测试来明确表示需求：

```python
# lists/tests/test_models.py
def test_list_owner_is_optional(self):
    List.objects.create() # 不该抛出异常
```

于是可以实现正确的模型了：

```python
# lists/models.py
from django.conf import settings
[...]

class List(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, blank=True, null=True)
    
    def get_absolute_url(self):
        return reverse("view_list", args=[self.id])
```

现在运行测试，会看到数据库错误，因此需要做一次迁移。

现在回到视图层，做些清理工作。注意，这些错误发生在针对 `new_list` 视图的测试中，而且用户没有登录。仅当用户登录后才应该保存清单的属主。（用户未登录时，Django 使用 AnonymousUser 类表示用户，此时 `is_authenticated()` 函数的返回值始终是 False）：

```python
# lists/views.py
if form.is_valid():
    list_ = List()
    if request.user.is_authenticated():
        list_.owner = request.user
    list_.save()
    form.save(for_list=list_)
    [...]
```

这样修改之后，测试通过了。

现在是提交的好时机了：

```shell
git add lists
git commit -m "lists can have owners, which are saved on creation."
```

#### 最后一步：实现模板需要的 `.name` 属性

使用由外而内设计方式还有最后一个需求，即清单根据其中第一个待办事项命名：

```python
# lists/tests/test_models.py
def test_list_name_is_first_item_text(self):
    list_ = List.objects.create()
    Item.objects.create(list_attr=list_, text="first item")
    Item.objects.create(list_attr=list_, text="second item")
    self.assertEqual(list_.name, "first item")
```

```python
# lists/models.py
@property
def name(self):
    return self.item_set.first().text
```

这样测试就能通过了，而且 "My Lists" 页面也能使用了。

> #### Python 中的 `@property` 修饰器
>
> 该修饰器的作用是把类中的方法转变成与属性一样，可以在外部访问。
>
> 这是 Python 语言一个强大的特性，因为很容易用它实现“鸭子类型”（duck typing），无需修改类的接口就能改变属性的实现方式。也就是说，如果想把 `.name` 改成模型真正的属性，在数据库中存储文本型数据，整个过程是完全透明的，只要兼顾其他代码，就能继续使用 `.name` 获取清单名，完全不用知道这个属性的具体实现方式。
>
> 不过，就算没使用 @property 修饰器，在 Django 的模板语言中还是会调用 `.name` 方法。不过这是 Django 专有的特性，不适用于一般的 Python 程序。

> #### 由外而内的 TDD
>
> * 由外而内的 TDD
>   * 一种编写代码的方法，由测试驱动，从外层开始（表现层，GUI），然后逐步向内层移动，通过视图层或控制层，最终达到模型层。这种方法的理念是由实际需要使用的功能驱动代码的编写，而不是在低层猜测需求。
> * 一厢情愿式编程
>   * 由外而内的过程有时也叫“一厢情愿式编程“。其实，任何 TDD 形式都涉及一厢情愿。我们总是为还未实现的功能编写测试。
> * 由外而内技术的缺点
>   * 由外而内技术鼓励我们关注用户立即就能看到的功能，但不会自动提醒我们为不是那么明显的功能编写关键测试，例如安全相关的功能。

