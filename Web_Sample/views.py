from django.shortcuts import render, get_object_or_404

# Create your views here.

from django.http import HttpResponse, HttpResponseRedirect
from django.template import loader
from django.urls import reverse
from django.utils import timezone
from django.views import generic

from Web_Sample.models import Question, Choice


# def index(request):
#     latest_question_list = Question.objects.order_by('-pub_date')[:5]
#     context = {
#         'latest_question_list': latest_question_list,
#     }
#     # template = loader.get_template('Web_Sample/index.html')
#     # return HttpResponse(template.render(context, request))
#     # 快捷函数render():载入模板,填充上下文,再返回由它生成的HttpResponse对象
#     # 注意到,我们不再需要导入loader和HttpResponse
#     return render(request, 'Web_Sample/index.html', context)
#
#
# def detail(request, question_id):
#     # try:
#     #     question = Question.objects.get(pk=question_id)
#     # except:
#     #     raise HttpResponse("Question does not exist")
#     # return render(request, 'Web_Sample/detail.html', {'question': question})
#     # 快捷函数get_object_or_404():获取一个对象,如果不存在就抛出Http404错误
#     question = get_object_or_404(Question, pk=question_id)
#     return render(request, 'Web_Sample/detail.html', {'question': question})
#
#
# def results(request, question_id):
#     question = get_object_or_404(Question, pk=question_id)
#     return render(request, 'Web_Sample/results.html', {'question': question})

# 使用通用视图:2.改良视图
# 使用两个通用视图:ListView和DetailView
# 这两个视图分别抽象"显示一个对象列表"和"显示一个特定类型对象的详细信息页面"这两种概念
class IndexView(generic.ListView):
    template_name = 'Web_Sample/index.html'
    context_object_name = 'latest_question_list'

    # def get_queryset(self):
    #     """Return the last five published questions."""
    #     return Question.objects.order_by('-pub_date')[:5]

    def get_queryset(self):
        """
        Return the last five published questions (not including those set to be
        published in the future).
        """
        return Question.objects.filter(
            pub_date__lte=timezone.now()
        ).order_by('-pub_date')[:5]
        # return Question.objects.filter(pub_date__date=datetime.date.today())
        # return Question.objects.filter(question_text__contains='今天')

class DetailView(generic.DetailView):
    model = Question
    template_name = 'Web_Sample/detail.html'

    def get_queryset(self):
        """
        Excludes any questions that aren't published yet.
        """
        return Question.objects.filter(pub_date__lte=timezone.now())


class ResultsView(generic.DetailView):
    model = Question
    template_name = 'Web_Sample/results.html'

    def get_queryset(self):
        """
        Excludes any questions that aren't published yet.
        """
        return Question.objects.filter(pub_date__lte=timezone.now())


def vote(request, question_id):
    question = get_object_or_404(Question, pk=question_id)
    try:
        selected_choice = question.choice_set.get(pk=request.POST['choice'])
    except (KeyError, Choice.DoesNotExist):
        # Redisplay the question voting form.
        return render(request, 'Web_Sample/detail.html', {
            'question': question,
            'error_message': "You didn't select a choice.",
        })
    else:
        selected_choice.votes += 1
        selected_choice.save()
        # Always return an HttpResponseRedirect after successfully dealing
        # with POST data. This prevents data from being posted twice if a
        # user hits the Back button.
        return HttpResponseRedirect(reverse('Web_Sample:results', args=(question.id,)))
