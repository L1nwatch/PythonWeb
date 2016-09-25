## 附录 D 测试数据库迁移

`Django-migrations` 及前身 South 已经出现好多年了，所以一般没必要测试数据库迁移。但有时我们会使用一种危险的迁移，即引入新的数据完整性越苏。

在大型项目中，如果有敏感数据，在生产数据中执行迁移之前，你可能想先在一个安全的环境中测试，增加一些自信。

测试迁移的另一个常见原因是测速——执行迁移时经常要把网站下线，而且如果数据集比较大，用时并不短。所以最好提前知道迁移要执行多长时间。

### D.1 尝试部署到过渡服务器

数据库中某些现有的数据违反了完整性越苏条件，所以当尝试应用约束条件时，数据库表达了不满。

为了处理这种问题，需要执行“数据迁移”。首先，要在本地搭建一个测试环境。

### D.2 在本地执行一个用于测试的迁移

使用线上数据库的副本测试迁移。

> 测试时使用真实数据一定要小心。例如，数据中可能有客户的真实电子邮件地址。

#### D.2.1 输入有问题的数据

在线上网站中新建一个清单，输入一些重复的待办事项

#### D.2.2 从线上网站中复制测试数据

从线上网站中复制数据库：

```shell
scp watch@watch0.top /home/watch/sites/watch0.top/database/db.sqlite3 .
mv ../database/db.sqlite3 ../database/db.sqlite3.bak
mv db.sqlite3 ../database/db.sqlite3
```

#### D.2.3 确认的确有问题

现在，本地还有一个未执行迁移的数据库，而且数据库中有一些问题数据。如果尝试执行 `migrate` 命令，会看到错误。

### D.3 插入一个数据迁移

[数据迁移](https://docs.djangoproject.com/en/dev/topics/migrations/#data-migrations)是一种特殊的迁移，目的是修改数据库中的数据，而不是变更模式。应用完整性约束之前，先要执行一次数据迁移，把重复数据删除。具体方法如下：

```shell
git rm lists/migrations/0005_list_item_unique_together.py
python3 manage.py makemigrations lists --empty
mv lists/migrations/0005_ lists/migrations/0005_remove_duplicates.py*
```

数据迁移的详情参阅 [Django 文档](https://docs.djangoproject.com/en/dev/topics/migrations/#data-migrations)。下面是修改现有数据的方法：

```python
# lists/migrations/0005_remove_duplicates.py
# encoding: utf8
from django.db import models, migrations

def find_dupes(apps, schema_editor):
    List = apps.get_model("lists", "List")
    for list_ in List.objects.all():
        items = list_.item_set.all()
        texts = set()
        for ix, item in enumerate(items):
            if item.text in texts:
                item.text = "{} ({})".format(item.text, ix)
                item.save()
            texts.add(item.text)
            
class Migration(migrations.Migration):
    dependencies = [
      ("lists", "0004_item_list")
    ]
    
    operations = [
        migrations.RubPython(find_dupes)
    ]
```

#### 重新创建以前的迁移

使用 `makemigrations` 重新创建以前的迁移，确保这是第 6 个迁移，而且还明确依赖于 0005，即那个数据迁移。

### D.4 一起测试这两个迁移

现在可以在线上数据中测试了：

```shel
cd deploy_tools
fab deploy:host=watch@watch0.top
[...]
```

还要重启服务器中的 Gunicorn 服务：

`sudo restart gunicorn-watch0.top`

然后可以在过渡网站中运行功能测试。

### D.5 小结

这个练习的主要目的是编写一个数据迁移，在一些真实的数据中测试。当然，这只是测试迁移的千万种方式之一。你还可以编写自动化测试，比较运行迁移前后数据库中的内容，确认数据还在。也可以为数据迁移中的辅助函数单独编写单元测试。你可以再多花点时间统计迁移所用的时间，然后实验多种提速的方法，例如，把迁移的步骤分得更细或更笼统。

但这种需求很少见。根据作者的经验，使用的迁移，99% 都不需要测试。

> #### 关于测试数据库迁移
>
> * 小心引入约束的迁移
>   * 99% 的迁移都没问题，但是如果迁移为现有的列引入了新的约束条件，一定要小心。
> * 测试迁移的执行速度
>   * 一旦项目变大，就应该考虑测试迁移所用的时间。执行数据库迁移时往往要下线网站，因为修改模式可能要锁定数据表（取决于使用的数据库种类），直到操作完成为止。所以最好在过渡网站中测试迁移要用多长时间。
> * 使用生产数据的副本时要格外小心
>   * 为了测试迁移，要在过渡网站的数据库中填充与生产数据等量的数据。如果直接转储生产数据库导入过渡网站的数据库中，一定要十分小心，因为生产数据中包含真实客户的详细信息。