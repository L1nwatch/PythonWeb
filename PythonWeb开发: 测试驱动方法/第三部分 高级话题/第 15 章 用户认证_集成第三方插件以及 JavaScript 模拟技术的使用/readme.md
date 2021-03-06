## 第 15 章 用户认证、集成第三方插件以及 JavaScript 模拟技术的使用

用户需要的是某种用户账户系统，那么就直接实现认证功能吧。

我们不会费力气自己存储密码，这是上世纪 90 年代的技术，而且存储用户密码还是个安全噩梦，所以还是交给第三方去完成吧。我们要使用一种联合认证系统（Federated Authentication System）。

如果你坚持要自己存储密码，可以使用 Django 提供的 auth 模块。这个模块很友好也很简单，具体的实现方法留给你自己去发掘。

本章会深入介绍一种测试技术，即”模拟“（mocking）。这一章会在 JavaScript 代码中多次用到模拟技术，下一章还要在 Python 代码中使用。

### 15.1 Mozilla Persona（BrowserID） 

要使用哪种联合认证系统呢？Oauth，Openid，还是”使用 Facebook 登录“？这些认证系统对于本书来说都有让人无法接受的负面作用。Mozilla 的开发者研发了一种注重隐私的认证机制，叫”Persona“，也叫”BrowserID“。

这种机制的原理是，把 Web 浏览器作为中间人，连接想要检查 ID 的网站和作为 ID 担保人的网站。ID 担保人可以是谷歌或 Facebook 等任何网站，Persona 使用的协议很明智，它们觉不知道你登陆过哪些网站以及何时登录。

Persona 最终可能无法成为认证平台，但不管集成哪种第三方认证系统，都要做到以下几点：

* 不测试别人的代码和 API
* 但要测试是否正确地把它们集成到自己的代码中
* 从用户的角度出发，检查一切是否可以正常运行
* 测试第三方系统不可用时你的网站是否能优雅降级

### 15.2 探索性编程（又名”探究“）

我们可以使用单元测试探索新 API 的用法。但有时你不想写测试，只是想捣鼓一下，看 API 是否能用，目的是学习和领会。这么做绝对可行。学习新工具，或者研究新的可行性方案时，一般都可以适当地把严格的 TDD 流程放在一边，不编写测试或编写少量的测试，先把基本的原型开发出来。

这种创建原型的过程一般叫做[”探究“（spike）](http://stackoverflow. com/questions/249969/why-are-tdd-spikes-called-spikes)。

首先，作者研究了一个现有的 `Django-Persona` 集成方案——[Django-BrowserID](https://github. com/mozilla/django-browserid)，可惜它不支持 Python3（2013 年的时候）。

你应该自己动手，把这些代码加到自己的网站中，这样才能得到试验的对象，然后使用自己的电子邮件地址登录试试，证明这些代码确实可用。

#### 15.2.1 为此次探究新建一个分支

着手探究之前，最好新建一个分支，这样就不用担心探究过程中提交的代码把 VCS 中的生产代码搞乱了：

```shell
git checkout -b persona-spike
```

#### 15.2.2 前端和 JavaScript 代码

先从前端入手。直接从 Persona 网站和 Dan 的幻灯片中复制粘贴代码，然后做少量修改：

```html
<!-- lists/templates/base.html -->
<script src="http://code.jquery.com/jquery.min.js"></script>
<script src="/static/list.js"></script>
<script src="https://login.persona.org/include.js"></script>
<script>
    $(document).ready(function () {
        var loginLink = document.getElementById("login");
        if (loginLink) {
            loginLink.onclick = function () {
                navigator.id.request();
            };
        }


        var logoutLink = document.getElementById("logout");
        if (logoutLink) {
            logoutLink.onclick = function () {
                navigator.id.logout();
            };
        }

        var currentUser = '{{ user.email }}' || null;

        var cstf_token = '{{ csrf_token }}';
        console.log(currentUser);

        navigator.id.watch({
            loggedInUser: currentUser,
            onlogin: function (assertion) {
                $.post('/accounts/login', {assertion: assertion, csrfmiddlewaretoken: csrf_token})
                        .done(function () {
                            window.location.reload();
                        })
                        .fail(function () {
                            navigator.id.logout();
                        })
            },
            onlogout: function () {
                $.post('/accounts/logout')
                        .always(function () {
                            window.location.reload();
                        });
            }
        });
    });
</script>
```

Persona 的 JavaScript 库提供了一个特殊的对象 `navigator.id`，把这个对象的 request 方法绑定到登录链接上（登录链接放在页面顶部），再把这个对象的 logout 方法绑定到退出链接上：

```html
<!-- lists/templates/base.html -->
<body>
<div class="container">
    <div class="navbar">
        {% if user.email %}
            <p>Logged in as {{ user.email }}</p>
            <p><a id="logout" href="{% url 'logout' %}">Sign out</a></p>
        {% else %}
            <a href="#" id="login">Sign in</a>
        {% endif %}
        <p>User: {{ user }}</p>
    </div>
    <div class="row">
      [...]
```

#### 15.2.3 `Browser-ID` 协议

现在，如果用户点击登录链接，Persona 会弹出它的认证对话框。接下来，用户输入电子邮件地址之后，浏览器负责验证电子邮件地址——把用户引导到电子邮件供应商的网站（谷歌、雅虎等），让供应商验证电子邮件。

假设我们使用的是谷歌电子邮箱，谷歌会要求用户输入用户名和密码，还可能要做两步认证，以此向浏览器确认你是不是你所声称的那个人。然后谷歌向浏览器返回一个证书，包含用户的电子邮件地址。这个证书有密码签名，以证明是由谷歌签发的。

然后，Persona 把证书和想要登录的网站域名一起存入一个叫做“判定数据”的二进制文件（即 assertion），再把这个二进制文件发送给网站进行验证。

现在代码执行到 `navigator.id.request` 和 `navigator.id.watch` 的 `onlogin` 回调之间——通过 POST 请求把判定数据发送给网站的登录 URL。

要在服务器端验证传入的判定数据，看它是否能证明用户确实拥有这个电子邮件地址。服务器之所以能验证，是因为谷歌使用它的公钥对判定数据进行了部分签名。可以自己编写代码解码，也可以使用 Mozilla 提供的公共服务完成。

> 是的，交给 Mozilla 完成完全违背了保护隐私的初衷，但这是惯用的方式。如果需要，也可以自己做。Mozilla 的[网站](https://developer.mozilla.org/en-US/docs/Mozilla/Persona/Protocol_Overview)中有详细说明，其中包括各种聪明的公钥加密方式，能防止谷歌知道你想登录的网站，还能避免重放攻击等。

#### 15.2.4 服务器端：自定义认证机制

接下来，启动要实现账户系统的应用：

```shell
python3 manage.py startapp accounts
```

发给 `accounts/login` 的 POST 请求由下面这个视图处理：

```python
# accounts/views.py
import sys
from django.contrib.auth import authenticate
from django.contrib.auth import login as auth_login
from django.shortcuts import redirect


def login(request):
    print("login view", file=sys.stderr)
    # user = PersonAuthenticationBackend().authenticate(request.POST['assertion'])
    user = authenticate(assertion=request.POST['assertion'])
    if user is not None:
        auth_login(request, user)
    return redirect('/')
```

这是 authenticate 函数，它以自定义的 Django ”认证后台“形式实现（虽然可以在视图中实现，但使用后台是 Django 推荐的做法。这么做可以在其他应用中重用认证系统，比如说管理后台）。

```python
# accounts/authentication.py
import requests
import sys
from accounts.models import ListUser

class PersonAuthenticationBackend(object):
    def authenticate(self, assertion):
      # 把判定数据发给 Mozilla 的验证服务
      data = {'assertion':assertion, 'audience':'localhost'}
      print('sending to mozilla', data, file=sys.stderr)
      resp = requests.post('https://verifier.login.persona.org/verify', data=data)
      print('got', resp.content, file=sys.stderr)

      # 验证服务是否有响应？
      if resp.ok:
          # 解析响应
          verification_data = resp.json()

          # 检查判定数据是否有效
          if verification_data['status'] == 'okay':
              email = verification_data['email']
              try:
                  return self.get_user(email)
              except ListUser.DoesNotExist:
                  return ListUser.objects.create(email=email)
	
    def get_user(self, email):
        return ListUser.objects.get(email=email)
```

从解说性的注释可以看出，这段代码是直接从 Mozilla 的网站上复制粘贴过来的。

需要执行 `pip install requests` 命令把 `requests` 库（`http://docs.python-requests.org/`）安装到虚拟环境中。

为了完成 Django 中自定义认证后台的操作，还需要一个自定义用户模型：

```python
# accounts/models.py
from django.contrib.auth.models import AbstractBaseUser, PermissionMixin
from django.db import models

class ListUser(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(primary_key=True)
    USERNAME_FIELD = 'email'
    # REQUIRED_FIELDS = ['email', 'height']

    objects = ListUserManager()

    @property
    def is_staff(self):
        return self.email == 'harry.percival@example.com'

    @property
    def is_active(self):
        return True
```

> 这个模型只有一个字段，没有多余的名字、姓和用户名字段，显然也没有密码字段——密码由他人代为存储。这就是被称作最简用户模型的原因。不过，从注释掉的代码行和硬编码的电子邮件地址可以看出，这段代码不能在生产中使用。

此时，建议你稍微浏览一下 Django 的[认证文档](https://docs.djangoproject.com/en/1.7/)。

除此之外，还要为用户提供一个模型管理器：

```python
# accounts/models.py
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin

class ListUserManager(BaseUserManager):
    def create_user(self, email):
        ListUser.objects.create(email=email)
    
    def create_superuser(self, email, password):
        self.create_user(email)
```

退出视图如下：

```python
# accounts/views.py
from django.contrib.auth import login as auth_login, logout as auth_logout
[...]

def logout(request):
    auth_logout(request)
    return redirect('/')
```

然后定义这两个视图的 URL 映射：

```python
# superlists/urls.py
urlpatterns = [
    # url(r'^admin/', admin.site.urls),
    url(r"^$", "lists.views.home_page", name="home"),
    url(r"^lists/", include("lists.urls")),
    url(r'^accounts/', include('accounts.urls')),
]
```

再修改下面这个文件：

```python
# accounts/urls.py
from django.conf.urls import patterns, url

urlpatterns = patterns('',
                      url(r'^login$', 'accounts.views.login', name='login'),
                      url(r'^logout$', 'accounts.views.logout', name='logout'),)
```

接着还要在 `settings.py` 中启用认证后台和刚编写好的账户应用：

```python
# superlists/settings.py
INSTALLED_APPS = (
	# 'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'lists',
    'accounts',
)

AUTH_USER_MODEL = 'accounts.ListUser'
AUTHENTICATION_BACKENDS = (
	'accounts.authentication.PersonAuthenticationBackend',
)

MIDDLEWARE_CLASSES = (
[...]
```

然后执行 `makemigrations` 命令，让刚才定义好的用户模型生效。

再执行 `migrate` 命令，更新数据库。

> 如果手动调试时 Persona 不起作用，而且在终端里看到 "audience mismatch" 错误，确认你访问网站使用的地址是：`http://localhost:8000`，而不是 `127.0.0.1`。

> ### 旁注：把日志输出到标准错误
>
> 探究时最好能看到代码抛出的异常。Django 默认情况下并没有把所有异常都输送到终端，不过可以在 `settings.py` 中使用 `LOGGING` 变量让 Django 这么做：
>
> ```python
> # superlists/settings.py
> LOGGING = {
>   'version': 1,
>   'disable_existing_loggers': False,
>   'handlers': {
>     'console': {
>       'level': 'DEBUG',
>       'class': 'logging.StreamHandler',
>     },
>   },
>   'loggers': {
>     'django': {
>       'handlers': ['console'],
>     },
>   },
>     'root': {'level': 'INFO'},
> }
> ```
>
> Django 使用 Python 标准库中的企业级日志模块。这个模块虽然功能完善，但学习曲线十分陡峭。

现在我们实现了一个可用的解决方案，把这些代码提交到探究时使用的分支吧：

```shell
git status
git add accounts
git commit -am "spiked in custom auth backend with persona"
```

现在该去掉探究代码了。

###  去掉探究代码

去掉探究代码意味着要使用 TDD 重写原型代码。第一步是编写功能测试先。

我们还得继续待在 `persona-spike` 分支中，看功能测试能否在探究代码中通过，然后再回到 master 分支，并且只提交功能测试。

功能测试的大纲如下：

```python
# functional_tests/test_login.py
from .bash import FunctionalTest

class LoginTest(FunctionalTest):
    def test_login_with_persona(self):
        # Y 访问这个很棒的超级列表网站
        # 第一次注意到 "Sign in" 链接
        self.browser.get(self.server_url)
        self.browser.find_element_by_id('login').click()

        # 出现一个 Persona 登录框
        # 需要辅助函数，它们都用于实现 Selenium 测试中十分常见的操作：等待某件事发生。
        self.switch_to_new_window("Mozilla Persona")

        # Y 使用她的电子邮件地址登录
        ## 测试中的电子邮件使用 mockmyid.com
        # 可以使用如下方法查找 Persona 电子邮件输入框的 ID：手动打开网站，使用 Firefox 调试工具条(`Ctrl + Shift + I`)
        # 这里没有使用真实的电子邮件地址，而是用虚拟工具生成的地址，因此不用在邮件服务供应商的网站上填写认证信息。虚拟工具可以使用 MockMyID 或者 Persona Test User
        self.browser.find_element_by_id("authentication_email").send_keys("edith@mockmyid.com")
        self.browser.find_element_by_tag_name("button").click()

        # Persona 窗口关闭
        self.switch_to_new_window("To-Do")

        # 她发现自己已经登录
        # 需要辅助函数，它们都用于实现 Selenium 测试中十分常见的操作：等待某件事发生。
        self.wait_for_element_with_id("logout")
        navbar = self.browser.find_element_by_css_selector(".navbar")
        self.assertIn("edith@mockmyid.com", navbar.text)
```

> ### 评估第三方系统的测试基础设施
>
> 测试是评估第三方系统的一部分。集成外部服务时，要想清楚如何在功能测试中使用这项服务。
>
> 测试通常可以使用和真实环境中一样的服务，但有时需要使用第三方服务的“测试”版本。集成 Persona 时，本可以使用真实的电子邮件地址。比如说写一个功能测试访问 Yahoo.com，然后使用注册的临时账户登录。这么做有个问题，功能测试怎么写完全取决于 Yahoo 的电子邮件登录界面，而这个界面随时可能变化。
>
> 使用 MockMyID 或 Persona Test User 就不同了。这两个工具在 Persona 的文档中都提到过，使用起来非常顺畅，因此我们只需测试集成的重要部分。
>
> 再看一个更严重的问题，支付系统。如果要开始整合支付，支付系统就会成为网站最重要的部分之一，因此必须充分测试。但是你并不想每次运动功能测试时都使用真实的信用卡交易。所以大多数支付服务供应商都提供了测试板支付 API。不过各家供应商提供的测试版 API 质量参差不齐，所以一定要仔细研究。

#### 15.3.1 常用 Selenium 技术：显示等待

实现“等待”功能的两个辅助函数之一如下所示：

```python
# functional_tests/test_login.py
import time
[...]

    def switch_to_new_window(self, text_in_title):
        retries = 60
        while retries > 0:
            for handle in self.browser.window_handles:
                self.browser.switch_to_window(handle)
                if text_in_title in self.browser.title:
                    return
            retries -= 1
            time.sleep(0.5)
        self.fail("could not find window")
```

在这个辅助函数中，我们自己动手实现等待机制：循环访问当前打开的所有浏览器窗口，查找有指定标题的那个。如果找不到，稍等一会再试，并且减少重试次数计数器。

这种功能在 Selenium 测试中经常会用到，因此开发团队创建了等待 API。不过这个 API 无法适用于所有情况，所以才在这个辅助函数中自己动手实现等待机制。实现更简单的等待时可以使用 WebDriverWait 类，比如说等待具有指定 ID 的元素出现在页面中，可以这么写：

```python
# functional_tests/test_login.py
from selenium.webdriver.support.ui import WebDriverWait
[...]

def wait_for_element_with_id(self, element_id):
    WebDriverWait(self.browser, timeout=30).until(
        lambda b: b.find_element_by_id(element_id)
    )
```

这就是 Selenium 所谓的“显示等待”。我们已经在 `FunctionalTest.setUp` 中定义了一个“隐式等待”。当时设定只等待 3 秒，大多数情况下这段时间已经够用了，但等待 Persona 等外部服务时，有时要延长等待时间。

[Selenium 文档](http://docs.seleniumhq.org/docs/04_webdriver_advanced.jsp)中有更多的示例，不过阅读[源码](http://code.google.com/p/selenium/source/browse/py/selenium/)也许会更直观，因为代码中的文档字符串写得很好。

> `implicitly_wait` 并不可靠，尤其是涉及 JavaScript 代码时。如果功能测试要检查页面中的异步交互，最好使用 `wait_for_element_wit_id` 方法中的方式。

运行这个功能测试会发现，我们的做法是可行的：

```python
python3 manage.py test functional_tests.test_login
```

你甚至还会看到视图留下的调试信息。现在撤销全部临时改动，使用测试驱动的方式一步步重新实现。

#### 15.3.2 删除探究代码

```shell
git checkout master # 切换到 master 分支
rm -rf accounts # 删除所有探究代码
git add functional_tests/test_login.py
git commit -m "FT for login with Persona"
```

然后再次运行功能测试，让它驱动开发：

```shell
python3 manage.py test functional_tests.test_login
```

测试首先要求添加一个登录链接。在 HTML ID 前加上 `id_` 。这是一种传统做法，便于区分 HTML 和 CSS 中的类和 ID。先稍微修改一下功能测试：

```python
# functional_tests/test_login.py
self.browser.find_element_by_id("id_login").click()
[...]
self.wait_for_element_with_id("id_logout")
```

然后添加一个没有实际作用的登录链接。Bootstrap 为导航条提供了原生的类，可以拿来使用：

```html
<!-- lists/template/base.html -->
<div class="container">
  <nav class="navbar navbar-default" role="navigation">
  	<a class="navbar-brand" href="/">Superlists</a>
    <a class="btn navbar-btn navbar-right" id="id_login" href="#">Sign in</a>
  </nav>
</div>

<div class="row">
[...]
```

等待 30 秒之后，测试出现了如下错误：

```python
AssertionError: could not find window
```

得到了测试的授权，可以进入下一步了：编写更多的 JavaScirpt 代码。

### 15.4 涉及外部组件的 JavaScript 单元测试：首次使用模拟技术

为了让功能测试继续向下运行，需要弹出 Persona 窗口。为此，要去除客户端 JavaScript 中的探究代码，换用 Persona 代码库。在这个过程中，要使用 JavaScript 单元测试和模拟技术驱动开发。

#### 15.4.1 整理：全站共用的静态文件夹

首先要做些整理工作：在 `superlists/superlists` 中创建一个全站共用的静态文件目录，把所有 Bootstarp 的 CSS 文件、QUnit 代码和 base.css 都移到这个目录中。移动之后应用的文件夹结构如下所示：

```shell
tree todo_app -L 3 -I __pycache__
todo_app
├── __init__.py
├── settings.py
├── static
│   ├── base.css
│   ├── bootstrap
│   │   ├── css
│   │   ├── fonts
│   │   └── js
│   └── tests
│       ├── qunit.css
│       └── qunit.js
├── urls.py
└── wsgi.py
```

> 执行这种工作前后一定要提交。

文件位置变了，所以要调整现有的 JavaScript 单元测试：

```html
<!-- lists/static/tests/tests.html -->
<link rel="stylesheet" href="../../../superlists/static/tests/qunit.css">

[...]

<script src="http://code.jquery.com/jquery.min.js"></script>
<script src="../../../superlists/static/tests/qunit.js"></script>
<script src="../list.js"></script>
```

可以在浏览器中打开这些单元测试，检查是否仍能正常使用。

我们要在设置文件中指定新的静态文件夹地址：

```python
# superlists/settings.py
STATIC_ROOT = os.path.join(BASE_DIR, "../static")
STATICFILES_DIRS = (
	os.path.join(BASE_DIR, "superlists", "static"),
)
```

> 建议把前面设定的 LOGGING 也加到设置文件中。

然后可以运行布局和样式的功能测试，确认 CSS 仍能正常使用：

```shell
python3 manage.py test functional_tests.test_layout_and_styling
```

接下来创建一个应用，命名为 accounts，与登录相关的代码都放在这个应用中，其中就有 Persona 的 JavaScript 代码：

```python
python3 manage.py startapp accounts
mkdir -p accounts/static/tests
```

整理完了就可以提交了。然后，再看一下探究时编写的 JavaScript 代码：

```javascript
var loginLink = document.getElementById("login");
if (loginLink) {
  loginLink.onclick = function() { navigator.id.request(); };
}
```

#### 15.4.2 什么是模拟技术，为什么要模拟，模拟什么

要把登录链接的 `onclick` 事件绑定到 `Persona` 代码库提供的 `navigator.id.request` 函数上。

不会在单元测试中真的调用第三方函数，因为不想让单元测试到处弹出 `Persona` 窗口。所以要使用模拟技术：在测试中虚拟或者模拟实现第三方 `API`。

要做的是把真正的 `navigator` 对象替换成一个我们自己创建的虚拟对象，这个虚拟对象能告诉我们发生了什么事。

#### 15.4.3 命名空间 

在 `base.html` 环境中，`navigator` 只是全局作用域中的一个对象。这个对象在 `Mozilla` 开发的 `Persona` 代码库中使用 `<script>` 标签引入 `include.js` 时创建。测试全局变量很麻烦，所以可以把 `navigator` 传入初始化函数（`initialise` 和 `initialize` 都是初始化的意思，不过 `initialise` 是英式英语），创建一个本地变量。`base.html` 最终使用的代码如下所示：

```html
<script src="/static/accounts/accounts.js"></script>
<script>
	$(document).ready(function() {
      Superlists.Accounts.initialize(navigator)
	});
</script>
```

这里指定把 `initialize` 函数放在多层嵌套的命名空间 `Superlists.Accounts` 对象中。`JavaScript` 的名声被全局作用域这种编程模式搞坏了，而上述命名空间和命名习惯有助于缓解这种局面。很多 `JavaScript` 库都可能有名为 `initialize` 的函数，但很少会有 `Superlists.Accounts.initialize`。调用 `initialize` 函数的那行代码很简单，无需任何单元测试。

 #### 15.4.4 在 `initialize` 函数的单元测试中使用一个简单的驭件(mock，或者称为侦件 spy)

`initialize` 函数本身需要测试。样板文件 `HTML` 从清单的测试复制而来，然后修改下面这一部分：

```html
<!-- accounts/static/tests/tests.html -->
<div id="qunit-fixture">
    <a id="id_login">Sign in</a>
</div>

<script src="http://code.jquery.com/jquery.min.js"></script>
<script src="../../../todo_app/static/tests/qunit.js"></script>
<script src="../accounts.js"></script>
<script>
    /* global $, test, equal, sinon, Superlists */

    QUnit.test("initialize binds sign in button to navigator.id.request", function (assert) {
        var requestWasCalled = false;	// 确保 requestWasCalled 的初始值为 false
        var mockRequestFunction = function () {
            requestWasCalled = true;
        };	// mockRequestFunction 是个简单的函数，调用时会把 requestWasCalled 变量的值简单地设为 true
        var mockNavigator = { // mockNavigator 其实就是一个普通的 JavaScript 对象，有个名为 id 的属性，其值也是一个对象，在这个对象中有个名为 request 的属性，其值是 mockRequestFunction 变量
            id: {
                request: mockRequestFunction
            }
        };

        Superlists.Accounts.initialize(mockNavigator); // 触发点击事件之前，像在真正的页面中一样，调用 Superlists.Accounts.initialize 函数。唯一的区别在于，没有传入 Persona 提供的真正全局 navigator 对象，而是虚拟的 mockNavigator 对象
        $("#id_login").trigger("click");	// id_login 元素上发生点击事件时调用
        assert.equal(requestWasCalled, true);	// 断定变量 requestWasCalled 的值为 true。这个断言检查的其实是有没有像在 `navigatro.id.request` 中一样调用 `request` 函数。
    })
</script>
```

 这些代码的最终目的是，如果想让这个测试通过，就只有一种方法，即 `initialize` 函数要把 `id_login` 元素的 click 事件绑定到 `.id.request` 方法上，而且这个方法必须由传入 `initialize` 函数的对象提供。如果使用驭件对象（mock object）时这个测试能通过，我们就相信，在真实的页面中传入真正的对象时，`initialize` 函数也会做出正确的操作。

> 在 DOM 元素上测试事件时，需要有一个真正存在的元素来触发事件，还要注册监听程序。如果你忘记添加这个元素，测试会出错，而且极难调试，因为 `.trigger` 悄无声息，不会报错。

运行测试，看到的第一个错误是：

```javascript
Died on test #1     at http://localhost:63342/superlists_for_pythonweb/accounts/static/tests/tests.html:21:11: Superlists is not defined@ 1 ms
Source: 	
ReferenceError: Superlists is not defined
```

这个错误和 Python 中的 ImportError 是一个意思。下面开始编写 `accounts/static/accounts.js` ：

```javascript
window.Superlists = null;
```

在 JavaScript 中可以写成 `window.Superlists = null;` 。使用 `windows.` 的目的是，确保获取全局作用域中的对象。

接下来，根据错误提示继续修改：

```javascript
window.Superlists = {
  Accounts: {}
};
```

测试结果为：

```javascript
Superlists.Accounts.initialize is not a function
```

在实践中，设定这种命名空间时，其实应该遵守“添加或创建”模式，如果作用域中已经有 `window.Superlists` 对象，我们就扩展这个对象，而不是替换原对象。`window.Superlists = window.Superlists || {}` 是一种方式，jQuery 的 `$.extend` 是另一种方式。

***

接着把它定义为一个函数：

```javascript
window.Superlists = {
  Accounts: {
    initialize: function() {}
  }
};
```

从而得到一个真正的测试失败的消息，而不仅仅是错误。

接下来，把定义 initialize 函数和导入命名空间 Superlists 这两步分开。同时，还要使用 console.log（JavaScript 中用于输出调试信息的方法），看看是哪个对象调用了 initialize 函数：

```javascript
var initialize = function (navigator){
  console.log(navigator);
};

window.Superlists = {
  Accounts: {
    initialize: initialize
  }
};
```

在 Firefox（Chrome）中可以使用快捷键 `Ctrl-Shift-I` 调出 JavaScript 终端（macOS 下是 `alt + command + I`)，在终端中会看到输出了 `[object Object]`。点击输出的内容，会看到在测试中定义的属性：一个 id，内部还有一个名为 `request` 的函数。

现在直接让测试通过：

```javascript
// accounts/static/accounts.js
var initialize = function (navigator) {
  navigator.id.request();
};
```

测试后是通过了，但这不是我们想要的实现方式。我们一直在调用 `navigator.id.request`，而不是只在点击时才调用，需要调整测试。

调整测试之前，先随便改改代码，看是否真正理解了我们在做什么。如果把代码改成下面这样：

```javascript
// accounts/static/accounts.js
var initialize = function (navigator) {
  navigator.id.request();
  navigator.id.doSomethingElse();
};
```

从测试的结果中可以看到，传入的模拟 navigator 对象完全在控制之中。这个对象只拥有被赋予的属性和方法。如果想接着改，可以定义这个方法：

```javascript
// accounts/static/tests/tests.html
var mockNavigator = {
  id: {
    request: mockRequestFunction,
    doSomethingElse: function () {
      console.log("called me!");
    }
  }
};
```

这样测试就通过了。打开调试窗口，会看到对应的输出。

现在撤销最近的两次改动，然后修改单元测试，确保 request 函数只在触发点击事件之后才被调用。还要添加一些错误消息，以便找出失败的是两个 equal 断言中哪个失败了：

```javascript
// accounts/static/tests.html
var mockNavigator = {
  id: {
    request: mockRequestFunction
  }
};
Superlists.Accounts.initialize(mockNavigator);
equal(requestWasCalled, false, "check request not called before click");
$("#id_login").trigger("click");
equal(requestWasCalled, true, "check request called after click");
```

>在 QUnit 中，断言的消息（equal 的第三个参数）其实是“成功”消息，不管测试是否通过都会显示。所以才要使用肯定式语句。

下面让 `navigator.id.request` 函数只在点击 `id_login` 之后才调用：

```javascript
// accounts/static/accounts.js
/* global $ */

var initialize = function (navigator) {
  $("#id_login").on("click", function () {
    navigator.id.request();
  });
};
[...]
```

测试能通过了，接下来在模板中引入这个文件：

```html
<!-- lists/templates/base.html -->
<script src="http://code.jquery.com/jquery.min.js"></script>
<script src="https://login.persona.org/include.js"></script>
<script src="/static/accounts.js"></script>
<script src="/static/list.js"></script>
<script>
  /* global $, Superlists, navigator */
  
  $(document).ready(function () {
    Superlists.Accounts.initialize(navigator);
  })
</script>
</body>
```

还得把 accounts 应用加到 settings.py 中，否则无法伺服静态文件 `accounts/static/accounts.js` 。

然后运行功能测试，可惜毫无进展。可以手动打开网站，然后查看 JavaScript 调试终端查明原因。

#### 15.4.5 高级模拟技术

现在要正确调用  `Mozilla` 的 `navigator.id.watch` 函数。再看一下之前编写的探究代码，可以看出，watch 函数需要从全局作用中获取一些信息，包括当前用户的电子邮件地址，作为 `loggedInUser` 参数传入 watch 函数。以及当前使用的 CSRF 令牌，传入发往登录视图的 `Ajax POST` 请求。

在这段代码中还硬编码了两个 URL，这两个 URL 最好从 Django 中获取，方法如下：

```javascript
var urls = {
  login: "{% url 'login' %}",
  logout: "{% url 'logout' %}",
};
```

这是从全局作用域中传入的第三个变量。已经定义了 initialize 函数，假设可以按照下面的方式调用：

```javascript
Superlists.Accounts.initialize(navigator, user, token, urls);
```

##### 使用 sinon.js 创建驭件，确认调用 API 的方式是否正确

正如看到的那样，创建驭件是可能的。实际上，JavaScript 更是将其变得相对容易，不过使用驭件库可以避免很多繁复的操作。JavaScript 领域最受欢迎的驭件库是 sinon.js。下载这个[代码库](http://sinonjs.org/)，把它放到全站共用的静态测试文件夹中。

接下来，在账户测试中引入这个库：

```html
<!-- accounts/static/tests/tests.html -->
<script src="http://code.jquery.com/jquery.min.js"></script>
<script src="../../../superlists/static/tests/qunit.js"></script>
<script src="../../../superlists/static/tests/sinon.js"></script>
<script src="../accounts.js"></script>
```

现在可以使用 Sinon 提供的驭件对象编写测试了(Sinon 还专门提供了侦件对象和桩件对象)：

```javascript
// accounts/static/tests/tests.html
QUnit.test("initialize calls navigator.id.watch", function (assert) {
  var user = 'cuurent user';
  var token = 'csrf token';
  var urls = {login: 'login url', logout: 'logout url'};
  var mockNavigator = {
    id: {
      watch: sinon.mock() // 和之前一样，创建一个模拟的 navigator 对象，不过这一次没有自己动手定义函数实现所需的功能，而是使用一个 sinon.mock() 对象
    }
  };

  Superlists.Accounts.initialize(mockNavigator, user, token, urls);

  assert.equal(
    mockNavigator.id.watch.calledOnce, // 这个对象会在特殊的属性(例如 calledOnce) 中记录发生了什么，在断言中可以比较这个属性的值。
    true,
    'check watch function called'
  );
});
```

Sinon 文档中有更多的说明——其实[首页](http://sinonjs.org/)的功能概览就写得不错。

会得到一个预期的失败测试。

接下来加入对 watch 函数的调用：

```javascript
// accounts/static/accounts.js
var initialize = function (navigator) {
  $('#id_login').on('click', function () {
    navigator.id.request();
  });
  
  navigator.id.watch();
};
```

但这么做导致另一个测试失败了。

在 Firefox 中，每个对象都有 `.watch` 函数。所以在前一个测试中也要创建一个驭件：

```javascript
<!-- accounts/static/tests/tests.html -->
  [...]
   var mockNavigator = {
     id: {
       request: mockRequestFunction,
  	   watch: function() {}
     }
   };
   [...]
```

现在测试都能通过了。

#### 15.4.6 检查参数的调用

调用 watch 函数的方法还不正确——watch 函数要知道当前用户，还要为登录和退出定义几个回调函数。先解决当前用户：

```javascript
// accounts/static/tests/tests.html

QUnit.test("watch sees current user", function (assert) {
  var user = 'current user';
  var token = 'csrf token';
  var urls = {login: 'login url', logout: 'logout url'};
  var mockNavigator = {
    id: {
      watch: sinon.mock()
    }
  };

  Superlists.Accounts.initialize(mockNavigator, user, token, urls);
  var watchCallArgs = mockNavigator.id.watch.firstCall.args[0];
  assert.equal(watchCallArgs.loggedInUser, user, 'check user');
});
```

编写代码的方式与前面类似（下一节我们要删除重复的测试代码）。在驭件上调用 `.firstCall.args[0]`，获取传入 watch 函数的参数（args 是由位置参数组成的列表）。

测试结果表明我们还没有向 watch 函数传入任何参数。一步步来解决：

```javascript
// accounts/static/accounts.js
navigator.id.watch({});
```

错误消息说是没有 `current user`。解决这个问题：

```javascript
var initialize = function (navigator, user, token, urls) {
  [...]
   
   navigator.id.watch({
     loggedInUser: user
   });
```

这样就能使测试全部通过了。

#### 15.4.7 QUnit 中的 setup 和 teardown 函数，以及 Ajax 请求测试

接下来检查 onlogin 回调函数。当 Persona 有用户认证信息要发给服务器验证时，该回调函数会被调用。这个过程涉及 Ajax 调用（`$.post`），一般来说很难测试，不过 `sinon.js` 提供了一个辅助的虚拟 `XMLHttpRequest` 服务器。

这个对象暂时屏蔽了 JavaScript 中原生的 `XMLHttpRequest` 类，所以测试完毕后确认其是否还原是个好习惯。借此机会，学习 `QUnit` 中的 `setup` 和 `teardown` 方法，这两个方法都用于 `module` 函数中。`module` 函数有点儿类似于 `unittest.TestCase` 类，其作用是把随后的所有测试归类到一起。

> #### 关于 Ajax
>
> Ajax 是 "Asynchronous JavaScript XML"（异步 JavaScript 和 XML）的简称，不过 "XML" 有点表述不当，因为现在基本上都是用纯文本或 JSON。使用 Ajax 技术可以在客户端 JavaScript 代码中通过 HTTP 协议（GET 和 POST）请求收发数据，而且 "异步" 完成，既没有阻塞，也不用重新加载页面。
>
> 这里要使用 Ajax 技术向登录视图发起 POST 请求，发送 Persona 获取的判定数据。我们会使用 jQuery 提供的 Ajax [辅助函数](http://api.jquery.com/jQuery.post/)。

在第一个测试之后、测试 "initialize calls navigator.id.watch" 之前加入 module 函数：

```javascript
// accounts/static/tests/tests.html
var user, token, urls, mockNavigator, requests, xhr; // 把 user、token、urls 等变量放在外层作用域中，这样它们才能用于该文件中的所有测试。
module("navigator.id.watch tests", {
  setup: function () {
    user = 'current user'; // setup 函数中的变量就像 unittest 中的 setUP 函数一样，会在每个测试之前初始化。这些变量中包括 mockNavigator
    token = 'csrf token';
    urls = { login: 'login url', logout: 'logout url'};
    mockNavigator = {
      id: {
        watch: sinon.mock()
      }
    };
    xhr = sinon.useFakeXMLHttpRequest(); // 在 setup 函数中，还调用了 Sinon 提供的 useFakeXMLHttpRequest 函数，暂时屏蔽浏览器对 Ajax 的支持
    requests = [];
    // 告诉 Sinon，把所有 Ajax 请求都保存到 requests 数组中，以便在测试中使用
    xhr.onCreate = function (request) { requests.push(request);};
  },
  teardown: function() {
    mockNavigator.id.watch.reset(); // 最后，要做些清理工作——在两次测试之间还原 watch 驭件(否则，在某次测试中的调用结果会显示在另一个测试中)。
    xhr.restore(); // 然后把 JavaScript 中的 XMLHttpRequest 还原到初始状态
  }
});

test("initialize calls navigator.id.watch", function(){
  [...]
```

这样就可以使用更少的代码重写前面两个测试了：

```javascript
// accounts/static/tests/tests.html
test("initialize calls navigator.id.watch", function () {
  Superlists.Accounts.initialize(mockNavigator, user, token, urls);
  equal(mockNavigator.id.watch.calledOnce, true, 'check watch function called');
});

test("watch sees current user", function () {
  Superlists.Accounts.initialize(mockNavigator, user, token, urls);
  var watchCallArgs = mockNavigator.id.watch.firstCall.args[0];
  equal(watchCallArgs.loggedInUser, user, 'check user');
});
```

测试仍能通过，另外测试名称前面加上了模块名。

#### 个人实践

由于跟书中的 QUnit 版本不同，所以以下是自己成功的代码：

```javascript
var user, token, urls, mockNavigator, requests, xhr; // 把 user、token、urls 等变量放在外层作用域中，这样它们才能用于该文件中的所有测试。
QUnit.module("navigator.id.watch tests", {
  // 这里书中用的是 setup, 不过自己测试了无效
  beforeEach: function () {
    user = 'current user'; // setup 函数中的变量就像 unittest 中的 setUP 函数一样，会在每个测试之前初始化。这些变量中包括 mockNavigator
    token = 'csrf token';
    urls = {login: 'login url', logout: 'logout url'};
    mockNavigator = {
      id: {
        watch: sinon.mock()
      }
    };
    xhr = sinon.useFakeXMLHttpRequest(); // 在 setup 函数中，还调用了 Sinon 提供的 useFakeXMLHttpRequest 函数，暂时屏蔽浏览器对 Ajax 的支持
    requests = [];
    // 告诉 Sinon，把所有 Ajax 请求都保存到 requests 数组中，以便在测试中使用
    xhr.onCreate = function (request) {
      requests.push(request);
    };
  },
  // 这里书中是用的 teardown, 不过自己测试了无效
  afterEach: function () {
    mockNavigator.id.watch.reset(); // 最后，要做些清理工作——在两次测试之间还原 watch 驭件(否则，在某次测试中的调用结果会显示在另一个测试中)。
    xhr.restore(); // 然后把 JavaScript 中的 XMLHttpRequest 还原到初始状态
  }
});

QUnit.test("initialize calls navigator.id.watch", function (assert) {
  Superlists.Accounts.initialize(mockNavigator, user, token, urls);
  assert.equal(mockNavigator.id.watch.calledOnce, true, 'check watch function called');
});

QUnit.test("watch sees current user", function (assert) {
  Superlists.Accounts.initialize(mockNavigator, user, token, urls);
  var watchCallArgs = mockNavigator.id.watch.firstCall.args[0];
  assert.equal(watchCallArgs.loggedInUser, user, 'check user');
});
```

onlogin 回调函数的测试方法如下：

```javascript
// accounts/static/tests/tests.html
QUnit.test("onlogin does ajax post to login url", function (assert) {
  Superlists.Accounts.initialize(mockNavigator, user, token, urls);
  var onloginCallback = mockNavigator.id.watch.firstCall.args[0].onlogin; // 从 navigator 模拟对象的 watch 驭件中可以提取出我们定义的 onlogin 回调函数
  onloginCallback(); // 为了测试这个回调函数，可以直接调用它
  assert.equal(requests.length, 1, 'check ajax request'); // Sinon 中的 fakeXMLHttpRequest 服务器会捕获我们发出的任意 Ajax 请求，并把它们存入 requests 数组。然后可以检查很多信息，例如是否为 POST 请求，或者请求的是哪个 URL
  assert.equal(requests[0].method, 'POST');
  assert.equal(requests[0].url, urls.login, 'check url');
});

QUnit.test("onlogin sends assertion with csrf token", function (assert) {
  Superlists.Accounts.initialize(mockNavigator, user, token, urls);
  var onloginCallback = mockNavigator.id.watch.firstCall.args[0].onlogin;
  var assertion = 'browser-id assertion';
  onloginCallback(assertion);
  assert.equal(
    requests[0].requestBody,
    $.param({assertion: assertion, csrfmiddlewaretoken: token}), 'check POST data'
    // POST 请求真正发送的参数保存在 .requestBody 中，而且被 URL 编码了(使用 &key=val 的语法形式)。jQuery 提供的 $.param 函数可以进行 URL 编码，所以对比时调用了这个函数。
  );
});
```

这两个测试跟预期的一样，失败了，接下来又要经历一次 "单元测试/编写代码" 循环。

最终写出的代码如下：

```javascript
navigator.id.watch({
  loggedInUser: user,
  onlogin: function (assertion) {
    $.post(urls['login'], {assertion: assertion, csrfmiddlewaretoken: token}
          );
  }
});
```

#### 退出

在作者写作书的时候，Persona 监视 API 状态的 “onlogout" 部分还未定型。它虽然可以使用，但不能满足作者的需求。所以作者只是把它编写成一个空函数，并将其当做一个占位符。最简单的测试如下：

```javascript
// accounts/static/tests/tests.html
QUnit.test("onlogout is just a placeholder", function (assert) {
  Superlists.Accounts.initialize(mockNavigator, user, token, urls);
  var onlogoutCallback = mockNavigator.id.watch.firstCall.args[0].onlogout;
  assert.equal(typeof onlogoutCallback, "function", "onlogout should be a function");
});
```

得到的退出函数十分简单：

```javascript
[...]
	onlogout: function() {}
 });
```

#### 15.4.8 深层嵌套回调函数和测试异步代码

回调嵌套是 JavaScript 的精髓。幸好 `sinon.js`  对此提供了帮助。还需要测试登录时调用的 post 方法，也设置了一些回调函数，在 POST 请求的结果返回之后做些处理工作：

```javascript
.done(function() { window.location.reload(); })
.fail(function() { navigator.id.logout(); });
```

这里不测试 `window.location.reload` ，因为这有点儿过于复杂了（我们无法模拟 `window.location.reload` ，所以要定义一个未经测试的 `Superlists.Accounts.refreshPage` 函数，然后在测试中创建一个驭件模拟 `refreshPage` 函数，检查它是否被设为 Ajax 调用的 `.done` 回调），而且这可以在 Selenium 测试中测试。不过，这里要测试 fail 回调函数，以此演示嵌套回调也能测试：

```javascript
// accounts/static/tests/test.html
QUnit.test("onlogin post failure should do navigator.id.logout", function (assert) {
  mockNavigator.id.logout = sinon.mock(); // 为需要测试的 mockNavigator.id.logout 函数创建一个驭件
  Superlists.Accounts.initialize(mockNavigator, user, token, urls);
  var onloginCallback = mockNavigator.id.watch.firstCall.args[0].onlogin;
  var server = sinon.fakeServer.create(); // 使用 Sinon 提供的 fakeServer。这是建立在 fakeXMLHttpRequest 之上的一个抽象对象，用来模拟 Ajax 服务器的响应
  server.respondWith([403, {}, "permission denied"]); // 让虚拟服务器返回 403 "permission denied" 响应，以此模拟用户未授权时的状态

  onloginCallback();
  assert.equal(mockNavigator.id.logout.called, false, "should not logout yet");

  server.respond(); // 然后，让虚拟服务器发送响应。因为只有响应发出后才会调用 logout 函数
  assert.equal(mockNavigator.id.logout.called, true, "should call logout");
});
```

根据这个测试，要稍微修改一下探究代码：

```javascript
// accounts/static/accounts.js
navigator.id.watch({
  loggedInUser: user,
  onlogin: function (assertion) {
    $.post(urls['login'], {assertion: assertion, csrfmiddlewaretoken: token}
          ).fail(function () {
      navigator.id.logout();
    });
  },
  onlogout: function (assertion) {
    $.post(urls["logout"]);
  }
});
```

最后，再添加 `window.location.reload` 。这么做只是为了确认它不会导致任何一个单元测试失败：

```javascript
// accounts/static/accounts.js
navigator.id.watch({
  loggedInUser: user,
  onlogin: function (assertion) {
    $.post(urls['login'], {assertion: assertion, csrfmiddlewaretoken: token}
          ).fail(function () {
      navigator.id.logout();
    }).done(function () {
      window.location.reload();
    });
  },
  onlogout: function (assertion) {
    $.post(urls["logout"]);
  }
});
```

一切仍然正常。如果觉得把 `.done` 和 `.fail` 放在一起不太合适，可以使用其他写法，比如：

```javascript
var deferred = $.post(
  urls.login,
  {assertion: assertion, csrfmiddlewaretoken: token}
);

deferred.done(function () {
  window.location.reload();
});
deferred.fail(function () {
  navigator.id.logout();
});
```

这段异步代码，串在一起读可能好理解一些：向 urls.login 发起 POST 请求，并把判定数据和 CSRF 令牌传给这个视图，请求处理完成之后，重新加载页面，如果请求失败，执行 `navigator.id.logout` 函数。可以阅读这篇[文章](http://otaqui.com/blog/1637/introducing-javascript-promises-aka-futures-in-google-chrome-canary/)研究一下 JavaScript 中的 deferred 对象（也叫 "promise"）。

接下来先调整一下对 `initialize` 函数的调用：

```javascript
// lists/templates/base.html
/* global $, Superlists, navigator */
$(document).ready(function () {
  var user = "{{ user.email }}" || null;
  var token = "{{ csrf_token }}";
  var urls = {
    login: "TODO",
    logout: "TODO"
  };
  Superlists.Accounts.initialize(navigator, user, token, urls);
});
```

然后运行功能测试，可以看到测试失败了，但看到弹出了 Persona 对话框，而且后面的操作也都完成了。

> #### 关于在 JavaScript 中探究和使用模拟技术
>
> * 探究
>   * 探索性编程，找到新 API 的用法，或者试验新解决方案的可行性。探究时可以不写测试。最好在新分支中探究，删除探究代码后再回到主分支。
> * 模拟技术
>   * 编写单元测试时，如果涉及第三方服务，但又不想在测试中真的使用这项服务，就可以使用模拟技术。驭件用来模拟第三方 API。虽然可以在 JavaScript 中自己创建驭件，但模拟框架（例如 Sinon）可以提供很多遍历，让编写测试变得更简单，更重要的是，测试读起来更顺口。
> * Ajax 请求的单元测试
>   * Sinon 能给予很大帮助。自动动手模拟 Ajax 请求真的很痛苦。