## 附录 A PythonAnywhere

### A.1 使用 Xvfb 在 Firefox 中运行 Selenium 会话

PythonAnywhere 是只有终端的环境，所以没有显示器就无法打开 Firefox。但是我们可以使用虚拟显示器。

解决办法是使用 Xvfb（X Vritual Framebuffer 的简称）。在没有真正的显示器的服务器中，Xvfb 会启动一个虚拟显示器，供 Firefox 使用。

`xvfb-run` 命令的作用是，在 Xvfb 中执行下一个命令。使用这个命令就会看到预期失败：

```shell
xvfb-run python3 functional_tests.py
```

### A.2 以 PythonAnywhere Web 应用的方式安装 Django

安装 Django。不建议使用 `django-admin.py start project` 命令，推荐使用 PythonAnywhere "Web" 选项卡中的快速设置。添加一个新 Web 应用，选择 Django 和 Python 3，然后在项目名中填写 superlists。

而且，不要在终端里运行测试服务器，让它运行在地址 `localhost:8000` 上，可以使用 PythonAnywhere 为 Web 应用提供的真实地址。

> 每次修改代码之后都要点击 “Reload Web App”（重新加载 Web 应用）按钮，更新网站。

也可以在终端运行开发服务器，但有个问题，PythonAnywhere 的终端不一定运行在同一台服务器中，所以无法保证运行测试的终端和运行服务器的终端是同一个。而且，如果在终端里运行服务器，没有简单的方法视觉检查网站的外观。

### A.3 清理 `/tmp` 目录

Selenium 和 Xvfb 会在 `/tmp` 目录中留下很多垃圾，如果关闭的方式不优雅，情况更糟（所以前文才要使用 `try/finally` 语句）。

遗留的东西太多，可能会用完存储配额，所以要经常清理 `/tmp` 目录：

`rm -rf /tmp/*`

### A.4 截图

建议使用 `time.sleep` 在功能测试运行的过程中暂停一会儿，这样才能在屏幕上看到 `Selenium` 浏览器。在 PythonAnywhere 做不到这一点，因为浏览器运行在虚拟显示器中。不过你可以检查线上网站。

对运行在虚拟显示器中的测试做视觉检查，最好的方法是使用截图。

### A.5 关于部署

如果想一直使用 PythonAnywhere，可以把应用部署到其他域名下。你需要一个自己的域名和一个 PythonAnywhere 付费账户。就算不这么做，也得确保功能测试能在真实的过渡网站中运行，而不能使用 LiveServerTestCase 提供的多线程服务器。

