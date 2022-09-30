from django.urls import path

from . import views

# 这句是必须的,和之后所有的URL语句有关
app_name = 'sqldemo'
urlpatterns = [
    path(r'index', views.index, name='index'),
    path(r'search/<str:column>/<str:kw>', views.search, name='search'),
    path(r'query', views.query, name='query'),
    path(r'export/<str:type>', views.export, name='export'),
]
