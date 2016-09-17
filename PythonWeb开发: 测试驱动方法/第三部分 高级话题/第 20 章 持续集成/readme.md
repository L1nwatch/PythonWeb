## 第 20 章 持续集成

运行功能测试时间太长，为了避免发生这种情况，可以搭建一个“持续集成”（Continuous Integration，简称 CI）服务器，自动运行功能测试。这样，在日常开发中，只需运行当下关注的功能测试，整个测试组件则交给 CI 服务器自动运行。如果不小心破坏了某项功能，CI 服务器会通知我们。单元测试的运行速度一直很快，每隔几秒就可以运行一次。

Jenkins 使用 Java 开发，经常出问题，界面也不漂亮，但大家都在用，而且插件系统很棒，下面安装并运行 Jenkins。

### 20.1 安装 Jenkins

CI 托管服务有很多，基本上都提供了一个立即就能使用的 Jenkins 服务器。比如有 `Sauce Labs`、`Travis`、`Circle-CI` 和 `ShiningPanda`，可能还有更多。假设要在自己有控制权的服务器上安装所需的一切软件。

> 把 Jenkins 安装在过渡服务器或生产服务器上可不是个好主意，因为有很多操作要交给 Jenkins 完成，比如重新引导过渡服务器。

要从 Jenkins 的官方 apt 仓库中安装最新版，因为 Ubuntu 默认安装的版本对本地化和 Unicode 支持还有些问题，而且默认配置也没监听外网：

```shell
# 从 Jenkins 网站上查到的安装说明
wget -q -O - http://pkg.jenkins.io/debian-stable/jenkins.io.key | sudo apt-key add -
echo deb http://pkg.jenkins.io/debian-stable binary/ | sudo tee /etc/apt/sources.list.d/jenkins.list
sudo apt-get update
sudo apt-get install jenkins
```

还要安装几个依赖：

```shell
sudo apt-get install git firefox python3 python-virtualenv xvfb
```

> shiningpanda 插件可能不兼容 3.4，但在 Python 3.3 中可以正常使用。可以考虑使用 Ubuntu Saucy（13.10），但不用 Trusty（14.04）。

然后就可以访问服务器的 URL，通过 8080 端口访问 Jenkins。

直接访问`localhost:8080`，然后会要求输入一个密码，这个密码在所给路径的文件中，cat 一下那个文件就可以得到密码了。

#### 20.1.1 Jenkins 的安全配置

首先，我们要设置一些认证措施，因为我们的服务器通过外网可以访问：

* `Manage Jenkins（管理 Jenkins) -> Configure Global Security（全局安全配置） -> Enable security（启用安全措施）`；
* 选择 "Jenkins' own user database"（Jenkins 自己的用户数据库），以及 "Matrix-based security"（基于矩阵的安全措施）；
* 取消匿名用户的所有权限；
* 然后为自己添加一个用户，并且赋予所有权限；
* 下一个页面会显示一些输入框，为刚才添加的用户创建账户，还要设定密码；


### 20.1.2 添加需要的插件

接下来安装一些插件，提供 Git、Python 和虚拟显示器支持。

* `Manage Jenkins（管理 Jenkins） -> Manage Plugins（管理插件） -> Available（可用插件）`
* 要安装的插件是：
  * Git
  * ShiningPanda
  * Xvfb

***

发现自己上不去，以下是解决办法：

```python
Go to Manage Jenkins->Configure Global Security
Click the checkbox for "Use browser for metadata download"
```

好吧，发现虽然能获取 List 了，但是下载依旧失败，手动吧。到[网址](http://updates.jenkins-ci.org/download/plugins/)查找下载。

或者换个[镜像](https://mirrors.tuna.tsinghua.edu.cn/jenkins/)更好一些，另外还是要开启上面那个选项。可能下载有哈希错误，换个网络，比如用手机开网试一下。

***

安装这么几个插件：

```shell
#structs
https://updates.jenkins-ci.org/download/plugins/structs/
# Pipeline: Step API
https://updates.jenkins-ci.org/download/plugins/pipeline-build-step/
#Credentials Plugin
http://updates.jenkins-ci.org/download/plugins/credentials/
#SSH Credentials Plugin
http://updates.jenkins-ci.org/download/plugins/ssh-credentials/
#Git Client Plugin
http://updates.jenkins-ci.org/download/plugins/git-client/
#SCM API Plugin
http://updates.jenkins-ci.org/download/plugins/scm-api/
#Git Plugin
http://updates.jenkins-ci.org/download/plugins/git/
#Xvfb Plugin
http://updates.jenkins-ci.org/download/plugins/xvfb/
# ShiningPanda
http://updates.jenkins-ci.org/download/plugins/shiningpanda/
```

安装完成后重启 Jenkins——可以在下个页面中勾选相应按钮，也可以在命令行中执行 `sudo service jenkins restart` 命令。

#### 告诉 Jenkins 到哪里寻找 Python3 和 Xvfb

要告诉 ShiningPanda 插件 Python3 安装在哪里，可以执行 `which python3` 查看。

在 `Global Tool Configuration` 里面进行配置。

### 20.2 设置项目

* Git 仓库填写

* 设为每小时轮询一次（Poll SCM：`H * * * *`）

* 在 Python3 虚拟环境中运行测试

* 单元测试和功能测试分开运行

* `Build Virtualenv Builder`

* 以下功能测试放在一起执行会报完整性错误，所以只好分开来写了

* ```python
  pip install -r virtualenv/requirements.txt
  pip install -U selenium
  mkdir -p database
  python todo_app/manage.py makemigrations
  python todo_app/manage.py migrate
  python todo_app/manage.py test lists accounts
  python todo_app/manage.py test functional_tests.test_login
  python todo_app/manage.py test functional_tests.test_my_lists
  python todo_app/manage.py test functional_tests.test_layout_and_styling
  python todo_app/manage.py test functional_tests.test_simple_list_creation
  python todo_app/manage.py test functional_tests.test_list_item_validation
  ```

### 20.3 第一次构建

点击 “Build Now！”，然后查看 "Console Output"。发现说浏览器无法连接。

> 有些人喜欢使用 test-requirements.txt 文件指定测试（不是主应用）需要的包。

### 20.4 设置虚拟显示器，让功能测试能在无界面的环境中运行

从调用跟踪中可以看出，Firefox 无法启动，因为服务器没有显示器。

这个问题有两种解决方法。第一种，换用无界面浏览器（headless browser），例如 PhantomJS 或 SlimerJS。这种工具绝对有存在的意义，最大的特点是运行速度快，但也有缺点。首先，它们不是真正的 Web 浏览器，所以无法保证能捕获用户使用真正的浏览器时遇到的全部怪异行为。其次，它们在 Selenium 中的表现差异很大，需要重新编写功能测试。

> 作者只把无界面浏览器当做开发工具，目的是在开发者的设备中提升功能测试的运行速度。在 CI 服务器上运行测试则使用真正的浏览器。

第二种方法是设置虚拟显示器：让服务器以为自己连接了显示器，这样 Firefox 就能正常运行了。这种工具很多，我们要使用的是 "Xvfb"(X Virtual Framebuffer)，因为它安装和使用都很简单，而且还有一个合用的 Jenkins 插件。

在 `Configure` 配置选项卡中找到 `Build Environment` 构建环境，勾选 `Start Xvfb before the build, and shut it down after.` 即可。（如果想在 Python 代码中控制虚拟显示器，可以试试 pyvirtualdisplay。

可以试一下在 `Build Environment` 中把这一项 `Let Xvfb choose display name` 勾选上，就不会看到 `selenium.common.exceptions.WebDriverException: Message: The browser appears to have exited before we could connect. If you specified a log_file in the FirefoxBinary constructor, check it for details.` 错误了。

接下来，为了调试错误，还需要截图。

### 20.5 截图

为了调试远程设备中意料之外的失败，最好能看到失败时的屏幕图片，或者还可以转储页面的 HTML。这些操作可在功能测试类中的 tearDown 方法里自定义逻辑实现。为此，要深入 unittest 的内部，使用私有属性 `_outcomeForDoCleanups`，不过下面这样写也是可以的：

```python
# functional_tests/base.py
import os
from datetime import datetime
SCREEN_DUMP_LOCATION = os.path.abspath(
	os.path.join(os.path.dirname(__file__), "screendumps")
)
[...]

def tearDown(self):
    if self._test_has_failed():
        if not os.path.exists(SCREEN_DUMP_LOCATION):
            os.makedirs(SCREEN_DUMP_LOCATION)
        for ix, handle in enumerate(self.browser.window_handles):
            self._windowid = ix
            self.browser.switch_to_window(handle)
            self.take_screenshot()
            self.dump_html()
    self.browser.quit()
    super().tearDown()
    
def _test_has_failed(self):
    # 针对 3.4。在 3.3 中可以直接使用 self._outcomeForDoCleanups.success:
    for method, error in self._outcome.errors:
        if error:
            return True
    return False
```

首先，必要时创建存放截图的目录。然后，遍历所有打开的浏览器选项卡和页面，调用一些 Selenium 提供的方法（`get_screen shot_as_file 和 browser.page_source`）截图以及转储 HTML：

```python
# functional_tests/base.py
def take_screenshot(self):
    filename = self._get_filename() + ".png"
    print("screenshotting to", filename)
    self.browser.get_screenshot_as_file(filename)
    
def dump_html(self):
    filename = self._get_filename() + ".html"
    print("dumping page HTML to", filename)
    with open(filename, "w") as f:
        f.write(self.browser.page_source)
```

最后，使用一种方式生成唯一的文件名标识符。文件名中包括测试方法和测试类的名字，以及一个时间戳：

```python
# functional_tests/base.py
def _get_filename(self):
    timestamp = datetime.now().isoformat().replace(":", ".")[:19]
    return "{folder}/{classname}.{method}-window{windowid}-{timestamp}".format(folder=SCREEN_DUMP_LOCATION,classname=self.__class__.__name__,method=self._testMethodName,windowid=self._windowid,timestamp=timestamp)
```

可以现在本地测试一下，故意让某个测试失败，然后观察输出。

之后提交改动：

```shell
git diff # 显示 base.py 中的改动
echo "functional_tests/screendumps" >> .gitignore
git commit -am "add screenshot on failure to FT runner"
git push
```

之后在 Jenkins 中重建构建时，会看到对应的输出。

可以在“工作空间”中查看我们输出的文件。工作空间是 Jenkins 用来存储源码以及运行测试所在的文件夹。

然后查看截图，尝试找出错误。

### 20.6 一个常见的 Selenium 问题：条件竞争

只要在 Selenium 测试中遇到莫名其妙的失败，最说得通的解释是其中隐含了条件竞争。看一下导致失败的那几行测试：

```python
# functional_tests/test_my_lists.py
# 她看到这个页面中有她创建的清单
# 而且清单根据第一个待办事项命名
self.browser.find_element_by_link_text("Reticulate_splines").click()
self.assertEqual(self.browser.current_url, first_list_url)
```

点击 "Reticulate splines" 之后，立即让 Selenium 检查当前页面的 URL 是否和第一个清单的 URL 相同。实际并不相同。

第二章为浏览器设置了 `implicitly_wait`，这种做法并不可靠。对 Selenium 的 `find_element_` 这类方法来说，`implicitly_wait` 还算能够正常运行，但 `browser.current_url` 就不行了。Selenium 点击某个元素后不会等待一段时间，所以浏览器还没完全加载新页面，`current_url` 也就仍是前一个的页面的 URL。需要使用复杂一些的等待代码，类似于在各个 Persona 页面中使用的那种。

现在可以定义一个辅助函数，实现等待功能。

```python
# functional_tests/test_my_lists.py
# 她看到这个页面中有她创建的清单
# 而且清单根据第一个待办事项命名
self.browser.find_element_by_link_text("Reticulate_splines").click()
self.wait_for(
	lambda: self.assertEqual(self.browser.current_url, first_list_url)
)
```

把 assertEqual 变成一个匿名函数，然后传给 `wait_for` 辅助方法。

```python
# functional_tests/base.py
import time
from selenium.common.exceptions import WebDriverException
[...]

def wait_for(self, function_with_assertion, timeout=DEFAULT_WAIT):
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            return function_with_assertion()
        except (AssertionError, WebDriverException):
            time.sleep(0.1)
    # 再试一次，如果还不行就抛出所有异常
    return function_with_assertion()
```

`wait_for` 试着运行传入的函数，如果断言失败，它不会让测试失败，而是捕获 assertEqual 通常会抛出的 AssertionError 异常，之后再循环重新运行。while 循环会一直运行下去，直到超过指定的超时时间为止。`wait_for` 还会捕获因为页面中没出现某个元素等原因导致的 WebDriverException 异常。超时时间到达后，`wait_for` 还会再运行一次断言试试，不过这一次没放入 `try/except` 语句中，所以如果真遇到了 AssertionError 异常，测试就会按照相应的方式失败。

> 我们知道，Selenium 提供了 WebdriverWait 作为一种实现等待的工具，但是用起来有点儿限制。而自己动手编写的版本，接收一个运行 unittest 断言的函数，所以能看到断言输出的、易读的错误消息。

超时时间是个可选参数，其默认值是一个常量。下面就在 `base.py` 中添加，另外在原先的 `implicitly_wait` 方法中也使用这个常量。

自己测试一下，发现可以生效，然后就可以提交了：

```shell
git diff # base.py, test_my_lists.py
git commit -am "Use wait_for function for URL checks in my_lists"
git push
```

 之后可以发现 Jenkins 使用蓝色表示构建成功。

### 20.7 使用 PhantomJS 运行 QUnit JavaScript 测试

还有 JavaScript 测试。现在的 “测试运行程序” 是真正的 Web 浏览器。若想在 Jenkins 中运行 JavaScript 测试，需要一种命令行测试运行程序。

#### 20.7.1 安装 node

安装方法参见 `node.js` 中的说明。Windows 和 Mac 系统都有安装包，Linux 也有各自的包。（自己是直接下载 Linux 32bits 的 binary 包）

安装好 node 之后，可以执行下面的命令安装 PhantomJS。

```shell
npm install -g phantomjs # -g 的意思是系统全局安装。可能需要使用 sudo
# 被 GFW 搞得安装好慢，执行下面这条好多了：
PHANTOMJS_CDNURL=https://npm.taobao.org/dist/phantomjs ./npm install phantomjs --registry=https://registry.npm.taobao.org --no-proxy
```

接下来要下载 QUnit/PhantomJS 测试运行程序。测试运行程序有很多，不过最好使用 [QUnit 插件页面](http://qunitjs.com/plugins/)提到的那个。这个运行程序的[仓库地址](https://github.com/jonkemp/qunit-phantomjs-runner)，只需要一个文件，`runner.js`。

最终得到的文件夹结构如下：

```shell
superlists/static/tests/
|--- qunit.css
|--- qunit.js
|--- runner.js
|___ sinon.js
```

试一下运行这个程序：

```shell
phantomjs superlists/static/tests/runner.js lists/static/tests/tests.html
phantomjs superlists/static/tests/runner.js accounts/static/tests/tests.html
```

保险起见，故意破坏一个测试：

```javascript
// lists/static/list.js
$("input").on("keypress", function () {
  //$(".has-error").hide();
});
```

可以看到测试果然失败了。

```shell
phantomjs superlists/static/tests/runner.js lists/static/tests/tests.html
```

接下来可以提交并推送运行程序，然后将其添加到 Jenkins 的构建步骤中。

```shell
git checkout lists/static/list.js
git add superlists/static/tests/runner.js
git commit -m "Add phantomjs test runner for javascript tests"
git push
```

#### 20.7.2 在 Jenkins 中添加构建步骤

再次编辑项目配置，为每个 JavaScript 测试文件添加一个构建步骤，还要在服务器中安装 PhantomJS。

```shell
sudo apt-get repository -y ppa:chris-lea/node.js
sudo apt-get update
sudo apt-get install nodejs
sudo npm install -g phantomjs
```

至此，编写了完整的 CI 构建步骤，能运行所有测试！

### 20.8 CI 服务器能完成的其他操作

Jenkins 和 CI 服务器的作用还有很多，比如可以让 CI 服务器在监控仓库的新提交方面变得更智能。

除了运行普通的功能测试之外，还可以使用 CI 服务器自动运行过渡服务器中的测试。如果所有功能测试都能通过，你可以添加一个构建步骤，把代码部署到过渡服务器中，然后在过渡服务器中再运行功能测试。

有些人甚至使用 CI 服务器把最新发布的代码部署到生产服务器中。

> #### CI 和 Selenium 最佳实践
>
> * 尽早为自己的项目搭建 CI 服务器
>   * 一旦运行功能测试所花的时间超过几秒钟，就应该考虑把这个任务交给 CI 服务器了，确保所有测试都能在某处运行
> * 测试失败时截图和转储 HTML
>   * 如果你能看到测试失败时网页时什么样，调试就容易多了。截图和转储 HTML 有助于调试 CI 服务器中的失败，而且对本地运行的测试也很有用。
> * 在 Selenium 测试中等待一段时间
>   * Selenium 提供的 `implicitly_wait` 只能用于 `find_element_`这类函数，但也不可靠（也能找到前一个页面中的元素）。定义一个辅助函数 `wait_for` ，在网站中执行的两次操作之间调用，然后等待一段时间，让操作生效。
> * 想办法把 CI 和过渡服务器连接起来
>   * 使用 `LiveServerTestCase` 的测试在开发环境中不会遇到什么问题，但若想得到十足的保障，就要在真正的服务器中运行测试。想办法让 CI 服务器把代码部署到过渡服务器中，然后在过渡服务器中运行功能测试。这么做还有个附带好处：测试自动化部署脚本是否可用。





