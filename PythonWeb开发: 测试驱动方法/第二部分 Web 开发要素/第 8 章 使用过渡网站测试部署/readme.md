## 第 8 章 使用过渡网站测试部署

术语开发运维（DevOps）。

### 8.1 TDD 以及部署的危险区域

部署过程中的一些危险区域如下：

* 静态文件（CSS、JavaScript、图片等）
  * Web 服务器往往需要特殊的配置才能伺服静态文件
* 数据库
  * 可能会遇到权限和路径问题，还要小心处理，在多次部署之间不能丢失数据。
* 依赖
  * 要保证服务器上安装了网站依赖的包，而且版本要正确。

相应的解决方案，下面一一说明：

* 使用与生产环境一样的基础架构部署“过渡网站”（staging site），这么做可以测试部署的过程，确保部署真正的网站时操作正确。
* 可以在过渡网站中运行功能测试，确保服务器中安装了正确的代码和依赖包。而且为了测试网站的布局，我们编写了冒烟测试，这样就能知道是否正确加载了 CSS。
* 在可能运行多个 Python 应用的设备中，可以使用 virtualenv 管理包和依赖。
* 最后，一切操作都自动化完成。使用自动化脚本部署新版本，使用同一个脚本把网站部署到过渡环境和生产环境，这么做能尽量保证过渡网站和线上网站一样。

> 内容提要
>
> 1. 修改功能测试，以便在过渡服务器中运行
> 2. 架设服务器，安装全部所需的软件，再把过渡和线上环境使用的域名指向这个服务器
> 3. 使用 Git 把代码上传到服务器
> 4. 使用 Django 开发服务器在过渡环境的域名下尝试运行过渡网站
> 5. 学习如何在服务器中使用 virtualenv 管理项目的 Python 依赖
> 6. 让功能测试一直运行着，告诉我们哪些功能可以正常运行哪些不能
> 7. 使用 Gunicorn、Upstart 和域套接字配置过渡网站，以便能在生产环境中使用
> 8. 配置好之后，编写一个脚本，自动执行前面手动完成的操作，这样以后就能自动部署网站了。
> 9. 最后，使用自动化脚本把网站的生产版本部署到真正的域名下

### 8.2 一如既往，先写测试

稍微修改一下功能测试，让它能在过渡网站中运行。添加一个参数，指定测试所用的临时服务器地址：

```python
class NewVisitorTest(StaticLiveServerTestCase):
    # setUpClass 方法和 setUp 类似，也由 unittest 提供，但是它用于设定整个类的测试背景。
    # 也就是说，setUpClass 方法只会执行一次，而不会在每个测试方法运行前都执行。
    # LiveServerTestCase 和 StaticLiveServerCase 一般都在这个方法中启动测试服务器。
    @classmethod
    def setUpClass(cls):
        for arg in sys.argv:  # 在命令行中查找参数 liveserver(从 sys.argv 中获取)
            if "liveserver" in arg:
                # 如果找到了，就让测试类跳过常规的 setUpClass 方法，把过渡服务器的 URL 赋值给 server_url 变量
                cls.server_url = "http://" + arg.split("=")[1]
                return
        super().setUpClass()
        cls.server_url = cls.live_server_url

    @classmethod
    def tearDownClass(cls):
        if cls.server_url == cls.live_server_url:
            super().tearDownClass()
```

LiveServerTestCase 有一定的缺陷，其中一个缺陷是，总是假定你想使用它自己的测试服务器。因此，还要修改到用 self.live_server_url 的三处测试代码：

```python
def test_can_start_a_list_and_retrieve_it_later(self):
    # Y 访问在线待办事项应用的首页
    # self.browser.get("http://localhost:8000") # 不用硬编码了
    self.browser.get(self.server_url)
    [...]
    
    # F 访问首页
    # 页面中看不到 Y 的清单
    self.browser.get(self.server_url)
    [...]
    
def test_layout_and_styling(self):
	# Y 访问首页
	self.browser.get(self.server_url)
```

运行功能测试，确保上述改动没有破坏现有功能。

然后指定过渡服务器的 URL 再运行试试，使用的过渡服务器地址是 `superlists-staging.ottg.eu`。

可以看到，和预期一样，两个测试都失败了，因为还没架设过渡网站。看起来功能测试的测试对象是正确的，所以做一次提交吧。

```shell
git diff
git commit -am "Hack FT runner to be able to test staging"
```

### 8.3 注册域名

watch0.top

### 8.4 手动配置托管网站的服务器

可以把部署的过程分成两个任务：

* 配置新服务器，用于托管代码
* 把新版代码部署到配置好的服务器中

有些人喜欢每次部署都用全新服务器，不过这种做法只适用于大型的复杂网站，或者对现有网站做了重大修改。对于简单的网站来说，分别完成上述两个任务更合理。虽然最终这两个任务都要完全自动化，但就目前而言更适合手动配置。

#### 8.4.1 选择在哪里托管网站

托管网站有大量不同的方案，不过基本上可以归纳为两类：

* 运行自己的服务器（可能是虚拟服务器）
* 使用“平台即服务”（Platform-As-A-Service，PaaS）提供商，如 Heroku、DotCloud、OpenShift 或 PythonAnywhere

对小型网站而言，PaaS 的优势尤其明显，强烈建议考虑使用 PaaS。不过本书不适用 PaaS。要学习一些优秀的老式服务器管理方法，包括 SSH 和 Web 服务器配置。这些方法永远不会过时。

#### 8.4.2 搭建服务器

不规定怎么搭建服务器，不管你选择使用 Amazon AWS、Rackspace 或 Digital Ocean，还是自己的数据中心里的服务器，抑或楼梯后橱柜里的 Raspberry Pi，只要满足以下条件即可：

* 服务器的系统使用 Ubuntu（13.04 或以上）
* 有访问服务器的 root 权限
* 外网可访问
* 可以通过 SSH 登录

强烈推荐 Ubuntu 是因为其中安装了 Python 3.4，而且有一些配置 Nginx 的特殊方式。

#### 8.4.3 用户账户、SSH 和权限

如果需要创建非 root 用户，可以这么做：

```shell
# 这些命令必须以 root 用户的身份执行
root@server:$ useradd -m -s /bin/bash elspeth # 添加用户，名为 elspeth
# -m 表示创建 home 目录，-s 表示 elspeth 默认能使用 bash
root@server:$ usermod -a -G sudo elspeth # 把 elspeth 添加到 sudo 用户组
root@server:$ passwd elspeth # 设置 elspeth 的密码
root@server:$ su - elspeth # 把当前用户切换为 elspeth
elspeth@server:$
```

通过 SSH 登录时，建议别用密码，应该学习如何使用私钥认证。若想使用私钥认证，要从自己的电脑中获取公钥，然后将其附加到服务器用户账户下的 ~/.ssh/authorized_keys 文件中。使用 Bitbucket 或 GitHub 时也会有类似的操作。

这篇[文档](https://library.linode.com/security/ssh-keys)对比做了比较详细的说明（注意，在 Windows 中，ssh-keygen 包含在 Git-Bash 中）。

#### 8.4.4 安装 Nginx

我们需要一个 Web 服务器。在服务器中安装 Nginx 只需执行一次 apt-get 命令即可，然后再执行一个命令就能看到 Nginx 默认的欢迎页面：

```shell
sudo apt-get install nginx
sudo service nginx start
```

现在访问服务器的 IP 地址就能看到 Nginx 的 "Welcome to nginx" 页面。

如果没看到这个页面，可能是因为防火墙没有开放 80 端口。以 AWS 为例，或许你要配置服务器的 "Security Group" 才能打开 80 端口。

既然有 root 权限，下面就来安装所需的系统级关键软件：Python、Git、pip 和 virtualenv。

```shell
sudo apt-get install git python3 python3-pip
sudo pip3 install virtualenv
```

#### 8.4.5 解析过渡环境和线上环境所用的域名

要把过渡环境和线上环境所用的域名解析到服务器上。

#### 8.4.6 使用功能测试确认域名可用而且 Nginx 正在运行

为了确认一切顺利，可以再次运行功能测试。会发现失败消息稍微有点不同，其中一个消息和 Ngix 有关：

```shell
python3 manage.py test functional_tests --liveserver=watch0.top
```

#### 个人实践

结果：

```python
selenium.common.exceptions.NoSuchElementException: Message: Unable to locate element: {"method":"id","selector":"id_new_item"}
AssertionError: 'To-Do' not found in 'Welcome to nginx!'
FAILED (failures=1, errors=1)
```

另外，其中遇到了个问题，如果加上了这一段代码：

```python
     @classmethod
     def tearDownClass(cls):
         if cls.server_url == cls.live_server_url:
             super().tearDownClass()
```

会有一个 `AttributeError: type object 'NewVisitorTest' has no attribute 'server_thread'` 错误。

所以参考[网站](https://groups.google.com/forum/#!topic/obey-the-testing-goat-book/pokPKQQB2J8)的说法是，不用添加这么一段代码，全都注释掉吧。

### 8.5 手动部署代码

接着要让过渡网站运行起来，检查 Ngix 和 Django 之间能否通信。从这一步起，配置结束了，进入“部署”阶段。在部署的过程中，要思考如何自动化这些操作。

需要一个文件夹用来存放源码。假设源码放在一个非 root 用户的 home 目录中，比如说路径是 /home/elspeth（好像所有共享主机的系统都是这么设置的。无论使用什么主机，一定要以非 root 用户身份运行 Web 应用）。按照下面的文件结构存放网站的代码：

```shell
/home/elspeth
	sites
		www.live.my.website.com
			database
				db.sqlite3
			source
				manage.py
				superlists
				etc...
			static
				base.css
				etc...
			virtualenv
				lib
				etc...
		www.staging.my-website.com
			database
			etc...
```

每个网站（过渡网站，线上网站或其他网站）都放在各自的文件夹中。在各自文件夹中又有单独的子文件夹，分别存放源码、数据库和静态我呢间。采用这种结构的逻辑依据是，不同版本的网站源码可能会变，但数据库始终不变。静态文件夹也在同一个相对位置，即 ../static。最后，virtualenv 也有自己的子文件夹。

#### 8.5.1 调整数据库中的位置

首先，在 settings.py 中修改数据库的位置，而且要保证修改后的位置在本地电脑中也能使用。使用 os.path.abspath 能避免以后混淆当前工作目录：

```python
import os

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
[...]
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, '../database/db.sqlite3'),
    }
}
[...]
STATIC_ROOT = os.path.abspath(os.path.join(BASE_DIR, "../static"))
```

在本地测试一下：

```shell
mkdir ../database
python3 manage.py migrate --noinput
ls ../database/
```

现在可以正常使用了，做次提交：

```shell
git diff # 会看到 settings.py 中的改动
git commit -am "move sqlite database outside of main source tree"
```

把源码上传到服务器所需的全部 Base 命令如下。export 的作用是创建一个可在 base 中使用的 “本地变量”：

```shell
export SITENAME=superlists-staging.ottg.eu
mkdir -p ~/sites/$SITENAME/database
mkdir -p ~/sites/$SITENAME/static
mkdir -p ~/sites/$SITENAME/virtualenv
# 要把下面这行命令中的 URL 换成你自己仓库的 URL
git clone https://github.com/hjwp/book-example.git ~/sites/$SITENAME/source
```

> 使用 export 定义的 Bash 变量只在当前终端会话中有效。如果退出服务器后再登陆，就需要重新定义。这个特性有点隐晦，因为 Bash 不会报错，而是直接用空字符串表示未定义的变量，这种处理方式会导致诡异的结果。可以执行 `echo $SITENAME`

现在网站安装好了，在开发服务器中运行试试——这是一个冒烟测试，检查所有活动部件是否连接起来了：

```shell
cd ~/sites/$SITENAME/source
python3 manage.py runserver
```

可以发现还没有安装 Django。

#### 创建虚拟环境

使用 virtualenv 能解决多用户使用 Django 的问题。virtualenv 使用一种优雅的方式在不同的位置安装 Python 包的不同版本，把不同的版本放在各自的 “虚拟环境” 中。

先在本地电脑中试一下：

```shell
pip3 install virtualenv # 在 Linux/Mac OS 中需要使用 sudo
```

沿用为服务器规划的文件夹结构：

```shell
virtualenv --python=python3 ../virtualenv
ls ../virtualenv/
```

#### 个人实践

**注意确保 virtualenv 全路径都是 ASCII 字符。**

上述命令会创建一个文件夹，路径是 ../virtualenv。在这个文件夹中有自己的一份 Python 和 pip，还有一个位置用于安装 Python 包。这个文件夹是自成一体的 Python “虚拟”环境。若想使用这个虚拟环境，可以执行 activate 脚本，修改系统路径和 Python 路径，让系统使用这个虚拟环境中的可执行文件和包：

```shell
which python3
source ../virtualenv/bin/activate
which python # 切换到虚拟环境中的 python 了
python3 manage.py test lists
```

> 在 Windows 中使用 virtualenv
>
> 在 Windows 中有细微的差别，使用时要注意两件事：
>
> * virtualenv/bin 文件夹叫 virtualenv/Scripts
> * 在 Git-Bash 中不要试图运行 active.bat，这个文件是为 DOS shell 编写的，要执行 source ..\virtualenv\Scripts\activate。source 才是关键。

看到了错误消息 "ImportError: No module named django"，这是因为还没在虚拟环境中安装 Django。下面进行安装，可以看到 Django 被安装到虚拟环境的 site-packages 文件夹中：

```shell
pip install django
python3 manage.py test lists
ls ../virtualenv/lib/python3.4/site-packages/
```

为了保存虚拟环境中所需的包列表，也为了以后能再次创建相同的虚拟环境，可以执行 pip freeze 命令，创建一个 requirements.txt 文件，再把这个文件添加到仓库中：

```shell
pip freeze > requirements.txt
deactivate
cat requirements.txt
git add requirements.txt
git commit -m "Add requirements.txt for virtualenv"
```

> Django 1.7 还没发布的话，可以使用 `pip install https://github.com/django/ django/archive/stable/1.7.x.zip` 安装这个版本。在 requirements.txt 中可以 把“Django==1.7”换成这个 URL,pip 很智能,能解析 URL。可以在本地 执行pip install -r requirements.txt命令,测试复建虚拟环境。会看到 pip 提示,所有包都已安装。

现在执行 git push 命令，把更新推送到代码分享网站中。

```shell
git push
```

然后，在服务器上拉取这些更新，创建一个虚拟环境，再执行 pip install -r requirements.txt 命令，让服务器中的虚拟环境和本地一样：

```shell
git pull # 可能会要求你先做 git config
virtualenv --python=python3 ../virtualenv
../virtualenv/bin/pip3 install -r ../virtualenv/requirements.txt
../virtualenv/bin/python3 manage.py runserver
```

看起来服务器运行得很顺畅，按 Ctrl-C 键暂时关闭服务器。

注意，使用虚拟环境不一定要执行 activate，直接指定虚拟环境中的 python 或 pip 路径也行。在服务器上，我们就直接使用路径。

看起来服务器运行得很顺畅，按 Ctrl-C 键暂时关闭服务器。

注意，使用虚拟环境并不一定要执行 activate，直接指定虚拟环境中的 python 或 pip 的路径也行。在服务器上，我们就直接使用路径。

#### 8.5.3 简单配置 Nginx

下面创建一个 Nginx 配置文件，把过渡网站收到的请求交给 Django 处理。如下是一个极简的配置(`server: /etc/nginx/sites-available/watch0.top`)：

```json
server {
  listen 80;
  server_name watch0.top;
  
  location / {
    proxy_pass http://localhost:8000;
  }
}
```

这个配置只对过渡网站e的域名有效，而且会把所有请求“代理”到本地 8000 端口，等待 Django 处理请求后得到的响应。

把这个配置保存为 superlists 文件，放在 /etc/nginx/sites-available 文件夹里，然后创建一个符号链接，把这个文件加入启用的网站列表中：

```shell
echo $SITENAME # 检查在这个 shell 会话中是否还能使用这个变量获取网站名
sudo ln -s ../sites-available/$SITENAME /etc/nginx/sites-enabled/$SITENAME
ls -l /etc/nginx/sites-enabled # 确认符号链接是否在那里
```

在 Debian 和 Ubuntu 中，这是保存 Nginx 配置的推荐做法——把真正的配置文件放在 sites-available 文件夹中，然后在 sites-enabled 文件夹中创建一个符号链接。这么做便于切换网站的在线状态。

还可以把默认的 "Welcome to nginx" 页面删除，避免混淆：

```shell
sudo rm /etc/nginx/sites-enabled/default
```

现在测试一下配置：

```shell
sudo service nginx reload
/virtualenv/bin/python3 manage.py runserver
```

> 如果用的是长域名，还要编辑 /etc/nginx/nginx.conf 文件，把 server_names_hash_bucket_size 64; 这行的注释去掉，这样才能使用长域名。执行 reload 命令时，如果配置有问题， Nginx 会提醒你。

#### 个人实践

之间建错了，名字全用的 superlists，但是自己的域名并不是这个。

删除符号链接：

```shell
# 删除符号链接，有创建就有删除
rm -rf   symbolic_name   # 切换到对应目录下
```

统一改成自己的域名之后发现成功了。

接下来看看功能测试的结果如何：`python3 manage.py test functional_tests --liveserver=watch0.top`

尝试提交新待办事项时测试失败了，因为还没设置数据库。运行测试时你可能注意到了 Django 的黄色报错页，页面中显示的消息和测试失败的消息差不多。

#### 8.5.4 使用迁移创建数据库

执行 migrate 命令，可以指定 --noinput 参数，禁止两次询问。

```shell
../virtualenv/bin/python3 manage.py migrate --noinput
ls ../database
../virtualenv/bin/python3 manage.py runserver
```

再运行功能测试试试，发现网站运行起来了。

> 如果看到 502 - Bad Gateway 错误，可能是因为执行 migrate 命令之后忘记使用 manage.py runserver 重启开发服务器

### 8.6 为部署到生产环境做好准备

在生产环境中真的不能使用 Django 开发服务器。而且，不能依靠 runserver 手动启动服务器。

#### 8.6.1 换用 Gunicorn

Django 提供了很多功能，包括 ORM、各种中间件、网站后台等。

```shell
../virtualenv/bin/pip install gunicorn
```

Gunicorn 需要知道 WSGI（Web Server Gateway Interface，Web 服务器网关接口）服务器的路径。这个路径往往可以使用一个名为 application 的函数获取。Django 在文件 superlists/wsgi.py 中提供了这个函数：

```shell
../virtualenv/bin/gunicorn todo_app.wsgi:application # 注意 todo_app 根据自己文件夹命名
```

如果现在访问网站，会发现所有样式都失效了。如果运行功能测试，会看到的确出问题了。添加待办事项的测试能顺利通过，但布局和样式的测试失败了。

样式失效的原因是，Django 开发服务器会自动伺服静态文件，但 Gunicorn 不会。现在配置 Nginx，让它代为伺服静态文件。

#### 8.6.2 让 Nginx 伺服静态文件

首先，执行 collectstatic 命令，把所有静态文件复制到一个 Nginx 能找到的文件夹中：

```shell
../virtualenv/bin/python3 manage.py collectstatic --noinput
ls ../static/
```

下面配置 Nginx，让它伺服静态文件。

```json
server {
  listen 80;
  server_name watch0.top;
 
  location /static {
    alias /home/watch/sites/superlists/source/static;
  }
 
  location / {
    proxy_pass http://localhost:8000;
  }
}
```

然后重启 Nginx 和 Gunicorn：

```shell
sudo service nginx reload
../virtualenv/bin/gunicorn todo_app.wsgi:application
```

接下来可以运行功能测试进行确认。

#### 8.6.3 换用 Unix 套接字

如果想要同时伺服过渡网站和线上网站，这两个网站就不能共用 8000 端口。可以为不同的网站分配不同端口。但更好的方法是使用 Unix 域套接字。域套接字类似于硬盘中的文件，不过还可以用来处理 Nginx 和 Gunicorn 之间的通信。要把套接字保存在文件夹 /tmp 中。下面修改 Nginx 的代理设置：

```json
server {
  listen 80;
  server_name watch0.top;
 
  location /static {
    alias /home/watch/sites/superlists/source/static;
  }
 
  location / {
    proxy_set_header Host $host;
    proxy_pass http://unix:/tmp/watch0.top.socket;
  }
}
```

#### 个人实践

vim 全选删除操作：ggVGd。

* gg 让光标移到首行，在 **vim** 才有效，vi 中无效
* V   是进入Visual(可视）模式
* G  光标移到最后一行
* d  删除**选**中内容

`proxy_set_header` 的作用是让 Gunicorn 和 Django 知道它们运行在哪个域名下。`ALLOWED_HOSTS` 安全功能需要这个设置。

现在重启 Gunicorn，不过这一次告诉它监听套接字，而不是默认的端口：

```shell
sudo service nginx reload
../virtualenv/bin/gunicorn --bind unix:/tmp/watch0.top.socket todo_app.wsgi:application
```

还要再次运行功能测试，确保所有测试仍能通过：

```shell
python3 manage.py test functional_tests --liveserver=watch0.top
```

#### 8.6.4 把 DEBUG 设为 False，设置 ALLOWED_HOSTS

在自己的服务器中开启调试模式有利于排查问题，但[显示满页的调用跟踪不安全](https://docs.djangoproject.com/en/1.7/ref/settings/#debug)。

在 settings.py 中的顶部有 DEBUG 设置项。如果把它设为 False，还需要设置另一个选项，`ALLOWED_HOSTS`。这个设置在 Django 1.5 中添加，目的是[提高安全性](https://docs.djangoproject.com/en/1.7/ ref/settings/#std:setting-ALLOWED_HOSTS)。不过，在默认的 settings.py 中没有为这个功能提供有帮助的注释。在服务器中按照下面的方式修改 settings.py。

```python
# 安全警告：别再生产环境中开启调试模式
DEBUG = False

TEMPLATE_DEBUG = DEBUG

# DEBUG=False 时需要这项设置
ALLOWED_HOSTS = ["watch0.top"]
```

然后重启 Gunicorn，再运行功能测试，确保一切正常。

> 在服务器中别提交这些改动。现在只是为了让网站正常运行做的小调整，不是需要纳入仓库的改动。一般来说，简单起见，只会在本地电脑中把改动提交到 Git 仓库。如果需要把代码同步到服务器中，再使用 git push 和 git pull。

#### 8.6.5 使用 Upstart 确保引导时启动 Gunicorn

部署的最后一步是确保服务器引导时自动启动 Gunicorn，如果 Gunicorn 崩溃了还要自动重启。在 Ubuntu 中，可以使用 Upstart 实现这个功能。

```json
# server:/etc/init/gunicorn-watch0.conf
description "Gunicorn server for watch0.top"

start on net-device-up # 确保只在服务器联网时才启动 Gunicorn
stop on shutdown

respawn # 如果进程崩溃，respawn 会自动重启 Gunicorn

setuid watch # setuid 确保以 watch 用户的身份运行 Gunicorn 进程
chdir /home/watch/sites/superlists/source/todo_app # 设定工作目录

exec ../virtualenv/bin/gunicorn --bind unix:/tmp/watch0.top.socket todo_app.wsgi:application # 真正要执行的进程
```

Upstart 脚本保存在 /etc/init 中，而且文件名必须以 .conf 结尾。

现在可以使用 start 命令启动 Gunicorn 了：

```shell
sudo start gunicorn-watch0.top
```

然后可以再次运行功能测试。

#### 个人实践

发现不支持中文，所以最终填入文件的内容是：

```json
description "Gunicorn server for watch0.top"

start on net-device-up
stop on shutdown

respawn

setuid watch
chdir /home/watch/sites/superlists/source/todo_app

exec ../virtualenv/bin/gunicorn --bind unix:/tmp/watch0.top.socket todo_app.wsgi:application
```

#### 8.6.6 保存改动：把 Gunicorn 添加到 requirements.txt

回到本地仓库，应该把 Gunicorn 添加到虚拟环境所需的包列表中：

```shell
source ../virtualenv/bin/activate # 如有必要
pip install gunicorn
pip freeze > requirements.txt
deactivate
git commit -am "Add gunicorn to virtualenv requirements"
git push
```

### 8.7 自动化

总结一下配置和部署的过程。

* 配置
  * 假设有用户账户和 home 目录
  * apt-get nginx git python-pip
  * pip install virtualenv
  * 添加 Nginx 虚拟主机配置
  * 添加 Upstart 任务，自动启动 Gunicorn
* 部署
  * 在 ~/sites 中创建目录结构
  * 拉取源码，保存到 source 文件夹中
  * 启用 ../virtualenv 中的虚拟环境
  * pip install -r requirements.txt
  * 执行 manage.py migrate，创建数据库
  * 执行 collectstatic 命令，收集静态文件
  * 在 settings.py 中设置 DEBUG = False 和 ALLOWED_HOSTS
  * 重启 Gunicorn
  * 运行功能测试，确保一切正常

假设现在不用完全自动化配置过程，则应该把 Nginx 和 Upstart 配置文件保存起来，便于以后重用。下面把这两个配置文件保存到仓库中一个新建的子文件夹中：

```shell
mkdir deploy_tools
```

```json
# deploy_tools/nginx.template.conf
server {
  listen 80;
  server_name SITENAME;
  
  location /static {
    alias /home/watch/sites/SITENAME/static;
  }

  location / {
    proxy_set_header Host $host;
    proxy_pass http://unix:tmp/SITENAME.socket;
  }
}
```

```json
# deploy_tools/gunicorn-upstart.template.conf
description "Gunicorn server for SITENAME"

start on net-device-up
stop on shutdown

respawn

setuid watch
chdir /home/watch/sites/SITENAME/source

exec ../virtualenv/bin/gunicorn --bind unix:/tmp/SITENAME.socket superlists.wsgi:application
```

以后使用这两个文件配置新网站就容易了，查找替换 SITENAME 即可。

其他步骤做些笔记就行了，在仓库中建个文件保存说明：

```markdown
配置新网站
=======

## 需要安装的包
* nginx
* Python 3
* Git
* pip
* virtualenv

以 Ubuntu 为例，可以执行下面的命令安装：
  sudo apt-get install nginx git python3 python3-pip
  sudo pip3 install virtualenv
  
## 配置 Nginx 虚拟主机
* 参考 nginx.template.conf
* 把 SITENAME 替换成所需的域名，例如 watch0.top

## Upstart 任务
* 参考 gunicorn-upstart.template.conf
* 把 SITENAME 替换成所需的域名，例如 watch0.top

## 文件夹结构：
假设有用户账户，home 目录为 /home/username

/home/username
	sites
		SITENAME
			database
			source
			static
			virtualenv
```

然后提交上述改动：

```shell
git add deploy_tools
git status # 看到三个新文件
git commit -m "Notes and template config files for provisioning"
```

> 测试驱动服务器配置和部署
>
> * 测试去除了部署过程中的某些不确定性
> * 常见痛点：数据库、静态文件、依赖和自定义设置
> * 测试允许我们做实验

