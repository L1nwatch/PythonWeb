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

最终，决定使用 [QUnit](http://qunitjs.com/)，因为它简单，而且能很好地和 jQuery 配合使用。

在 `lists/static` 中新建一个目录，将其命名为 tests，把 QUnit JavaScript 和 CSS 两个文件下载到该目录，如果必要的话，去掉文件名中的版本号。还要在该目录中放入一个 `test.html` 文件：

```shell
tree lists/static/tests/
|--- qunit.css
|--- qunit.js
|___ tests.html
```

QUnit 的 HTML 样板文件内容如下，其中包含一个冒烟测试：

```html
<!DOCTYPE html>
<html>
  <head>
    <meta charset="utf-8">
    <title>Javascript tests</title>
    <link rel="stylesheet" href="qunit.css">
  </head>
  
  <body>
    <div id="qunit"></div>
    <div id="qunit-fixture">
        <script src="qunit.js"></script>
        <script>
          /* global $, test, equal */
          
          test("smoke test", function() {
            equal(1, 1, "Maths works!");
          });
        </script>
    </div>
  </body>
</html>
```

仔细分析这个文件时，要注意几个重要的问题：使用第一个 `<script>` 标签引入 `qunit.js`，然后在第二个 `<script>` 标签中编写测试的主体。

> 写 /* global 这行注释，是因为作者正在使用一种名为 jslint 的工具，它集成在作者的编辑器中，是 JavaScript 句法检查程序。这行注释告诉 jslint 期望的全局变量是什么，这对代码本身并不重要，所以不担心。推荐了解一下这种 JavaScript 工具，例如 jslint 和 jshint，它们很有用，能防止你落入常见的 JavaScript 陷阱。

试试在 Web 浏览器中打开这个文件（不用运行开发服务器，在硬盘中找到这个文件即可）。

查看测试代码会发现，和我们目前编写的 Python 测试有很多相似之处：

```javascript
test("smoke test", function () { // test 函数定义一个测试用例，有点儿类似 Python 中的 def test_something(self)。test 函数的第一个参数是测试名，第二个参数是一个函数，定义这个测试的主体。
equal(1, 1, "Maths works!"); // equal 函数是一个断言，和 assertEqual 非常像，比较两个参数的值。不过，和在 Python 中不同的是，不管失败还是通过都会显示消息，所以消息应该使用肯定式而不是否定式。
})
```

### 13.3 使用 jQuery 和 `<div>` 固件元素

接下来熟悉一下这个测试框架能做什么，也开始使用一些 jQuery。

下面在脚本中加入 `jQuery`，以及测试中要使用的几个元素（自己使用的版本是 2 版本以上，原书中的 `test` 等方法已过时：

```html
    <div id="qunit-fixture"></div>

    <form> <!-- form 及其中的内容放在那儿是为了表示真实的清单页面中的内容 -->
        <input name="text"/>
        <div class="has-error">
            Error text
        </div>
    </form>

    <script src="http://code.jquery.com/jquery.min.js"></script>
    <script src="qunit.js"></script>
    <script>
        /* global $, test, equal */

    QUnit.test("smoke test1", function (assert) {
        // $("#has-error").show();
        assert.equal($('.has-error').is(':visible'), true, "Not hidden");
        /* jQuery 开始，$ 是 jQuery 用来查找 DOM 中的内容。$ 的第一个参数是 CSS 选择符，要查找类为 "error" 的所有元素。查找得到的结果是一个对象，表示一个或多个 DOM 元素。然后，可以在这个对象上使用很多有用的方法处理或者查看这些元素。 */
        /* 其中一个方法是 .is，它的作用是指出某个元素的表现是否和指定的 CSS 属性匹配。这里使用 :visible 检查元素是否显示出来。 */
        $('.has-error').hide();
        /* 使用 jQuery 提供的 .hide() 方法隐藏这个 <div> 元素。其实，这个方法是在元素上动态设定 style="display: none" 属性。 */
        assert.equal($('.has-error').is(':visible'), false, "Hidden");
        /* 最后，使用第二个 equal 断言检查隐藏是否成功。 */
    });
    </script>
```

注意，equal 的用法跟书中的不一样，具体[参考](http://stackoverflow.com/questions/8337186/jquery-isvisible-not-working-in-chrome)。刷新浏览器后应该会看到所有测试都通过了。

下面要介绍如何使用固件（fixture）：

> QUnit 中的测试不会按照既定的顺序运行，所以不要觉得第一个测试一定会在第二个测试之前运行。

我们需要一种方法在测试之间执行清理工作，有点儿类似于 setUp 和 tearDown，或者像 Django 测试运行程序一样，运行完每个测试后还原数据库。id 为 `qunit-fixture` 的 `<div>` 元素就是我们正在寻找的方法。把表单移到这个元素中：

```html
<div id="qunit"></div>
  <div id=qunit-fixture>
    <form>
      <input name="text" />
      <div class="has-error">
        Error text
      </div>
    </form>
</div>
```

每次运行测试前，jQuery 都会还原这个固件元素中的内容。因此，两个测试都能通过了。

### 为想要实现的功能编写 JavaScript 单元测试

现在我们已经熟悉这个 JavaScript 测试工具了，所以可以只留下一个测试，开始编写真正的测试代码了：

```html
<script>
    /* global $, test, equal */
    QUnit.test("errors should be hidden on keypress", function (assert) {
        $('input').trigger('keypress'); // jQuery 提供的 .trigger 方法主要用于测试，作用是在指定的元素上触发一个 JavaScript DOM 事件。这里使用的是 keypress 事件，当用户在指定的输入框中输入内容时，浏览器就会触发这个事件。
        assert.equal($('.has-error').is(':visible'), false);
    });
</script>
```

> 这里 jQuery 隐藏了很多复杂的细节。不同浏览器之间处理事件的方式大不一样，详情可以参考[Quirksmode.org](http://www.quirksmode.org/dom/events/)。jQuery 之所以这么受欢迎就是因为它消除了这些差异。

这个测试将会失败。

假设我们想把代码放在单独的 JavaScript 文件中，命名为 `list.js`。



