## 第 1 章 使用功能测试协助安装 Django

### 1.1 遵从测试山羊的教诲，没有测试什么也别做

Web 开发的第一步通常是安装和配置 Web 框架。下载、安装、配置、运行脚本

使用 TDD 时要转换思维方式，做测试驱动开发时，记得先测试。

在 TDD 的过程中，第一步始终是编写测试，然后运行，看是否和预期一样失效，只有失败了才能继续下一步——编写应用程序。

首先，要检查是否安装了 Django，并且能够正常运行。检查的方法是，在本地电脑中能否启动 Django 的开发服务器，并在浏览器中查看能否打开网页。使用浏览器自动化工具 Selenium 完成这个任务。

新建一个 Python 文件，命名为 functional_tests.py，并输入以下代码：

```Python
from selenium import webdriver

__author__ = '__L1n__w@tch'

if __name__ == "__main__":
    browser = webdriver.Chrome()
    browser.get("http://localhost:8000")
    assert 'Django' in browser.title
```

这段代码的工作：

* 启动一个 Selenium webdriver，打开一个真正的 Firefox 浏览器窗口
* 在这个浏览器中打开期望本地电脑伺服的网页
* 检查（测试断言）这个网页的标题中是否包含单词 Django

#### 个人实践

实践时报了错误，其中一个：

```Python
'chromedriver' executable needs to be in PATH. Please see https://sites.google.com/a/chromium.org/chromedriver/home
```

想想是不是因为 Selenium 没配置好，自己试着配置一下：

* [安装 Java JDK 环境](http://www.oracle.com/technetwork/java/javase/downloads)，这个好像是不需要的，或者说是因为我已经安装了 JRE 的缘故？
* 安装 Selenium-Server：Homebrew 安装
* [安装 chromedriver](https://sites.google.com/a/chromium.org/chromedriver/downloads)

### 1.2 让 Django 运行起来

使用 Django 的第一步是创建项目，网站就放在这个项目中。Django 为此提供了一个命令行工具：

`$ django-admin.py startproject superlists`

这个命令会创建一个名为 superlists 的文件夹，并在其中创建一些文件和子文件夹。

在 superlists 文件夹中还有一个名为 superlists 的文件夹。回顾 Django 的历史，会找到出现这种结构的原因。现在，superlists/superlists 文件夹的作用是保存应用于整个项目的文件，例如 settings.py 的作用是存储网站的全局配置信息。

还有 manage.py，这个文件作用之一是运行开发服务器。执行命令`cd superlists`，进入顶层文件夹 superlists，然后执行`python3 manage.py runserver`

让这个命令一直运行着，再打开一个命令行窗口，在其中再次尝试运行测试`python3 functional_test.py`

可以发现没有 AssertionError 以及 Selenium 弹出的浏览器窗口中显示的页面不一样了。

如果想退出开发服务器，可以回到第一个 shell 中，按 Ctrl-C 键。

#### 浏览器的问题

发现 Selenium 库支持好几种浏览器，比如说 Chrome（需要下载 chromedriver）等，自己平常就是用 Chrome 查找资料的，所以如果开发的时候也用 Chrome 感觉不太方便。

再此替换为 Firefox 浏览器，步骤如下：

* 安装 Firefox 浏览器
* 直接就可以使用 webdriver.Firefox() 来开启了

### 创建 Git 仓库

把作品提交到版本控制系统（Version Control System，VCS）。这里使用 Git 作为 VCS。

先把 functional_tests.py 移到 superlists 文件夹。然后执行 git init 命令，创建仓库：

```shell
ls
mv functional_test.py superlists/
cd superlists
git init .
```

接着，添加想提交的文件——其实所有文件都要提交：

```shell
ls
# db.sqlite3 是数据库文件。不想把这个文件纳入版本控制，因此要将其添加到一个特殊的文件 .gitigonre 中，告诉 Git 将其忽略：
echo "db.sqlite3" >> .gitignore
```

接下来，可以添加当前文件夹中的其他内容了：

```shell
git add .
git status
```

会发现添加了很多 .pyc 文件，这些文件没必要提交。将其从 Git 中删掉，并添加到 .gitignore 中：

```shell
git rm -r --cached superlists/__pycache__
echo "__pycache__" >> .gitignore
echo "*.pyc" >> .gitignore
```

Git 别名：比如说可以把 git status 别名为 git st

做第一次提交：

```shell
git commit
```

输入 git commit 后，会弹出一个编辑器窗口，让你输入提交信息。

接下来还要学习如何把代码推送到云端的 VCS 托管服务中，例如 GitHub 或 BitBucket。