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
                $.post('/account/logout')
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
        return ListUser.objets.get(email=email)
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
        ListUser.obejcts.create(email=email)
    
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

