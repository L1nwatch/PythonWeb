## 第 21 章 简单的社会化功能、页面模式，以及练习

我们就让用户能和其他人协作完成他们的列表。

在实现这个功能的过程中，先使用 Selenium 交互等待模式改进功能测试，然后试用页面对象模式（Page Object pattern）。

### 21.1 有多个用户以及使用 addCleanup 的功能测试

这个功能测试需要两个用户：

```python
# functional_tests/test_sharing.py
from selenium import webdriver
from .base import FunctionalTest

def quit_if_possible(browser):
    try:
        browser.quit()
    except: pass

class SharingTest(FunctionalTest):
    def test_logged_in_users_lists_are_saved_as_my_lists(self):
        # Y 是已登录用户
        self.create_pre_authenticated_session("edith@example.com")
        edith_browser = self.browser
        self.addCleanup(lambda: quit_if_possible(edith_browser))
        
        # 她的朋友 Oniciferous 也在使用这个清单网站
        oni_browser = webdriver.Firefox()
        self.addCleanup(lambda: quit_if_possible(oni_browser))
        self.browser = oni_browser
        self.create_pre_authenticated_session("oniciferous@example.com")
        
        # Y 访问首页，新建一个清单
        self.browser = edith_browser
        self.browser.get(self.server_url)
        self.get_item_input_box().send_keys("Get help\n")
        
        # 她看到“分享这个清单”选项
        share_box = self.browser.find_element_by_css_selector("input[name=email]")
        self.assertEqual(
        	share_box.get_attribute("placeholder"),
            "your-friend@example.com"
        )
```

有一个功能值得注意：`addCleanup` 函数，它的文档可以在[这里](https://docs.python. org/3/library/unittest.html#unittest.TestCase.addCleanup)查看。这个函数可以代替 `tearDown` 函数，清理测试中使用的资源。如果资源在测试运行的过程中才用到，最好使用 `addCleanup` 函数，因为这样就不用在 `tearDown` 函数中花时间区分哪些资源需要清理，哪些不需要清理。

`addCleanup` 函数在 `tearDown` 函数之后运行，所以在 `quit_if_possible` 函数中才要使用 `try/except` 语句，因为不管 `edith_browser` 和 `oni_browser` 中哪一个值是 `self.browser`，测试结束时 `tearDown` 函数都会关闭这个浏览器。

还要把测试方法 `create_pre_authenticated_session` 从 `test_my_lists.py` 中移到 `base.py` 中。

测试可以看到意料之中的失败，因为页面中没有填写邮件地址的输入框，无法分享给别人。

现在做一次提交，因为至少已经编写了一个占位功能测试，也移动了 `create_pre_authenticated_session` 函数，接下来要重构功能测试。

```shell
git add functional_tests
git commit -m "New FT for sharing, move session creation stuff to base"
```

### 21.2 实现 Selenium 交互等待模式

先仔细看一下现在功能测试中与网站交互的代码：

```python
# functional_tests/test_sharing.py
# Y 访问首页，新建一个清单
self.browser.get(self.server_url)
# 与网站交互
self.get_item_input_box().send_keys("Get help\n")

# 她看到“分享这个清单”选项
# 猜想页面更新后的状态
share_box = self.browser.find_element_by_css_selector("input[name=email]")
self.assertEqual(share_box.get_attribute("placeholder"), "your-friend@example.com")
```

与网站交互后，过多猜想浏览器的状态有风险。理论上，如果 `find_element_by_css_selector` 第一次没有找到 `input[name=email],implicitly_wait` 在后台会再试几次。但重试的过程中可能出错，假如前一个页面中也有属性为 `name=email` 的输入框，只是占位文本不同，测试会莫名其妙地失败，因为理论上，在新页面加载的同时，Selenium 也可以获取前一个页面中的元素，很可能会抛出 `StaleElementException` 异常。

> 如果 Selenium 意外抛出 StaleElementException 异常，通常是因为有某种条件竞争。或许应该使用显式等待模式。

因此，如果交互后想立即检查结果，一定要谨慎。可以沿用 `wait_for` 函数中使用的等待方式，改为：

```python
# functional_tests/test_sharing.py
self.get_item_input_box().send_keys("Get help\n")

# 她看到”分享这个清单“选项
self.wait_for(
	lambda: self.assertEqual(
    	self.browser.find_element_by_css_selector(
        	"input[name=email]"
        ).get_attribute("placeholder"),
        "your-friend@example.com"
    )
)
```

### 21.3 页面模式

这里可以使用”三则重构“原则。这个测试以及很多测试，开头都是用户新建一个清单。定义一个辅助函数，命名为 `start_new_list`，让它调用 `wait_for` 以及输入清单中的待办事项。

分析功能测试的辅助代码有个公认可行的方式，叫做[页面模式](http://www.seleniumhq.org/ docs/06_test_design_considerations.jsp#page-object-design-pattern)。在页面模式中要定义多个对象，分别表示网站中不同的页面，而且只能在这些对象中存储于页面交互的方式。

首页的页面对象如下：

```python
# functional_tests/home_and_list_pages.py
class HomePage(object):
    def __init__(self, test):
        self.test = test # 使用表示当前测试的对象初始化，这样就能声明断言，通过 self.test.browser 访问浏览器实例，也能使用 wait_for 函数
	
    def go_to_home_page(self): # 大多数页面对象都有一个方法用于访问这个页面。注意，这个方法实现了交互等待模式——首先调用 get 方法获取这个页面的 URL，然后等待我们知道会在首页中显示的元素出现
        self.test.browser.get(self.test.server_url)
        self.test.wait_for(self.get_item_input)
        return self # 返回 self 只是为了操作方便。这么做可以使用方法串接 https://en.wikipedia.org/wiki/ Method_chaining
    
    def get_item_input(self):
        return self.test.browser.find_element_by_id("id_text")
    
    def start_new_list(self, item_text): # 这是用于新建清单的方法。访问首页，找到输入框，再按回车键。然后等待一段时间，确保交互完成。不过可以看出，这次等待其实发生在另一个页面对象中
        self.go_to_home_page()
        inputbox = self.get_item_input()
        inputbox.send_keys(item_text + "\n")
        list_page = ListPage(self.test) # ListPage 稍后定义，初始化的方式类似于 HomePage
        list_page.wait_for_new_item_in_list(item_text, 1) # 调用 ListPage 类中的 wait_for_new_item_in_list 方法，指定期望看到的待办事项文本以及在清单中的排位
        return list_page # 最后，把 list_page 对象返回给调用者，因为调用者可能会用到这个对象
```

ListPage 类的定义如下：

```python
# functional_tests/home_and_list_pages.py
[...]

class ListPage(object):
    def __init__(self, test):
       	self.test = test

    def get_list_table_rows(self):
        return self.test.browser.find_elements_by_css_selector("#id_list_table tr")
    
    def wait_for_new_item_in_list(self, item_text, position):
        expected_row = "{}: {}".format(position, item_text)
        self.test.wait_for(lambda: self.test.assertIn(
        	expected_row,
            [row.text for row in self.get_list_table_rows()]
        ))
```

> 一般来说，最好把页面对象放在各自的文件中。这里 HomePage 和 ListPage 联系比较紧密，所以可以放在同一个文件中。

下面看一下如何在测试中使用页面对象：

```python
# functional_tests/test_sharing.py
from .home_and_list_pages import HomePage
[...]

# Y 访问首页，新建一个清单
self.browser = edith_browser
list_page = HomePage(self).start_new_list("Get help")
```

继续改写测试，只想访问列表页面中的元素，就使用页面对象：

```python
# functional_tests/test_sharing.py
# 她看到”分享这个清单“选项
share_box = list_page.get_share_box()
self.assertEqual(
	share_box.get_attribute("placeholder"),
    "your-friend@example.com"
)

# 她分享自己的清单之后，页面更新了
# 提示已经分享给 Oniciferous
list_page.share_list_with("oniciferous@example.com")
```

我们要在 ListPage 类中添加以下三个方法：

```python
# functional_tests/home_and_list_pages.py
def get_share_box(self):
    return self.test.browser.find_element_by_css_selector("input[name=email]")

def get_shared_with_list(self):
    return self.test.browser.find_element_by_css_selector(".list-sharee")

def share_list_with(self, email):
    self.get_share_box().send_keys(email + "\n")
    self.test.wait_for(lambda: self.test.assertIn(
    	email,
        [item.text for item in self.get_shared_with_list()]
    ))
```

页面模型背后的思想是，把网站中某个页面的所有信息都集中放在一个地方，如果以后想要修改这个页面，比如简单的调整 HTML 布局，功能测试只需改动一个地方。

接下来要继续重构其他功能测试。

### 21.4 扩展功能测试测试第二个用户和 ”My Lists“ 页面

把分享功能的用户故事写得更加详细一点。Y 在她的清单页面看到这个清单已经分享给 Oniciferous，然后 Oniciferous 登录，看到这个清单出现在 ”My Lists“ 页面中，或许显示在 ”分享给我的清单“ 中：

```python
# functional_tests/test_sharing.py
[...]
list_page.share_list_with("oniciferous@example.com")

# 现在 Oniciferous 在他的浏览器中访问清单页面
self.browser = oni_browser
HomePage(self).go_to_home_page().go_to_my_lists_page()

# 他看到了 Y 分享的清单
self.browser.find_element_by_link_text("Get help").click()
```

为此，要在 HomePage 类中再定义一个方法：

```python
# functional_tests/home_and_list_pages.py
class HomePage(object):
    [...]
    def go_to_my_lists_page(self):
        self.test.browser.find_element_by_link_text("My Lists").click()
        self.test.wait_for(lambda: self.test.assertEqual(
        	self.test.browser.find_element_by_tag_name("h1").text,
            "My Lists"
        ))
```

这个方法最好放在 `test_my_lists.py` 中，或许还可以再定义一个 `MyListsPage` 类。

现在，Oniciferous 也可以在这个清单中添加待办事项：

```python
# functional_tests/test_sharing.py
# 在清单页面，Oniciferous 看到这个清单属于 Y
self.wait_for(lambda: self.assertEqual(
	list_page.get_list.owner(),
    'edith@example.com'
))

# 他在这个清单中添加一个待办事项
list_page.add_new_item("Hi Edith!")

# Y 刷新页面后，看到 Oniciferous 添加的内容
self.browser = edith_browser
self.browser.refresh()
list_page.wait_for_new_item_in_list("Hi Edith!", 2)
```

为此，要在页面对象中再定义几个方法：

```python
# functional_tests/home_and_list_pages.py
ITEM_INPUT_ID = "id_text"
[...]

class HomePage(object):
    [...]
    
    def get_item_input(self):
        return self.test.browser.find_element_by_id(ITEM_INPUT_ID)
    
class ListPage(object):
    [...]
    
    def get_item_input(self):
        return self.test.browser.find_element_by_id(ITEM_INPUT_ID)
    
    def add_new_item(self, item_text):
        current_pos = len(self.get_list_table_rows())
        self.get_item_input().send_keys(item_text + "\n")
        self.wait_for_new_item_in_list(item_text, current_pos + 1)
        
    def get_list_owner(self):
        return self.test.browser.find_element_by_id("id_list_owner").text
```

接下来运行功能测试，看看这些测试能否通过。

得到预料之中的失败，因为还没在页面中添加输入框，填写电子邮件地址，分享给别人，做次提交：

```shell
git add functional_tests
git commit -m "Create Page objects for Home and List pages, use in sharing FT"
```

### 21.5 留给读者的练习

实现这个新功能所需的步骤大致如下：

1. 在 list.html 添加一个新区域，先写一个表单，表单中包含一个输入框，用来输入电子邮件地址。功能测试应该会前进一步

   ```html
   {% block extra_content %}
       <div class="col-md-4 col-md-offset-1">
           <h3>Share this list:</h3>
           <form class="form-inline" method="POST" action="{%url 'share_list' %}">
               {% csrf_token %}
               <input name="email" placeholder="your-friend@example.com"/>
           </form>
       </div>
   {% endblock %}
   ```

2. 需要一个视图，处理表单。先在模板中定义 URL，例如 `lists//share`

   ```python
   # lists/urls.py
   urlpatterns = [
       url(r"^(\d+)/$", lists.views.view_list, name="view_list"),
       url(r"^new$", lists.views.new_list, name="new_list"),
       url(r"^users/(.+)/$", lists.views.my_lists, name="my_lists"),
       url(r'^(\d+)/share$', lists.views.share_list, name="share_list")
   ]

   # lists/views.py
   def share_list(request):
       pass
   ```

3. 然后，编写第一个单元测试，驱动我们定义占位视图。我们希望这个视图处理 POST 请求，响应是重定向，指向清单页面，所以这个测试可以命名为 `ShareListTest.test_post_redirects_to_lists_page`

   ```python
   # list.html
   {% block extra_content %}
       <div class="col-md-4 col-md-offset-1">
           <h3>Share this list:</h3>
           <form class="form-inline" method="POST"> action="{% url 'share_list' list_attr.id%}">
               {% csrf_token %}
               <input name="email" placeholder="your-friend@example.com"/>
           </form>
       </div>
   {% endblock %}

   # test_views.py
   class ShareListTest(TestCase):
       def test_post_redirects_to_lists_page(self):
           list1 = List.objects.create()
           response = self.client.post("/lists/{}/share".format(list1.id), data={"email": "test2@email.com"})
           self.assertRedirects(response, list1.get_absolute_url())
   ```

4. 编写占位视图，只需两行代码，一行用于查找清单，一行用于重定向

   ```python
   # lists/views.py
   def share_list(request, list_id):
       list_ = List.objects.get(id=list_id)
       return redirect(list_)
   ```

5. 可以再编写一个单元测试，在测试中创建一个用户和一个清单，在 POST 请求中发送电子邮件地址，然后检查 `list_.shared_with.all()` （类似于 "My Lists" 页面使用的那个 ORM 用法）中是否包含这个用户。`shared_with` 属性还不存在，我们使用的是由外而内的方式

   ```python
   # lists/tests/test_views.py
   def test_post_share_email_correct(self):
       user = User.objects.create(email="test@email.com")
       list1 = List.objects.create()
       response = self.client.post("/lists/{}/share".format(list1.id), data={"email": user.email})
       self.assertIn(user, list1.shared_with.all())
   ```

6. 所以在这个测试通过之前，要下移到模型层。下一个测试要写入 `test_models.py` 中。在这个测试中，可以检查清单能否响应 `shared_with.add` 方法。这个方法的参数是用户的电子邮件地址。然后检查清单的 `shared_with.all()` 查询集合中是否包含这个用户。

   ```python
   # lists/tests/test_models.py
   def test_shared_wtih_add_and_all(self):
       # 检查清单能否响应 shared_with.add 方法
       list1 = List.objects.create()
       test_email = "test@email.com"
       user = User.objects.create(email=test_email)
       list1.shared_with.add(test_email)
       list_in_db = List.objects.get(id=list1.id)
       self.assertIn(user, list_in_db.shared_with.all())
   ```

7. 然后需要用到 `ManyToManyField`。或许你会看到一个错误消息，提示 `related_name` 有冲突，查阅 Django 的文档之后你会找到解决办法。

   ```python
   # lists/models.py
   class List(models.Model):
       owner = models.ForeignKey(settings.AUTH_USER_MODEL, blank=True, null=True)
       shared_with = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name="lists_want_to_share")
       [...]
   ```

8. 需要执行一次数据库迁移

   ```shell
   python3 manage.py makemigrations
   python3 manage.py migrate
   ```

9. 然后，模型测试应该可以通过。回过头来修正视图测试

   ```python
   python3 manage.py test lists
   ```

10. 可能会发现重定向视图的测试失败，因为视图发送的 POST 请求无效。可以选择忽略无效的输入，也可以调整测试，发送有效的 POST 请求。

```python
   # lists/views.py
   def share_list(request, list_id):
       list_ = List.objects.get(id=list_id)
       list_.shared_with.add(request.POST["email"])
       return redirect(list_)
```

111. 然后回到模板层。"My Lists" 页面需要一个 `<ul>` 元素，使用 for 循环列出分享给这个用户的清单。还想在清单页面显示这个清单分享给谁了，并注明这个清单的属主是谁。各元素的类和 ID 参加功能测试。如果需要，还可以为这几个需求编写简单的单元测试。

```python
# lists/templates/list.html
{% block extra_content %}
<div class="row">
<div class="col-md-6">
<h3>Shared with</h3>
{% for has_shared in list_attr.shared_with.all %}
<li class="list-shared">{{ has_shared.email }}</li>
{% endfor %}
</div>


<div class="col-md-4 col-md-offset-1">
<h3>Share this list:</h3>
    <form class="form-inline" method="POST" action="{% url 'share_list' list_attr.id %}">
    {% csrf_token %}
    <input name="email" placeholder="your-friend@example.com"/>
    </form>
    </div>
    </div>
{% endblock %}
```

```python
# functional_tests/home_and_list_pages.py
def get_shared_with_list(self):
    return self.test.browser.find_elements_by_css_selector(".list-shared") # 注意是 find_elements 而不是 find_element
```

```python
# lists/templates/my_lists.html
{% block extra_content %}
<h2>
{#        <!-- 需要一个名为 owner 的变量，在模板中表示用户 -->#}
    {{ owner.email }}'s lists
    </h2>
    <ul>
    {#        <!-- 想使用 owner.list_set.all 遍历用户创建的清单(ORM 提供了这个属性) -->#}
        {% for list_attr in owner.list_set.all %}
        {#            <!-- 想使用 list.name 获取清单的名字，目前清单以其中的第一个待办事项命名 -->#}
            <li><a href="{{ list_attr.get_absolute_url }}">{{ list_attr.name }}</a></li>

            {% endfor %}
            </ul>
            <ul>
            {% for list_attr in owner.lists_want_to_share.all %}
            <li>
            <a href="{{ list_attr.get_absolute_url }}">{{ list_attr.name }}</a>
            ({{ list_attr.owner.email }})
            </li>
            {% endfor %}
            </ul>
            {% endblock %}
```

```python
# functional_tests/test_sharing.py
# 在清单页面，Oniciferous 看到这个清单属于 Y
self.wait_for(lambda: self.assertEqual(
    list_page.get_list_owner(), # 注意这里之前打成 get_list.owner() 了
    'edith@example.com'
))
```

```python
# lists/templates/list.html
{% block table %}
    <table id="id_list_table" class="table">
        {% for item in list_attr.item_set.all %}
            <tr>
                <td>{{ forloop.counter }}: {{ item.text }}</td>
            </tr>
        {% endfor %}
    </table>

    {% if list_attr.owner %}
        <p>List owner: <span id="id_list_owner">{{ list_attr.owner.email }}</span><p>
    {% endif %}
{% endblock %}
```

122. 执行 runserver 命令让网站运行起来，或许能帮助你解决问题，以及调整布局和外观。如果使用隐私浏览器会话，可以同时登陆多个用户。

> #### 页面模式以及真正留给读者的练习
>
> * 在功能测试中运用 DRY 原则
>   * 功能测试多起来后，就会发现不同的测试使用了 UI 的同一部分。尽量避免在多个功能测试中使用重复的常量，例如某个 UI 元素 HTML 代码中的 ID 和 类。
> * 页面模式
>   * 把辅助方法移到 FunctionalTest 基类中会把这个类变得臃肿不抗。可以考虑把处理网站特定部分的全部逻辑保存到单独的页面对象中。