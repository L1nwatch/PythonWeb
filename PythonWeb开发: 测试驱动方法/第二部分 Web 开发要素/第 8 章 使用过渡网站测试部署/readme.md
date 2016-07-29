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
import sys
[...]

class NewVisitorTest(StaticLiveServerCase):
    @classmethod
    def setUp(cls): # setUpClass 方法和 setUp 类似，也由 unittest 提供，但是它用于设定整个类的测试背景。也就是说，setUpClass 方法只会执行一次，而不会在每个测试方法运行前都执行。LiveServerTestCase 和 StaticLiveServerCase 一般都在这个方法中启动测试服务器。
        for arg in sys.argv: # 在命令行中查找参数 liveserver(从 sys.argv 中获取)
            if "liveserver" in arg:
                # 如果找到了，就让测试类跳过常规的 setUpClass 方法，把过渡服务器的 URL 赋值给 server_url 变量
                cls.server_url = "http://" + arg.split("=")[1]
                return
        super().setUpClass()
        cls.server_url = cls.live_server_url
        
    @classmethod
    def tearDown(cls):
        if cls.server_url == cls.live_server_url:
            super().tearDownClass()
            
    def setUp(self):
        [...]
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
```

运行功能测试，确保上述改动没有破坏现有功能。

然后指定过渡服务器的 URL 再运行试试，使用的过渡服务器地址是 `superlists-staging.ottg.eu`。

可以看到，和预期一样，两个测试都失败了，因为还没架设过渡网站。看起来功能测试的测试对象是正确的，所以做一次提交吧。

```shell
git diff
git commit -am "Hack FT runner to be able to test staging"
```

