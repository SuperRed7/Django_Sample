from django import template

register = template.Library()


@register.filter(name='percentage')
# 用AJAX异步加载的返回里调用的,没法应用django tag
def percentage(value, decimal):
    print(decimal)
    try:
        format_str = '{0:.' + str(decimal) + '%}'
        print(format_str.format(value))
        return format_str.format(value)
    except:
        return value
