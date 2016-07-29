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
../virtualenv/bin/pip install -r requirement.stxt
../virtualenv/bin/python3 manage.py runserver
```

看起来服务器运行得很顺畅，按 Ctrl-C 键暂时关闭服务器。

注意，使用虚拟环境不一定要执行 activate，直接指定虚拟环境中的 python 或 pip 路径也行。在服务器上，我们就直接使用路径。