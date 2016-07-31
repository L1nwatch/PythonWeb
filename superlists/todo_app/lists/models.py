from django.db import models


class List(models.Model):
    pass


# Create your models here.
class Item(models.Model):
    text = models.TextField(default="")
    list_attr = models.ForeignKey(List, default=None)  # List 的声明得在该类上方
