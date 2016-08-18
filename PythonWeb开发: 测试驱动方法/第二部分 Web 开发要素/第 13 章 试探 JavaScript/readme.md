## 第 13 章 试探 JavaScript

> 假设知道基本的 JavaScript 语法。如果还没读过 《JavaScript 语言精粹》（JavaScript：The Good Parts）可以考虑买一下。

### 13.1 从功能测试开始

在 `ItemValidationTest` 类中添加一个新的功能测试：

```python
# test_list_item_validation.py
def test_error_messages_are_cleared_on_input(self):
    # Y 新建一个清单，但方法不当，所以出现了一个验证错误
    self.browser.get(self.server_url)
    self.get_item_input_box().send_keys("\n")
    error = self.browser.find_element_by_css_selector(".has-error")
    self.assertTrue(error.is_displayed()) # 1
    
    # 为了消除错误，她开始在输入框中输入内容
    self.get_item_input_box().send_keys("a")
    
    # 看到错误消息消失了，她很高兴
    error = self.browser.find_element_by_css_selector(".has-error")
    self.assertFalse(error.is_displayed()) # 2
```

\#1\#2 `is_displayed()` 可检查元素是否可见。不能只靠检查元素是否存在于 DOM 中去判断，因为现在要开始隐藏元素了。

这个测试无疑会失败。但在继续之前，由于多次使用 CSS 查找错误消息元素。应该把这个操作移到一个辅助函数中了：

```python
# test_list_item_validation.py
def get_error_element(self):
    return self.browser.find_element_by_css_selector(".has-error")
```

> 作者建议把辅助函数放在使用它们的功能测试类中，仅当辅助函数需要在别处使用时才放在基类中，以防止基类太臃肿。这就是 YAGNI 原则。

然后，在 `test_list_item_validation.py` 中做五次替换。之后进行测试，得到了一个预期错误。`python3 manage.py test functional_tests.test_list_item_validation` 可以提交这些代码，作为对功能测试的首次改动。

###  13.2 安装一个基本的 JavaScript 测试运行程序

在 Python 和 Django 领域中选择测试工具非常简单。标准库中的 unittest 模块完全够用了，而且 Django 测试运行程序也是一个不错的默认选择。除此之外，还有一些替代工具，比如 nose 很受欢迎。另外作者对 pytest 的印象比较深刻。不过默认选项很不错，已能满足要求。

在 JavaScript 领域，情况就不一样了。在工作中使用 YUI，但应该看看有没有其他新推出的工具。有很多的选项——jsUnit、Qunit、Mocha、Chutzpah、Karma、Testacular、Jasmine 等。而且还不仅仅局限于此：几乎选中其中一个工具后，还得选择一个断言框架和报告程序，或许还要选择一个模拟技术库。