## 第 6 章 完成最简可用的网站
### 6.1 确保功能测试之间相互隔离

如何隔离测试？运行功能测试后待办事项一直存在于数据库中，这会影响下次测量的结果。

运行单元测试时，Django 的测试运行程序会自动创建一个全新的测试数据库（和应用真正使用的数据库不同），运行每隔测试之前都会清空数据库，等所有测试都运行完之后，再删除这个数据库。但是功能测试目前使用的是应用真正使用的数据库 db.sqlite3。

这个问题的解决方法之一是自己动手，在 `functional_tests.py` 中添加执行清理任务的代码。这样的任务最适合在 setUp 和 tearDown 方法中完成。

不过从 1.4 版本开始，Django 提供的一个新类，LiveServerTestCase，它可以代我们完成这一任务。这个类会自动创建一个测试数据库（跟单元测试一样），并启动一个开发服务器，让功能测试在其中运行。

LiveServerTestCase 必须使用 manage.py，由 Django 的测试运行程序运行。从 Django 1.6 开始，测试运行程序查找所有名字以 test 开头的文件。为了保持文件结构清晰，要新建一个文件夹保存功能测试，让它看起来就像一个应用。Django 对这个文件夹的要求只有一个——必须是有效的 Python 模块，即文件夹中要有一个 `__init__.py` 文件。

```shell
mkdir functional_tests
touch functional_tests/__init__.py
```

然后要移动功能测试，把独立的 `functional_tests.py` 文件移到 `functional_tests` 应用中，并把它重命名为 tests.py。使用 `git mv` 命令完成这个操作，让 Git 知道文件移动了。

```shell
git mv functional_tests.py functional_tests/tests.py
git status # 显示文件重命名为 functional_tests/tests.py，而且新增了 __init__.py
```

现在，运行功能测试不执行 `python functional_tests.py`，而是使用 `python manage.py test functional_tests` 命令。

> 功能测试可以和 lists 应用测试混在一起，不过作者更倾向于把两种测试分开，因为功能测试检测的功能往往存在不同应用中。功能测试以用户的视角看待事物，而用户并不关心你如何把网站分成不同的应用。

接下来编辑 `functional_tests/tests.py`，修改 `NewVisitorTest` 类，让它使用 LiveServerTestCase：

```python
from django.test import LiveServerTestCase
from selenium import webdriver
from selenium.webdriver.common.keys import keys

class NewVisitorTest(LiveServerTestCase):
    def setUp(self):
        [...]
```

继续往下修改。访问网站时，不用硬编码的本地地址（localhost:8000），可以使用 LiveServerTestCase 提供的 `live_server_url` 属性：

```python
def test_can_start_a_list_and_retrieve_it_later(self):
        # Y 访问在线待办事项应用的首页
        # self.browser.get("http://localhost:8000") # 不用硬编码了
        self.browser.get(self.live_server_url)
```

还可以删除文件末尾的 `if __name__ == "__main__"` 代码块，因为之后都使用 Django 的测试运行程序运行功能测试。

功能测试和重构前一样，能运行到 self.fail。如果再次运行测试，你会发现，之前的测试不再遗留待办事项了，因为功能测试运行完之后把它们清理掉了。

提交这次小改动：

```shell
git status # 重命名并修改了 functional_tests.py， 新增了 __init__.py
git add functional_tests
git diff --staged -M
git commit # 提交消息举例： "make functional_tests an app, use LiveServerTestCase"
```

git diff 命令中的 -M 标志很有用，意思是“检测移动”，所以 git 会注意到 `functional_tests.py` 和 `functional_tests/tests.py` 是同一个文件，显示更合理的差异。

#### 只运行单元测试

现在，如果执行 `python manage.py test` 命令，Django 会运行功能测试和单元测试：`python manage.py test`

如果只想运行单元测试，可以指定只运行 lists 应用中的测试：`python manage.py test lists`