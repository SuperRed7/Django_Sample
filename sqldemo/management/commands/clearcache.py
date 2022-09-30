from django.core.cache import cache
from django.core.management import BaseCommand


# 可在终端手动输入命令清除缓存
# python manage.py clearcache
class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        cache.clear()
        self.stdout.write('缓存已清除\n')
