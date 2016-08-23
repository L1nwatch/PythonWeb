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

现在，如果用户点击登录链接，Persona