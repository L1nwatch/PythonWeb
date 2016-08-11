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

