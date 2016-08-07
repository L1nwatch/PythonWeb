## 第 9 章 使用 Fabric 自动部署

手动部署过渡服务器的意义通过自动部署才能体现出来。部署的过程能重复执行，我们才能确信部署到生产环境时不会出错。

使用 Fabric 可以在服务器中自动执行命令。可以系统全局安装 Fabric，因为它不是网站的核心功能，所以不用放到虚拟环境中，也不用加入 requirements.txt 文件。在本地电脑中执行下述命令安装 Fabric：`pip install fabric`

> 在 Windows 中安装 Fabric
>
> Fabric 依赖于 pycrypto，而这个包需要编译。在 Windows 中编译相当痛苦，所以使用别人预先编译好的二进制安装程序往往更快捷。Michael Foord 提供了一些预先编译好的 [pycrypto Windows 二进制安装程序](http://www.voidspace.org.uk/python/ modules.shtml#pycrypto)。
>
> 在 Windows 中安装 Fabric 的过程如下：
>
> * 从前面提供的地址下载并安装 pycrypto
> * 使用 pip 安装 Fabric
>
> 还有一个预编译好的 Python 包 Windows 安装[程序源](http://www.lfd.uci.edu/~gohlke/ pythonlibs/)也很棒，由 Christoph Gohlke 维护。

Fabric 的使用方法一般是创建一个名为 fabfile.py 的文件，在这个文件中定义一个或多个函数，然后使用命令行工具 fab 调用：`fab function_name, host=SERVER_ADDRESS`。这个命令会调用名为 `function_name` 的函数，并传入要连接的服务器地址 `SERVER_ADDRESS`。fab 命令还有很多其他参数，可以指定用户名和密码等，详情可执行 fab --help 命令查阅。

### 9.1 分析一个 Fabric 部署脚本

Fabric 的用法，通过实例来说明，以下这个脚本自动执行前一章用到的所有部署步骤。在这个脚本中，主函数是 main，我们在命令行中要调用的就是这个函数。除此之外，脚本中还有多个辅助函数。从命令行传入的服务器地址保存在 env.host 中。

```python
from fabric.contrib.files import append, exists, sed
from fabric.api import env, local, run

__author__ = '__L1n__w@tch'

# 要把常量 REPO_URL 的值改成代码分享网站中你仓库的 URL
REPO_URL = "https://github.com/L1nwatch/PythonWeb.git"


def deploy():
    # env.host 的值是在命令行中指定的服务器地址，例如 watch0.top, env.user 的值是登录服务器时使用的用户名
    site_folder = "/home/{}/sites/{}".format(env.user, env.host)
    source_folder = site_folder + "/source"

    _create_directory_structure_if_necessary(site_folder)
    _get_latest_source(source_folder)
    _update_settings(source_folder, env.host)
    _update_virtualenv(source_folder)
    _update_static_files(source_folder)
    _update_database(source_folder)
```

创建目录结构的方法如下，即便某个文件夹已经存在也不会报错：

```python
def _create_directory_structure_if_necessary(site_folder):
    for sub_folder in ("database", "static", "virtualenv", "source"):
        # run 的作用是在服务器中执行指定的 shell 命令
        # mkdir -p 是 mkdir 的一个有用变种，它有两个优势，其一是深入多个文件夹层级创建目录；其二，只在必要时创建目录。
        run("mkdir -p {}/{}".format(site_folder, sub_folder))
```

然后拉取源码：

```python
def _get_latest_source(source_folder):
    # exists 检查服务器中是否有指定的文件夹或文件。我们指定的是隐藏文件夹 .git，检查仓库是否已经克隆到文件夹中。
    if exists(source_folder + "/.git"):
        # 很多命令都以 cd 开头，其目的是设定当前工作目录。Fabric 没有状态记忆，所以下次运行 run 命令时不知道在哪个目录中
        # 在现有仓库中执行 git fetch 命令是从网络中拉取最新提交
        run("cd {} && git fetch".format(source_folder))
    else:
        # 如果仓库不存在，就执行 git clone 命令克隆一份全新的源码。
        run("git clone {} {}".format(REPO_URL, source_folder))
        # Fabric 中的 local 函数在本地电脑中执行命令，这个函数其实是对 subprocess.Popen 的再包装。
        # 我们捕获 git log 命令的输出，获取本地仓库中当前提交的哈希值，这么做的结果是，服务器中代码将和本地检出的代码版本一致
    current_commit = local("git log -n 1 --format=%H", capture=True)
    # 执行 git reset --hard 命令，切换到指定的提交。这个命令会撤销在服务器中对代码仓库所做的任何改动。
    run("cd {} && git reset --hard {}".format(source_folder, current_commit))
```

> 为了让这个脚本可用，你要执行 git push 命令把本地仓库推送到代码分享网站，这样服务器才能拉取仓库，再执行 git reset 命令。如果你遇到 Could not parse object 错误，可以执行 git push 命令。

然后更新配置文件，设置 `ALLOWED_HOSTS` 和 `DEBUG`，还要创建一个密钥：

```python
def _update_settings(source_folder, site_name):
    settings_path = source_folder + "/superlists/settings.py"
    # Fabric 提供的 sed 函数作用是在文本中替换字符串。这里把 DEBUG 的值由 True 改成 False
    sed(settings_path, "DEBUG = True", "DEBUG = False")
    # 这里使用 sed 调整 ALLOWED_HOSTS 的值，使用正则表达式匹配正确的代码行
    sed(settings_path, "ALLOWED_HOSTS = .+$", "ALLOWED_HOSTS = ['{}']".format(site_name))
    secret_key_file = source_folder + "/superlists/secret_key.py"
    # Django 有几处加密操作要使用 SECRET_KEY: cookie 和 CSRF 保护。在服务器中和(可能公开的)源码仓库中使用不同的密钥是个好习惯。
    # 如果还没有密钥，这段代码会生成一个新密钥，然后写入密钥文件。有密钥后，每次部署都要使用相同的密钥。
    # 更多信息参见 [Django 文档](https://docs.djangoproject.com/en/1.7/topics/signing/)
    if not exists(secret_key_file):
        chars = "abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)"
        key = "".join(random.SystemRandom().choice(chars) for _ in range(50))
        append(secret_key_file, "SECRET_KEY = '{}'".format(key))
    # append 的作用是在文件末尾添加一行内容
    # (如果要添加的行已经存在，就不会再次添加；但如果文件末尾不是一个空行，它却不能自动添加一个空行。因此加上了 \n。)
    # 使用的是 "相对导入"(relative import，使用 from .secret key 而不是 from secret_key)
    # 目的是确保从本地而不是从 sys.path 中其他位置的模块导入。
    append(settings_path, "\nfrom .secret_key import SECRET_KEY")
```

> 有些人，建议使用环境变量设置密钥等，你觉得在你的环境中哪种方法安全，就使用哪种方法。

接下来创建或更新虚拟环境：

```python
def _update_virtualenv(source_folder):
    virtualenv_folder = source_folder + "/../virtualenv"
    # 在 virtualenv 文件夹中查找可执行文件 pip，以检查虚拟环境是否存在
    if not exists(virtualenv_folder + "/bin/pip"):
        run("virtualenv --python=python3 {}".format(virtualenv_folder))
    # 然后和之前一样，执行 pip install -r 命令
    run("{}/bin/pip install -r {}/requirements.txt".format(virtualenv_folder, source_folder))
```

更新静态文件只需要一个命令：

```python
def _update_static_files(source_folder):
    # 如果需要执行 Django 的 manage.py 命令，就要指定虚拟环境中二进制文件夹，确保使用的是虚拟环境中的 Django 版本，而不是系统中的版本
    run("cd {} && ../virtualenv/bin/python3 manage.py collectstatic --noinput".format(source_folder))
```

最后，执行 manage.py migrate 命令更新数据库：

```python
def _update_database(source_folder):
    run("cd {} && ../virtualenv/bin/python3 manage.py migrate --noinput".format(source_folder))
```

### 9.2 试用部署脚本

可以在现有的过渡服务器中使用这个部署脚本——这个脚本可以在现有的服务器中运行，也可以在新服务器中运行。如果再次运行，这个脚本不会做任何操作。

```shell
cd deploy_tools
fab deploy:host=watch@watch0.top
```

> 配置 Fabric
>
> 如果使用 SSH 密钥登录，密钥存储在默认的位置，而且本地电脑和服务器使用相同的用户名，那么无需配置即可直接使用 Fabric。如果不满足这几个条件，就要配置用户名、SSH 密钥的位置或密码等，才能让 fab 执行命令。
>
> 这几个信息可在命令行中传给 Fabric。更多信息可执行 `fab --help` 命令查看，或者阅读 [Fabric 的文档](http://docs.fabfile.org/)。

#### 9.2.1 部署到线上服务器

下面在线上服务器中试试这个脚本：

```shell
fab deploy:host=watch@watch0.top # 注意 Python3 会报错，得用 Python2 安装 fabric 后再运行(2016.08.07)
```

#### 【个人实践】

```shell
# 重新弄了个仓库，专门用来搭建这个网站的
https://github.com/L1nwatch/superlists_for_pythonweb.git

# 然后重新 git
git https://github.com/L1nwatch/superlists_for_pythonweb.git

# 之后切换到对应目录
fab deploy:host=watch@watch0.top

# 报错了，第一个错就是
Fatal error: Low level socket error connecting to host localhost: Connection refused
找了下相关资料，发现是我的 SSH 端口号并不是默认的 22，于是改成这样：
fab deploy:host=watch@watch0.top:29999 # 即输入自己的 SSH 端口号

# 接着不断根据提示的错误进行更改
最终无错即可
```

#### 9.2.2 使用 sed 配置 Nginx 和 Gunicorn

把网站放到生产环境之前，根据配置笔记，还要使用模板文件创建 Nginx 虚拟主机和 Upstart 脚本。使用 Unix 命令行工具完成：

```shell
sed "s/SITENAME/watch0.top/g" deploy_tools/nginx.template.conf | sudo tee /etc/nginx/sites-available/watch0.top
```

sed（stream editor, 流编辑器）的作用是编辑文本流。Fabric 中进行文本替换的函数也叫 sed，这并不是巧合。这里，使用 `s/replaceme/withthis/g` 句法把字符串 SITENAME 替换成网站的地址。然后使用管道操作（|）把文本流传给一个有 root 权限的用户处理（sudo），把传入的文本流写入一个文件，即 sites-available 文件夹中的一个虚拟主机配置文件。

现在可以激活这个文件配置的虚拟主机：

```shell
sudo ln -s ../sites-available/watch0.top /etc/nginx/sites-enabled/watch0.top
```

然后编写 Upstart 脚本：

```shell
sed "s/SITENAME/watch0.top/g" deploy_tools/gunicorn-upstart.template.conf | sudo tee /etc/init/gunicorn-watch0.top.conf
```

最后，启动这两个服务：

```shell
sudo service nginx reload
sudo start gunicorn-watch0.top
```

成功运行后可以提交把 fabfile.py 添加到仓库中：

```shell
git add deploy_tools/fabfile.py
git commit -m "Add a fabfile for automated deploys"
```

### 9.3 使用 Git 标签标注发布状态

最后还要做些管理操作。为了保留历史标记，使用 Git 标签（tag）标注代码库的状态，指明服务器中当前使用的是哪个版本：

```shell
git tag LIVE
export TAG=`date +DEPLOYED-%F/%H%M` # 生成一个时间戳
echo $TAG # 会显示 "DEPLOYED-" 和时间戳
git tag $TAG
git push origin LIVE $TAG # 推送标签
```

现在，无论何时都能轻易地查看当前代码库和服务器中的版本有何差异。看一下提交历史中的标签：

```shell
git log --graph --oneline --docorate
```

### 9.4 延伸阅读

可以考虑使用 Fabric 的替代品 Ansible。

### 自己的测试：

自己编写的 fabfile.py 能够完成从 git 库一直到配置 nginx 和 gunicorn 了，以下完整的步骤（假定当前是一个刚装好的 Ubuntu 系统）：

```shell

```

