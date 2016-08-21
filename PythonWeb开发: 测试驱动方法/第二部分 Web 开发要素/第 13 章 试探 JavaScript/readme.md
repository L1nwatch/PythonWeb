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

```html
<!-- static/tests/tests.html -->
<script src="qunit.js"></script>
<script src="../list.js"></script>
<script>
  ...
```

若想让这个测试通过，所需的最简代码如下所示：

```javascript
// static/list.js
$('.has-error').hide();
```

显然还有个问题，最好再添加一个测试：

```html
<!-- static/tests/tests.html -->
<script src="../list.js"></script>
<script>
    /* global $, test, equal */
    QUnit.test("errors should be hidden on keypress", function (assert) {
        $('input').trigger('keypress'); // jQuery 提供的 .trigger 方法主要用于测试，作用是在指定的元素上触发一个 JavaScript DOM 事件。这里使用的是 keypress 事件，当用户在指定的输入框中输入内容时，浏览器就会触发这个事件。
        //$('.has-error').hide();
        assert.equal($('.has-error').is(':visible'), false);
    });

    QUnit.test("errors not be hidden unless there is a keypress", function (assert) {
        assert.equal($('.has-error').is(':visible'), true);
    });
</script>
```

得到一个预期的失败。然后，可以使用一种更真实的实现方式：

```javascript
// static/list.js
$('input').on('keypress', function() { // 查找所有 input 元素，然后在找到的每个元素上附属一个事件监听器，作用在 keypress 事件上。事件监听器是那个行间函数，其作用是隐藏类为 .has-error 的所有元素
	$('.has-error').hide();
});
```

这段代码能让单元测试通过。

接下来，在所有页面中都引入这个脚本和 jQuery ：

```html
</div>
<script src="http://code.jquery.com/jquery.min.js"></script>
<script src="/static/list.js"></script>
</body>
</html>
```

> 习惯做法是在 HTML 的 body 元素末尾引入脚本，因为这么做用户无须等到所有 JavaScript 都加载完才能看到页面中的内容。而且还能保证运行脚本前加载了大部分 DOM。

然后运行功能测试，发现也通过了。

```shell
python3 manage.py test functional_tests.test_list_item_validation.ItemValidationTest.test_error_messages_are_messages_are_cleared_on_input
```

接下来可以做次提交了。

#### 个人实践，由于所用版本与书中不同，以下是自己成功的版本：

```html
<!-- tests.html -->
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
    <form> <!-- form 及其中的内容放在那儿是为了表示真实的清单页面中的内容 -->
        <input name="text"/>
        <div class="has-error">
            Error Text
        </div>
    </form>
</div>

<script src="http://code.jquery.com/jquery.min.js"></script>
<script src="qunit.js"></script>

<script src="../list.js"></script>
<script>
    /* global $, test, equal */
    QUnit.test("errors should be hidden on keypress", function (assert) {
        $('input[name="text"]').trigger('keypress'); // jQuery 提供的 .trigger 方法主要用于测试，作用是在指定的元素上触发一个 JavaScript DOM 事件。这里使用的是 keypress 事件，当用户在指定的输入框中输入内容时，浏览器就会触发这个事件。
        //$('.has-error').hide();
        assert.equal($('.has-error').is(':visible'), false);
    });

    QUnit.test("errors not be hidden unless there is a keypress", function (assert) {
        assert.equal($('.has-error').is(':visible'), true);
    });
</script>

</body>
</html>
```

```javascript
// list.js
var hide_error = function () {
    $('input').on("keypress", function () {
        $(".has-error").hide();
    });
};

QUnit.module("module A ", {
    before: hide_error
});
```

但是注意着只是能通过 JavaScript 的单元测试，在 Python 的功能测试中依旧失败，还是得用书中给出的代码才能通过功能测试，郁闷了。

### 13.5 JavaScript 测试在 TDD 循环中的位置

JavaScript 测试在双重 TDD 循环中处于什么位置？答案是，JavaScript 测试和 Python 单元测试扮演的角色完全相同。

1. 编写一个功能测试，看着它失败
2. 判断接下来需要哪种代码，Python 还是 JavaScript？
3. 使用选中的语言编写单元测试，看着它失败。
4. 使用选中的语言编写一些代码，让测试通过。
5. 重复上述步骤。

### 13.6 经验做法：onload 样板代码和命名空间

最后还有一件事。如果 JavaScript 需要和 DOM 交互，最好把相应的代码包含在 onload 样板代码中，确保在执行脚本之前完全加载了页面。目前的做法也能正常运行，因为我们把 `<script>` 标签放在页面的底部，但不能依赖这种方式。

jQuery 提供的 onload 样板代码非常简洁：

```javascript
// static/list.js
$(document).ready(function (){
  $('input').on('keypress', function() {
    $('.has-error').hide();
  });
});
```

此外，还使用了 jQuery 提供的神奇 $ 函数，但是其他 JavaScript 库可能也会使用这个名字。$ 其实是 jQuery 的别名，jQuery 这个名字在其他库很少会用到，所以更精确地控制命名空间的标准方法如下：

```javascript
jQuery(document).ready(function ($) {
  $('input').on('keypress', function(){
    $('.has-error').hide();
  });
});
```

更多信息请阅读 jQuery.read() 的[文档](http://api.jquery.com/ready/)。

#### 个人实践

```
郁闷了,能通过单元测试的代码没法通过 Python 的功能测试, 能通过功能测试的代码没法通过单元测试. 后来我灵机一动, 两种方法都用上不就两个测试都能过了吗...这算啥- -, 现在提交的版本是两个都用上的版本
```

### 13.7 一些缺憾

* 选择符 $(input) 的作用太大了，它为页面中所有的 input 元素都附上了事件句柄。
* 目前，测试只检查 JavaScript 能否在一个页面中使用。JavaScript 能使用，是因为在 base.html 中引入了 JavaScript 文件。如果只在 home.html 中引入 JavaScript 文件，测试也能通过。你可以选择在哪个文件中引入，但也可以再编写一个测试。

> ### JavaScript 测试笔记
>
> * Selenium 最大的优势之一是可以测试 JavaScript 是否真的能使用，就像测试 Python 代码一样。
> * JavaScript 测试运行库有很多，QUnit 和 jQuery 联系紧密
> * QUnit 主要希望你在真正的 Web 浏览器中运行测试，这就带来一个好处，可以方便地创建一些 HTML 固件，匹配网站中真正含有的 HTML，在测试中使用
> * JavaScript 其实也可以很有趣。不过还是要再说一次：一定要阅读《JavaScript 语言精神》