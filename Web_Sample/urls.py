from django.urls import path

from . import views

app_name = 'Web_Sample'
urlpatterns = [
    # path('', views.index, name='index'),
    # path('<int:question_id>/', views.detail, name='detail'),
    # path('<int:question_id>/results/', views.results, name='results'),

    # 使用通用视图:1.转换URLconf
    # 路径字符串中匹配模式的名称已经由<question_id>改为<pk>
    path('', views.IndexView.as_view(), name='index'),
    path('<int:pk>/', views.DetailView.as_view(), name='detail'),
    path('<int:pk>/results/', views.ResultsView.as_view(), name='results'),

    # ex: /Web_Sample/1/vote/
    path('<int:question_id>/vote/', views.vote, name='vote'),
]
