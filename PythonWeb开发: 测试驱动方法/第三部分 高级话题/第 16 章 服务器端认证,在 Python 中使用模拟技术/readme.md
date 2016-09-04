## 第 16 章 服务器端认证, 在 Python 中使用模拟技术

### 16.1 探究登录视图

我们已经写好了可以使用的客户端代码，尝试把认证判定数据发给服务器中的登录视图。下面开始编写这个视图，然后再创建后台认证函数。

探究时编写的登录视图如下所示：

```python
def persona_login(request):
    print("login view", file=sys.stderr)
    # user = PersonaAuthenticationBackend().authenticate(request.POST["assertion"])
    user = authenticate(assertion=request.POST["assertion"]) # authenticate 是我们自定义的认证函数，这个函数的作用是验证客户端发送的判定数据
    if user is not None:
        login(request, user) # login 是 Django 原生的登录函数。它把一个会话对象存储到服务器中，并且和用户的 cookie 关联起来，这样在以后的请求中我们就知道这个用户已经通过认证
    return redirect("/")
```

authenticate 函数要通过互联网访问 Mozilla 的服务器。在单元测试中我们需要模拟 authenticate 函数的功能。

### 16.2 在 Python 代码中使用模拟技术

流行的 mock 已经集成到 Python 3.3 中。（在 Python2 中，可以执行命令 pip3 install mock 安装，然后把后文中出现的 `from unittest.mock` 换成 `from mock` ）这个包提供了一个神奇的对象 Mock，有点像 Sinon 驭件对象，不过功能更强大：

```python
>>> from unittest.mock import Mock
>>> m = Mock()
>>> m.any_attribute
<Mock name='mock.any_attribute' id='4384429224'>
>>> m.foo
<Mock name='mock.foo' id='4396036952'>
>>> m.any_method()
<Mock name='mock.any_method()' id='4396102096'>
>>> m.foo()
<Mock name='mock.foo()' id='4396102208'>
>>> m.called
False
>>> m.foo.called
True
>>> m.bar.return_value = 1
>>> m.bar()
1
```

使用驭件对象模拟 authenticate 函数的功能应该很灵巧。下面介绍如何模拟。

#### 16.2.1 通过模拟 authenticate 函数测试视图

```python
# accounts/tests/test_view.py, 注意创建 tests 文件夹后要加入 __init__.py 同时删除默认的 tests.py 文件
from django.test import TestCase
from unittest.mock import patch

class LoginViewTest(TestCase):
    # patch 修饰符有点像 Sinon 中的 mock 函数，作用是指定要模拟的对象。这里要模拟的是 authenticate 函数
    @patch("accounts.views.authenticate")
    # 修饰符把模拟对象作为额外的参数传入被应用的函数中
    def test_calls_authenticate_with_assertion_from_post(self, mock_authenticate):
        # 然后我们可以配置这个驭件，让它具有特定的行为。让 authenticate 函数返回 None 是最简单的行为
        # 所以我们设定了特殊的 .return_value 属性。否则，这个驭件会返回另一个驭件，视图可能不知道怎么处理
        mock_authenticate.return_Value = None
        self.client.post("/accounts/login", {"assertion": "assert this"})
        # 驭件可以做出断言，我们检查驭件是否被调用，以及调用时传入的参数是什么
        mock_authenticate.assert_called_once_with(assertion="assert this")
```

测试的结果：```python3 manage.py test accounts`

表明我们试图模拟的函数还不存在，需要把 `authenticate` 函数导入 `views.py`（虽然我们要自己定义 authenticate 函数，不过还是要从 `django.contrib.auth` 中导入。只要我们在 `settings.py` 中配置好，Django 就会自动换用我们自己定义的函数。这么做有个好处，如果以后要使用第三方库代替 authenticate 函数，无需修改 `views.py`）：

```python
# accounts/views.py
from django.contrib.auth import authenticate
```

现在测试的结果表明，我们需要把登录视图和一个 URL 联系起来。

```python
# superlists/urls.py
urlpatterns = [
    # url(r'^admin/', admin.site.urls),
    url(r"^$", "lists.views.home_page", name="home"),
    url(r"^lists/", include("lists.urls")),
    url(r"^accounts/", include("accounts.urls")),
]
```

```python
# accounts/urls.py
from django.conf.urls import patterns, url

urlpatterns = patterns("",
                      url(r"^login$", "accounts.views.persona_login", name="persona_login"),)
```

为了通过测试，持续进行编写：

```python
# accounts/views.py
from django.http import HttpResponse
from django.contrib.auth import authenticate


def persona_login(request):
    authenticate(assertion=request.POST["assertion"])
    return HttpResponse()
```

到目前为止一切顺利。我们模拟并测试了一个 Python 函数。

#### 16.2.2 确认视图确实登录了用户

但是，如果 authenticate 函数返回一个用户，authenticate 视图也要通过调用 Django 中的 `auth.login` 函数，让用户真正登录网站。所以 authenticate 函数不能返回空响应——既然这个视图处理的是 Ajax 请求，那么就无需返回 HTML，返回一个简单的“OK”字符串就行：

```python
# accounts/tests/test_views.py
from django.contrib.auth import get_user_model
from django.test import TestCase
from unittest.mock import patch
User = get_user_model() # 这个函数的作用是找出项目使用的用户模型，不管是标准的用户模型还是自定义的模型都能使用

class LoginViewTest(TestCase):
    @patch("accounts.views.authenticate")
    def test_calls_authenticate_with_assertion_from_post(...):
    	[...]
    
    @patch("accounts.views.authenticate")
    def test_returns_ok_when_user_found(self, mock_authenticate):
        user = User.objects.create(email="a@b.com")
        user.backend = ""  # 为了使用 auth.login，必须设定这个属性
        mock_authenticate.return_value = user
        response = self.client.post("/accounts/login", {"assertion": "a"})
        self.assertEqual(response.content.decode(), "OK")
```

这个测试检查的是想得到的响应。下面我们要测试用户确实正确登录了。我们使用的方法是检查 Django 测试客户端，看它是否正确设定了会话 cookie。

```python
# accounts/tests/test_views.py
from django.contrib.auth import get_user_model, SESSION_KEY
[...]

@patch("accounts.views.authenticate")
def test_gets_logged_in_session_if_authenticate_returns_a_user(self, mock_authenticate):
    user = User.objects.create(email="a@b.com")
    user.backend = "" # 为了使用 auth.login, 必须设定这个属性
    mock_authenticate.return_value = user
    self.client.post("/accounts/login", {"assertion": "a"})
    self.assertEqual(self.client.session[SESSION_KEY], user.pk) # Django 测试客户端会记录用户的会话，为了确认用户是否通过验证，我们要检查用户的 ID(主键，简称 pk)是否和会话关联在一起
    
@patch("accounts.views.authenticate")
def test_does_not_get_logged_in_if_authenticate_returns_None(self, mock_authenticate):
    mock_authenticate.return_value = None
    self.client.post("/accounts/login", {"assertion": "a"})
    self.assertNotIn(SESSION_KEY, self.client.session) # 如果用户没有通过认证，会话中就不应该包含 SESSION_KEY
```

> #### Django 会话：用户的 cookie 如何告诉服务器她已经通过认证
>
> 接下来解释什么是会话、cookie，以及在 Django 中怎么认证用户。
>
> HTTP 是无状态的，因此服务器需要一种在每次请求中识别不同的客户端的方法。IP 地址可以共用，所以一般使用的方法是为每个客户端指定一个唯一的会话 ID。会话 ID 存储在 cookie 中，每次请求都会提交给服务器。服务器在某处存储会话 ID（默认情况下存入数据库），这样它就知道各个请求来自哪个特定的客户端。
>
> 使用开发服务器登录网站时，如果需要，其实可以手动查看自己的会话 ID。默认情况下，会话 ID 存储在 sessionid 键下。
>
> 不管用户是否登录，只要访问使用 Django 开发的网站，就会为访问者设定会话 cookie。
>
> 如果网站以后需要识别已经登录且通过认证的客户端，不用要求客户端在每次请求中都发送用户名和密码，服务器可以把客户端的会话标记为已通过验证，并且在数据库中把会话 ID 和用户 ID 关联起来。
>
> 会话的数据结构有点儿像字典，用户 ID 存储在哪个键下由 `django.contrib.auth.SESSION_KEY` 决定。如果需要，可以在 manage.py 的终端控制台查看会话：
>
> ```python
> python3 manage.py shell
> from django.contrib.sessions.models import Session
>
> # 这里会显示浏览器 cookie 中存储的会话 ID
> session = Session.objects.get(session_key="...")
>
> print(session.get_decoded())
> ```
>
> 在用户的会话中还可以存储其他任何需要的信息，作为临时记录某种状态的方式。对未登录的用户也可以这么做。在任意一个视图中使用 `request.session` 即可，用法和字典一样。可以参考 Django 文档中对[会话的说明](http://djangoproject.com/en/1.7/topics/http/sessions/)。

得到的是两个失败的测试。处理用户登录以及标记会话的 Django 函数是 `django.contrib.auth.login` 。所以我们还要历经几次 TDD 循环，最终才能编写出视图函数：

```python
# accounts/views.py
def persona_login(request):
    user = authenticate(assertion=request.POST["assertion"])
    if user is not None:
        login(request, user)
    return HttpResponse("OK")
```

测试结果为：OK。至此，我们得到了一个可以使用的登录视图。

> #### 使用驭件测试登录
>
> 测试是否正确调用 Django 中 login 函数的另一种方法也是模拟 login 函数：
>
> ```python
> # accounts/tests/test_views.py
> from django.http import HttpRequest
> from accounts.views import persona_login
> [...]
>
> @patch("accounts.views.login")
> @patch("accounts.views.authenticate")
> def test_calls_auth_login_if_authenticate_returns_a_user(self, mock_authenticate, mock_login):
>     request = HttpRequest()
>     request.POST["assertion"] = "asserted"
>     mock_user = mock_authenticate.return_value
>     login(request)
>     mock_login.assert_called_once_with(request, mock_user)
> ```
>
> 这种测试方式的优点是，不依赖 Django 测试客户端，也不用知道 Django 会话的工作方式，只需要知道你要调用的函数名即可。
>
> 缺点是几乎都在测试实现方式，但没测试行为，而且和 Django 中实现登录功能的函数名和 API 结合地太过紧密。

### 16.3 模拟网络请求，去除自定义认证后台中的探究代码

接下来我们要自定义认证后台。探究时编写的代码如下所示：

```python
class PersonAuthenticationBackend(object):
    def authenticate(self, assertion):
        # 把判定数据发送给 Mozilla 的验证服务
        data = {"assertion": assertion, "audience": "localhost"}
        print("sending to mozilla", data, file=sys.stderr)
        resp = requests.post("https://verifier.login.persona.org/verify", data=data)
        print("got", resp.content, file=sys.stderr)
        
        # 验证服务器有响应吗？
        if resp.ok:
            # 解析响应
            verification_data = resp.json()
            
            # 检查判定数据是否有效
            if verification_data["status"] == "okay":
                email = verification_data["email"]
                try:
                    return self.get_user(email)
              	except ListUser.DoesNotExist:
                    return ListUser.objects.create(email=emial)
                
	def get_user(self, email):
        return ListUser.objects.get(email=email)
```

这段代码的意思是：

* 使用 requests.post 把判定数据发送给 Mozilla
* 然后检查响应码（resp.ok），再检查响应的 JSON 数据中 status 字段的值是否为 okay
* 最后，从响应中提取电子邮件地址，通过这个地址找到现有的用户，如果找不到就创建一个新用户

#### 16.3.1 一个 if 语句需要一个测试

如何为这种函数编写测试有个经验法则：一个 if 语句需要一个测试，一个 try/except 语句需要一个测试。所以一共需要四个测试。先编写第一个：

```python
# accounts/tests/test_authentication.py
from unittest.mock import patch
from django.test import TestCase
from accounts.authentication import (
	PERSONA_VERIFY_URL, DOMAIN, PersonaAuthenticationBackend
)

class AuthenticateTest(TestCase):
    @patch("accounts.authentication.requests.post")
    def test_sends_assertion_to_mozilla_with_domain(self, mock_post):
        backend = PersonaAuthenticationBackend()
        backend.authenticate("an assertion")
        mock_post.assert_called_once_with(
        	PERSONA_VERIFY_URL,
            data={"assertion": "an assertion", "audience": DOMAIN}
        )
```

在 `authentication.py` 中，我们先编写好一些占位代码：

```python
# accounts/authentication.py
import requests

PERSONA_VERIFY_URL = "https://verifier.login.persona.org/verify"
DOMAIN = "localhost"

class PersonaAuthenticationBackend(object):
    def authenticate(self, assertion):
        pass
```

此时，我们需要把 requests 库添加到 requirements.txt 中，否则下一次部署会失败。

然后执行一下测试，观察测试结果，最终写出的代码如下：

```python
def authenticate(self, assertion):
    requests.post(PERSONA_VERIFY_URL, data={"audience": DOMAIN, "assertion": assertion})
```

测试全部通过了。

接下来，检查 authenticate 函数在发现请求的响应中有错误时是否返回 None：

```python
# accounts/tests/test_authentication.py
@patch("accounts.authentication.requests.post")
def test_returns_none_if_response_errors(self, mock_post):
    mock_post.return_value.ok = False
    backend = PersonaAuthenticationBackend()
    
    user = backend.authenticate("an assertion")
    self.assertIsNone(user)
```

这个测试直接就能通过，因为不管什么情况，现在返回的都是 None。

#### 16.3.2 在类上使用 patch 修饰器

接下来要检查响应的 JSON 数据中 status 字段是否为 okay。编写这个测试会涉及到一些重复代码：

```python
# accounts/tests/test_authentication.py
@patch("accounts.authentication.requests.post") # patch 修饰器也可以在类上使用，这样，类中的每个测试方法都会应用这个修饰器，而且驭件会传入每个测试方法
class AuthenticateTest(TestCase):
    def setUp(self):
        self.backend = PersonaAuthenticationBackend() # 现在我们可以在 setUp 函数中准备所有测试都会用到的变量
        
    def test_sends_assertion_to_mozilla_with_domain(self, mock_post):
        self.backend.authenticate("an assertion")
        mock_post.assert_called_once_with(
            PERSONA_VERIFY_URL,
            data = {"assertion": "an assertion", "audience": DOMAIN}
        )

	def test_returns_none_if_response_errors(self, mock_post):
        mock_post.return_value.ok = False # 现在每个测试只调整需要设定的变量，而没有设定一堆重复的样板代码，所以测试更具易读性
        user = self.backend.authenticate("an assertion")
        self.assertIsNone(user)
        
	def test_returns_none_if_status_not_okay(self, mock_post):
        mock_post.return_value.json.return_value = {"status": "not okay!"} # 现在每个测试只调整需要设定的变量，而没有设定一堆重复的样板代码，所以测试更具易读性
        user = self.backend.authenticate("an assertion")
        self.assertIsNone(user)
```

一切都很顺利，测试仍能通过。

现在我们该测试能通过认证的情况了，看 authenticate 函数是否返回一个用户对象。我们期望下面这个测试失败：

```python
# accounts/tests/test_authentication.py
from django.contrib.auth import get_user_model
User = get_user_model()
[...]
	def test_finds_existing_user_with_email(self, mock_post):
        mock_post.return_value.json.return_value = {"status": "okay", "email": "a@b.com"}
        actual_user = User.objects.create(email="a@b.com")
        found_user = self.backend.authenticate("an assertion")
        self.assertEqual(found_user, actual_user)
```

下面开始编写代码，先用一个”作弊“的实现方式，直接获取在数据库中找到的第一个用户：

```python
# accounts/authenticate.py
import requests
from django.contrib.auth import get_user_model
User = get_user_model()
[...]

def authenticate(self, assertion):
    requests.post(
    	PERSONA_VERIFY_URL,
        data = {"assertion": assertion, "audience": DOMAIN}
    )
    return User.objects.first()
```

这段代码让所有测试都通过了，这是因为如果数据库中没有用户，`objects.first()` 会返回 None。我们要保证运行每个测试时数据库中都至少有一个用户，让其他情况更可行一些：

```python
# accounts/tests/test_authentication.py
def setUp(self):
    self.backend = PersonaAuthenticationBackend()
    user = User(email="other@user.com")
    user.username = "otheruser" # 在默认情况下，Django 的用户都有 username 属性，其值必须具有唯一性。这里使用的值只是一个占位符，方便我们创建多个用户。后面我们要使用电子邮件做主键，到时候就不用用户名了。
    user.save()
```

下面，我们开始编写在响应出错或状态不是 okay 的情况下防范认证失败的代码：

```python
# accounts/authentication.py
def authenticate(self, assertion):
    response = requests.post(
    	PERSONA_VERIFY_URL,
        data = {"assetion": assertion, "audience": DOMAIN}
    )
    if response.json()["status"] == "okay":
        return User.objects.first()
```

这么写居然能修正两个测试，下节再分析，现在先取回正确的用户，让最后一个测试也通过：

```python
# accounts/authenticate.py
if response.json()["status"] == "okay":
    return User.objects.get(email=response.json()["email"])
```

#### 16.3.3 进行布尔值比较时要留意驭件

那么为什么 `test_returns_none_if_response_errors` 没有失败？因为我们模拟了 `requests.post`，response 是驭件对象。或许你还记得，它返回的所有属性和也都是驭件。（其实，只有 patch 修饰符时才会发生这种情况，response 其实是 MagicMock 对象，比 mock 模拟的层级还深，有点儿像字典。[详情](https://docs.python.org/3/library/unittest.mock.html#magicmock-)）所以，在下面这行代码中：

```python
# accounts/authentication.py
if response.json()["status"] == "okay":
```

response 其实是一个驭件，`response.json()` 也是驭件，`response.json()["status"]` 还是驭件。最终，我们是拿一个驭件和字符串 "okay" 进行比较，结果自然是 False，因此 authenticate 函数的返回值是 None。我们要把测试的表述改得更明确一些，把响应的 JSON 数据声明为一个空字典：

```python
# accounts/tests/test_authentication.py
def test_returns_none_if_response_errors(self, mock_post):
    mock_post.return_value.ok = False
    mock_post.return_value.json.return_value = {}
    user = self.backend.authenticate("an assertion")
    self.assertIsNone(user)
```

此时，测试的结果为：

```python
if response.json()["status"] == "okay":
KeyError: "status"
```

这个问题可以使用下面的方式修正：

```python
# accounts/authentication.py
if response.ok and response.json()["status"] == "okay":
    return User.objects.get(email=response.json()["email"])
```

现在的测试结果为 OK。



