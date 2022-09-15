from django.contrib import admin
from django.db import models
import datetime
from django.utils import timezone


# Create your models here.

# Question模型包括问题描述和发布时间
class Question(models.Model):
    question_text = models.CharField(max_length=200, verbose_name='问题描述')
    pub_date = models.DateTimeField(verbose_name='发布时间')

    def __str__(self):
        return self.question_text

    @admin.display(
        boolean=True,
        ordering='pub_date',
        description='是否近一日内发布?',
    )
    def was_published_recently(self):
        # return self.pub_date >= timezone.now() - datetime.timedelta(days=1)
        now = timezone.now()
        return now - datetime.timedelta(days=1) <= self.pub_date <= now

    class Meta:
        verbose_name = "问题"  # 表名改成中文名
        verbose_name_plural = verbose_name


# Choice模型有两个字段,选项描述和当前得票数
# 每个选项属于一个问题
class Choice(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, verbose_name='问题')
    choice_text = models.CharField(max_length=200, verbose_name='选项描述')
    votes = models.IntegerField(default=0, verbose_name='票数')

    def __str__(self):
        return self.choice_text

    class Meta:
        verbose_name = "选项"  # 表名改成中文名
        verbose_name_plural = verbose_name
