# 第一部分 TDD 和 Django 基础

* 介绍测试驱动开发（Test-Driven Development，TDD）的基础知识
* 每个阶段都要先写测试
* 涵盖使用 Selenium 完成的功能测试，以及单元测试
* TDD 流程（单元测试/编写代码）循环
  * 重构
  * 版本控制系统（Git）

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

### 1.2 让 Django 运行起来

