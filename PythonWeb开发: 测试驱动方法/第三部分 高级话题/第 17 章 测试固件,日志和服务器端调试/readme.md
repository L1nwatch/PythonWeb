## 第 17 章 测试固件、日志和服务器端调试

理论上一个测试只应该测试一件事，所以没必要在每隔功能测试中都测试登录和退出功能。所以需要找到一种方法“作弊”，跳过认证，这样就不用花时间等待执行完重复的测试路径了。

> 在功能测试中去除重复时不要做得太过火了。功能测试的优势之一是，可以捕获应用不同部分之间交互时产生的神秘莫测的表现。

### 17.1 实现创建好会话，跳过登陆过程

用户再次访问网站时 cookie 仍然存在，这种现象很常见。所以“作弊”手段具体做法如下：

```python
# functional_tests/test_my_lists.py
from django.conf import settings
from django.contrib.auth import BACKEND_SESSION_KEY, SESSION_KEY, get_user_model
from django.contrib.sessions.backends.db import SessionStore
from .base import FunctionalTest

User = get_user_model()

class MyListsTest(FunctionalTest):
    def create_pre_authenticated_session(self, email):
        user = User.objects.create(email=email)
        session = SessionStore()
        session[SESSION_KEY] = user.pk # 在数据库中创建一个会话对象。会话键的值是用户对象的主键，即用户的电子邮件地址
        session[BACKEND_SESSION_KEY] = settings.AUTHENTICATION_BACKENDS[0]
        session.save()
        
        ## 为了设定 cookie，我们要先访问网站
        ## 而 404 页面是加载最快的
        self.browser.get(self.server_url + "/404_no_such_url/")
        self.browser.add_cookie(dict(
        	name=settings.SESSION_COOKIE_NAME,
            value=session.session_key, # 然后把一个 cookie 添加到浏览器中，cookie 的值和服务器中的会话匹配。这样再次访问网站时，服务器就能识别已登录的用户。
            path="/",
        ))
```

注意，这种做法仅当使用 LiveServerTestCase 时才有效，所以已创建的 User 和 Session 对象只存在于测试服务器的数据库中。等下会修改实现的方式，让这个测试也能在过渡服务器里的数据库中运行。

> #### JSON 格式的测试固件有危害
>
> 使用测试数据预先填充数据库的过程，例如存储 User 对象及其相关的 Session 对象，叫做设定"测试固件"（test fixture）。
>
> Django 原生支持把数据库中的数据保存为 JSON 格式（使用 manage.py dumpdata 命令）。如果在 TestCase 中使用类属性 fixtures，运行测试时 Django 会自动加载 JSON 格式的数据。
>
> 越来越多的人[建议不要使用 JSON 格式的固件](http://blog.muhuk.com/2012/04/09/carl- meyers-testing-talk-at-pycon-2012.html#.U5XCBpRdXcQ)。如果修改了模型，这种固件维护起来像噩梦。因此，只要可以，就直接使用 Django ORM 加载数据，或者使用 [`factory_boy`](https://factoryboy.readthedocs.org/) 之类的工具。

#### 检查是否可行

要检查这种做法是否可行，最好使用前面测试中定义的 `wait_to_be_logged_in` 函数。要想在不同的测试中访问这个方法，就要把它连同另外几个方法一起移到 `FunctionalTest` 类中。

```python
# functional_tests/base.py
from selenium.webdriver.support.ui import WebDriverWait
[...]

class FunctionalTest(StaticLiveServerCase):
    [...]
    
    def wait_for_element_with_id(self, element_id):
        [...]
        
	def wait_to_be_logged_in(self, email):
        self.wait_for_element_with_id("id_logout")
        navbar = self.browser.find_element_by_css_selector(".navbar")
        self.assertIn(email, navbar.text)
        
	def wait_to_be_logged_out(self, email):
        self.wait_for_element_with_id("id_login")
        navbar = self.browser.find_element_by_css_selector(".navbar")
        self.assertNotIn(email, navbar.text)
```

相应调整一下 `test_login.py` ：

```python
# functional_tests/test_login.py
TEST_EMAIL = "edith@mockmyid.com"
[...]

class LoginTest(FunctionalTest):
    def test_login_with_persona(self):
        # Y 访问这个很棒的超级列表网站
        # 第一次注意到 "Sign in" 链接
        self.browser.get(self.server_url)
        self.browser.find_element_by_id('id_login').click()

        # 出现一个 Persona 登录框
        # 需要辅助函数，它们都用于实现 Selenium 测试中十分常见的操作：等待某件事发生。
        self.switch_to_new_window("Mozilla Persona")

        # Y 使用她的电子邮件地址登录
        ## 测试中的电子邮件使用 mockmyid.com
        # 可以使用如下方法查找 Persona 电子邮件输入框的 ID：手动打开网站，使用 Firefox 调试工具条(`Ctrl + Shift + I`)
        # 这里没有使用真实的电子邮件地址，而是用虚拟工具生成的地址，因此不用在邮件服务供应商的网站上填写认证信息。虚拟工具可以使用 MockMyID 或者 Persona Test User
        self.browser.find_element_by_id("authentication_email").send_keys(TEST_EMAIL)
        self.browser.find_element_by_tag_name("button").click()

        # Persona 窗口关闭
        self.switch_to_new_window("To-Do")

        # 她发现自己已经登录
        # 需要辅助函数，它们都用于实现 Selenium 测试中十分常见的操作：等待某件事发生。
        self.wait_to_be_logged_in(TEST_EMAIL)

        # 刷新页面，她发现真的通过会话登录了
        # 而且并不只在那个页面中有效
        self.browser.refresh()
        self.wait_to_be_logged_in(TEST_EMAIL)

        # 对这项新功能有些恐惧，她立马点击了退出按钮
        self.browser.find_element_by_id("id_logout").click()
        self.wait_to_be_logged_out(TEST_EMAIL)

        # 刷新后仍旧保持退出状态
        self.browser.refresh()
        self.wait_to_be_logged_out(TEST_EMAIL)
```

为了确认我们没有破坏现有功能，再次运行登录测试：

```python
python3 manage.py test functional_tests.test_login
```

现在可以为 “My Lists” 页面编写一个占位测试，检查实现创建认证会话的做法是否可行：

```python
# functional_tests/test_my_lists.py
def test_logged_in_users_lists_are_saved_as_my_lists(self):
    email = "edith@example.com"
    
    self.browser.get(self.server_url)
    self.wait_to_be_logged_out(email)
    
    # Y 是已登录用户
    self.create_pre_authenticated_session(email)
    
    self.browser.get(self.server_url)
    self.wait_to_be_logged_in(email)
```

测试结果为 OK，现在可以提交了：

```shell
git add functional_tests
git commit -m "placeholder test_my_lists and move login checkers into base"
```

### 17.2 实践时检验真理的唯一标准：在过渡服务器中捕获最后的问题

这个功能测试在本地运行一切正常，但在过渡服务器中遇到了意料之外的问题，为了解决这个问题，要找到在测试服务器中管理数据库的方法：

```shell
cd deploy_tools
fab deploy --host=watch0.top
```

然后重启 Gunicron

```shell
sudo restart gunicorn-watch0.top
```

接着运行功能测试：

```python
python3 manage.py test functional_tests --liveserver=watch0.top
```

无法登陆，不管真的是用 Persona 还是已经使用通过认证的会话都不行。这说明测试有问题。我们需要练习如何使用服务器端调试技术。

#### 17.2.1 设置日志

为了记录这个问题，配置 Gunicorn，让它记录日志。在服务器中使用 `vi` 或 `nano` 按照下面的方式调整 Gunicorn 的配置：

```shell
# server: /etc/init/gunicorn-watch0.top.conf
[...]
exec ../../virtualenv/bin/gunicorn \
    --bind unix:/tmp/SITENAME.socket \
    --access-logfile ../../access.log \
    --error-logfile ../../error.log \
    todo_app.wsgi:application
```

这样配置之后，Gunicorn 会在 `~/sites/$SITENAME` 文件夹中保存访问日志和错误日志。然后在 authenticate 函数中调用日志相关的函数输出一些调试信息。

```python
# accounts/authentication.py
import logging
def authenticate(self, assertion):
    logging.warning("entering authenticate function")
    response = request.post(
    	PERSONA_VERIFY_URL,
        data = {"assertion": assertion, "audience": settings.DOMAIN}
    )
    logging.warning("got response from persona")
    logging.warning(response.content.decode())
    [...]
```

> 像这样直接调用日志记录器（`logging.warning` ）不太好

还要确保 `settings.py` 中仍有 `LOGGING` 设置，这样调试信息才能输送到终端。

```python
# superlists/settings.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
        },
    },
    'root': {'level': 'INFO'},
}
```

再次重启 Gunicron，然后运行功能测试。在这些操作执行的过程中，可以使用下面的命令监视日志：

```shell
tail -f error.log # assumes we are in ~/sites/$SITENAME folder
[...]
```

注意 Persona 系统的一个重要部分，即认证只在特定的域名中有效。在 `accounts/authentication.py` 中把域名硬编码即可。

***

#### 个人世间

按照上面那样打印不出来日志，原因未知，自己重新这样设定就可以了：

```python
# settings.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
        },
        'logfile': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, "../../logfile")
        },
    },
    'root': {
        'level': 'INFO',
        'handlers': ['console', 'logfile']
    },
}
```

#### 17.2.2 修正 Persona 引起的这个问题

修正方法如下所示，在本地电脑中修改代码，首先把 DOMOAIN 变量移到 `settings.py`中，稍后可以在部署脚本中重定义这个变量：

```python
# settings.py
# 部署脚本会修改这个变量
DOMAIN = "localhost"

ALLOWED_HOSTS = [DOMAIN]
```

然后修改测试，应对上述改动：

```python
# accounts/tests/test_authentication.py
from unittest.mock import patch
from django.test import TestCase
from django.conf import settings
from accounts.authentication import (
    PERSONA_VERIFY_URL, PersonaAuthenticationBackend
)
from django.contrib.auth import get_user_model

User = get_user_model()

__author__ = '__L1n__w@tch'


@patch("accounts.authentication.requests.post")  # patch 修饰器也可以在类上使用，这样，类中的每个测试方法都会应用这个修饰器，而且驭件会传入每个测试方法
class AuthenticateTest(TestCase):
    def setUp(self):
        self.backend = PersonaAuthenticationBackend()  # 现在我们可以在 setUp 函数中准备所有测试都会用到的变量
        user = User(email="other@user.com")
        # 在默认情况下，Django 的用户都有 username 属性，其值必须具有唯一性。
        # 这里使用的值只是一个占位符，方便我们创建多个用户。后面我们要使用电子邮件做主键，到时候就不用用户名了。
        user.username = "other_user"
        user.save()

    def test_sends_assertion_to_mozilla_with_domain(self, mock_post):
        self.backend.authenticate("an assertion")
        mock_post.assert_called_once_with(
            PERSONA_VERIFY_URL,
            data={"assertion": "an assertion", "audience": settings.DOMAIN}
        )

[...]
```

接着，修改实现方式：

```python
# accounts/authentication.py
from django.conf import settings
from django.contrib.auth import get_user_model

__author__ = '__L1n__w@tch'

PERSONA_VERIFY_URL = "https://verifier.login.persona.org/verify"
User = get_user_model()


class PersonaAuthenticationBackend(object):
    def authenticate(self, assertion):
        logging.warning("entering authenticate function")
        response = requests.post(
            PERSONA_VERIFY_URL,
            data={"assertion": assertion, "audience": settings.DOMAIN}
        )
[...]
```

运行测试确认一下：

```python
python3 manage.py test accounts
```

然后再修改 `fabfile.py`，让它调整 `settigns.py` 中的域名，同时删除使用 sed 修改 `ALLOWED_HOSTS` 那两行多余的代码：

```python
# deploy_tools/fabfile.py
def _update_settings(source_folder, site_name):
    settings_path = source_folder + "/superlists/settings.py"
    sed(settings_path, "DEBUG = True", "DEBUG = False")
    sed(settings_path, 'DOMAIN = "localhost"', '"DOMAIN = {}"'.format(site_name))
    secret_key_file = source_folder + "/superlists/secret_key.py"
    if not exists(secret_key_file):
        [...]
```

重新部署，看输出中有没执行 sed 修改 DOMAIN 的值。

```python
fab deploy --host=watch0.top
```

### 17.3 在过渡服务器中管理测试数据库

现在可以再次运行功能测试，此时又会看到一个失败测试，因为无法创建已经通过认证的会话，所以针对 “My Lists` 页面的测试失败了：

```python
python3 manage.py test functional_tests --liveserver=watch0.top
```

失败的真正原因是 `create_pre_authenticated_session` 函数只能操作本地数据库。要找到一种方法，管理服务器中的数据库。

#### 17.3.1 创建会话的 Django 管理命令

若想在服务器中操作，就要编写一个自成一体的脚本，在服务器中的命令行里执行。大多数情况下都会使用 Fabric 执行这样的脚本。

尝试编写可在 Django 环境中运行的独立脚本（和数据库交互等）。有些问题需要谨慎处理，例如正确设定 `DJANGO_SETTINGS_MODULE` 环境变量，还要正确处理 `sys.path`。与其在这些细节上浪费时间，其实 Django 允许我们自己创建”管理命令“（可以使用 `python manage.py` 运行的命令），可以把一切琐碎的事情都交给 Django 完成。管理命令保存在应用的 `management/command` 文件夹中：

```shell
mkdir -p functional_tests/management/commands
touch functional_tests/management/__init__.py
touch functional_tests/management/commands/__init__.py
```

管理命令的样板代码是一个类，继承自 `django.core.management.BaseCommand`，而且定义了一个名为 handle 的方法：

```python
# functional_tests/management/commands/create_session.py
from django.conf import settings
from django.contrib.auth import BACKEND_SESSION_KEY, SESSION_KEY, get_user_model
from django.contrib.sessions.backends.db import SessionStore
from django.core.management.base import BaseCommand

__author__ = '__L1n__w@tch'

User = get_user_model()


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('email')

    def handle(self, *args, **kwargs):
        email = kwargs["email"]
        session_key = create_pre_authenticated_session(email)
        self.stdout.write(session_key)


def create_pre_authenticated_session(email):
    user = User.objects.create(email=email)
    session = SessionStore()
    session[SESSION_KEY] = user.pk
    session[BACKEND_SESSION_KEY] = settings.AUTHENTICATION_BACKENDS[0]
    session.save()
    return session.session_key

```

`create_pre_authenticated_session` 函数的代码从 `test_my_lists.py` 文件中提取而来。handle 方法从命令行的第一个参数中获取电子邮件地址，返回一个将要存入浏览器 cookie 中的会话键。这个管理命令还会把会话期间打印到命令行中，试一下这个命令：

```python
python3 manage.py create_session a@b.com
```

还要做一步设置——把 `functional_tests` 加入 `settings.py`，让 Django 把它识别为一个可能包含管理命令和测试的真正应用。

```python
# superlists/settings.py
INSTALLED_APPS = [
    # 'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    "lists",
    "accounts",
    "functional_tests"
]
```

现在这个管理命令可以使用了：

```python
python3 manage.py create_session a@b.com # 自己测试失败了，提示说找不到表 account_user
# 个人实践
# 参考：http://stackoverflow.com/questions/31933772/django-db-utils-operationalerror-no-such-table-django-site
# 说是一旦修改了 settings.py 中的东西，在 < Django1.9 版本之前会自动执行 sycndb，但是1.9 之后需要手动删除数据库然后 migrate 才能成功
# 于是我就手动删除然后执行 makemigrations 以及 migrate ，然后就成功了
```

#### 17.3.2 让功能测试在服务器上运行管理命令

接下来调整 `test_my_lists.py` 文件中的测试，让它在本地服务器中运行本地函数，但是在过渡服务器中运行管理命令：

```python
# functional_tests/test_my_lists.py
from django.conf import settings
from base import FunctionalTest
from server_tools import create_session_on_server
from management.commands.create_session import create_pre_authenticated_session

class MyListsTest(FunctionalTest):
    def create_pre_authenticated_session(self, email):
        if self.against_staging:
            session_key = create_session_on_server(self.server_host, email)
        else:
            session_key = create_pre_authenticated_session(email)
		# 为了设定 cookie，我们要先访问网站
        # 而 404 页面是加载最快的
        self.browser.get(self.server_url + "/404_no_such_url/")
        self.browser.add_cookie(dict(
        	name=settings.SESSION_COOKIE_NAME,
            value=session_key,
            path="/",
        ))
```

看一下如何判断是否运行在过渡服务器中。`self.against_staging` 的值在 `base.py` 中设定：

```python
# functional_tests/base.py
from server_tools import reset_database

class FunctionalTest(StaticLiveServerCase):
    @classmethod
    def setUpClass(cls):
        for arg in sys.argv:
            if "liveserver" in arg:
                cls.server_host = arg.split("=")[1] # 如果检测到命令行参数中有 liveserver, 就不仅存储 cls.server_url 属性，还存储 server_host 和 against_staging 属性
                cls.server_url = "http://" + cls.server_host
                cls.against_staging = True
                return
		super().setUpClass()
        cls.against_staging = False
        cls.server_url = cls.live_server_url
        
	@classmethod
    def tearDownClass(cls):
        if not cls.against_staging:
            super().tearDownClass()
            
	def setUp(self):
        if self.against_staging:
            reset_database(self.server_host) # 需要在两次测试之间还原服务器中数据库的方法
        self.browser = webdriver.Firefox()
        self.browser.implicitly_wait(3)
```

#### 17.3.3 使用 subprocess 模块完成额外的工作

我们的测试使用 Python 3，不能直接调用 Fabric 函数，因为 Fabric 只能在 Python 2 中使用。所以要做些额外工作，像部署服务器时一样，在新进程中执行 fab 命令。要做的额外工作如下，代码写入 `server_tools` 模块中：

```python
# functional_tests/server_tools.py
from os import path
import subprocess
THIS_FOLDER = path.abspath(path.dirname(__file__))
SSH_PORT = 26832

def create_session_on_server(host, email):
    return subprocess.check_output(
    	[
          "fab",
          "create_session_on_server:email={}".format(email), # 可以看出，在命令行中指定 fab 函数的参数使用的句法很简单，冒号后跟着 "变量=参数" 形式的写法
          "--host={}:{}".format(host, SSH_PORT), # 自己的服务器使用 SSH_PORT 端口号
          "--hide=everything,status", # 因为这些工作通过 Fabric 和子进程完成，而且在服务器中运行，所以从命令行的输出中提取字符串形式的会话键时一定要格外小心
    	],
        cwd = THIS_FOLDER
    ).decode().strip()

def reset_database(host):
    subprocess.check_call(
    	["fab", "reset_database", "--host={}:{}".format(host, SSH_PORT)],
        cwd = THIS_FOLDER
    )
```

这里使用 subprocess 模块通过 fab 命令调用几个 Fabric 函数。

如果使用自定义的用户名或密码，需要修改调用 `subprocess` 那行代码，和运行自动化部署脚本时 fab 命令的参数保持一致。

最后，看一下 `fabfile.py` 中定义的那两个在服务器端运行的命令。这两个命令的作用是还原数据库和设置会话：

```python
# functional_tests/fabfile.py
from fabric.api import env, run

def _get_base_folder(host):
    return "~/sites/" + host

def _get_manage_dot_py(host):
    return "{path}/virtualenv/bin/python {path}/source/manage.py".format(path=_get_base_folder(host))

def reset_database():
    run("{manage_py} flush --noinput".format(
    	manage_py=_get_manage_dot_py(env.host)
    ))

def create_session_on_server(email):
    session_key = run("{manage_py} create_session {email}".format(manage_py=_get_manage_dot_py(env.host),email=email,))
    print(session_key)
```

首先，在本地运行测试，确认没有造成任何破坏：`python3 manage.py test functional_tests.test_my_lists`。

然后，在服务器中运行。先把代码推送到服务器中：

```shell
git push # 要先提交改动
cd deploy_tools
fab deploy --host=watch0.top:26832
```

再运行测试。注意，现在指定 `liveserver` 参数的值时可以包含 `elspeth@`：

```shell
python3 manage.py test functional_tests.test_my_lists --liveserver=watch@watch0.top
```

之后还可以运行全部测试确认一下。

> 作者展示了管理测试数据库的一种方法，也可以试验其他方式。例如，使用 MySQL 或 Postgres，可以打开一个 SSH 隧道连接服务器，使用端口转发直接操作数据库。然后修改 `settings.DATABSES`，让功能测试使用隧道连接的端口和数据库交互。

> #### 警告：小心，不要在线上服务器中运行测试
>
> 我们现在编写的代码能直接影响服务器中的数据库。一定要非常小心，别在错误的主机中运行功能测试，把生产数据库清空了。
>
> 此时，可以考虑使用一些安全防护措施。例如，把过渡环境和生产环境放在不同的服务器中，而且不同的服务器使用不同的口令认证密钥对。
>
> 在生产环境的数据副本中运行测试也有同样的危险。

### 17.4 集成日志相关的代码

接下来要把日志相关的代码集成到应用中。把输出日志的代码放在那儿，并且纳入版本控制，有助于调试以后遇到的登陆问题。

先把 `Gunicorn` 的配置保存到 `deploy_tools` 文件夹里的临时文件中。

#### 使用可继承的日志配置

前面调用 `logging.warning` 时，使用的是根日志记录器。一般来说，这么做并不好，因为第三方模块会干扰根日志记录器。一般的做法是使用以所在文件命名的日志记录器，使用下面的代码：

`logger = logging.getLogger(__name__)`

日志的配置可以继承，所以可以为顶层模块定义一个父日志记录器，让其中的所有 Python 模块都继承这个配置。

在 `settings.py` 中为所有应用设置日志记录器的方式如下所示：

```python
# superlists/settings.py
LOGGING = {
  "version": 1,
  "disable_existing_loggers": False,
  "handlers": {
    "console": {
      "level": "DEBUG",
      "class": "logging.StreamHandler",
    },
  } ,
  "loggers": {
    "django": {
      "handlers": ["console"],
    },
    "accounts": {
      "handlers": ["console"],
    },
    "lists": {
      "handlers": ["console"],
    },
  },
  "root": {"level": "INFO"}
}
```

现在，`accounts.models`、`accounts.views` 和 `accounts.authentication` 等应用都从父日志记录器 accounts 中继承 `logging.StreamHandler`。

不过，受限于 Django 的项目结构，无法为整个项目定义一个顶层日志记录器（除非使用根日志记录器），所以必须为每个应用定义各自的日志记录器。

为日志行为编写测试的方法如下所示：

```python
# accounts/tests/test_authentication.py
import logging
[...]

@patch("accounts.authentication.requests.post")
class AuthenticateTest(TestCase):
    [...]
    
    def test_logs_non_okay_responses_from_persona(self, mock_post):
        response_json = {"status": "not okay", "reason": "eg, audience mismatch"}
        mock_post.return_value_ok = True
        mock_post.return_value.json.return_value = response_json  # 给测试提供一些数据，触发日志记录器

        logger = logging.getLogger("accounts.authentication")  # 获取正在测试的这个模块的日志记录器
        # 使用 patch.object 临时模块这个日志记录器的 warning 函数。使用 with 的目的是把这个驭件作为测试目标函数的上下文管理器
        with patch.object(logger, "warning") as mock_log_warning:
            self.backend.authenticate("an assertion")

        # 然后可以使用这个驭件声明断言
        mock_log_warning.assert_called_once_with("Persona says no. Json was: {}".format(response_json))
```

可以测试一下，确保测试了我们想测试的行为：

```python
# accounts/authenticaion.py
import logging
logger = logging.getLogger(__name__)
[...]
	if response.ok and response.json["status"] == "okay":
        [...]
    else:
        logger.warning("foo")
```

然后使用真正的实现方式：

```python
# accounts/authentication.py
else:
    logger.warning(
    	"Persona says no. Json was: {}".format(response.json())
    )
```

进行测试，可以看到成功了。

### 17.5 小结

至此，已经让测试固件既可以在本地使用也能在服务器中使用，还设定了更牢靠的日志配置。

> #### 固件和日志
>
> * 谨慎去除功能测试中的重复
>   * 每个功能测试没必要都测试应用的全部功能。在功能测试中还可能需要跳过一些过程。但是，要提醒一下，功能测试的目的是为了捕获应用不同部分之间交互时的异常表现，所去除重复时不要太过火了。
> * 测试固件
>   * 测试固件指运行测试之前要提前准备好的测试数据。一般使用一些数据填充数据库，不过如前所示（创建浏览器的 cookie），也会涉及到其他准备工作。
> * 避免使用 JSON 固件
>   * Django 提供的 dumpdata 和 loaddata 等命令，简化了把数据库中的数据导出为 JSON 格式的操作，也可以轻易的使用 JSON 格式数据还原数据库。大多数人都不建议使用这种固件，因为数据库模式发生变化后这种固件很难维护。所以建议使用 ORM，或者 [`factory_boy`](https://factoryboy.readthedocs.org/)这类工具。
> * 固件也要在远程服务器中使用
>   * 在本地运行测试，使用 `LiveServerTestCase` 即可轻松通过 `Django ORM` 与测试数据库交互。与过渡服务器中的数据库交互就没这么简单了。解决办法之一是使用 Django 管理命令。
> * 使用以所在模块命名的日志记录器
>   * 根日志记录器是一个全局对象，Python 进程中加载的所有库都能访问，所以这个日志记录器不完全在你的控制之中。因此，要使用 `logging.getLogger(__name__)` 获取一个相对模块唯一的记录器，而且这个记录器继承自设定的顶层配置。
> * 测试重要的日志消息
>   * 日志消息对于调试生产环境中的问题十分重要。如果某个日志消息很重要，必须保留在代码中，或许也有必要测试。根据经验，比 `logging.INFO` 等级高的日志消息都要测试。在测试目标模块所用的日志记录器上使用 `patch.object`，有助于简化日志消息的单元测试。