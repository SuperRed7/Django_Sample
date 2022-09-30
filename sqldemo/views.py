# Create your views here.
import json
import six
from django.shortcuts import render
from django.http import HttpResponse
from sqlalchemy import create_engine
import pandas as pd
import numpy as np
from io import BytesIO as IO
from sqldemo.charts import echarts_stackbar
import datetime
from django.views.decorators.cache import cache_page
from django.contrib.auth.decorators import login_required

ENGINE = create_engine('postgresql://postgres:123456@localhost/django_sample')
DBTABLE = 'sqldemo_data'

# 该字典key为前端准备显示的所有多选字段名, value为数据库对应的字段名
D_MULTI_SELECT = {
    '商品名|PRODUCT': 'product',
    'TC I': 'TC I',
    'TC II': 'TC II',
    'TC III': 'TC III',
    'TC IV': 'TC IV',
    '通用名|MOLECULE': 'molecule',
    '包装|PACKAGE': 'package',
    '生产企业|CORPORATION': 'corporation',
    '企业类型': 'manuf_type',
    '剂型': 'formulation',
    '剂量': 'strength'
}
D_TRANS = {
    'MAT': '滚动年',
    'QTR': '季度',
    'Value': '金额',
    'Volume': '盒数',
    'Volume (Counting Unit)': '最小制剂单位数',
    '滚动年': 'MAT',
    '季度': 'QTR',
    '金额': 'Value',
    '盒数': 'Volume',
    '最小制剂单位数': 'Volume (Counting Unit)'
}


# # 拼接SQL
# def sqlparse(period, unit, filter_sql=None):
#     sql_data = """
#     select
#         "TC I",
#         "TC II",
#         "TC III",
#         "TC IV",
#         "molecule",
#         "product",
#         "package",
#         "corporation",
#         "manuf_type",
#         "formulation",
#         "strength",
#         "unit",
#         "PERIOD",
#         "amount"::numeric(18,2) as "amount",
#         "DATE"::date as "DATE"
#     from
# 	    %s
#     where
# 	    "PERIOD" = '%s'
# 	    and "unit" = '%s'
#     """ \
#                % (DBTABLE, period, unit)  # 必选的两个筛选字段
#     if filter_sql is not None:
#         sql_data = "%s And %s" % (sql_data, filter_sql)  # 其他可选的筛选字段,如有则以And连接自定义字符串
#     return sql_data


# 生成整体市场的规模、增长率和CAGR(年复合增长率)
def get_kpi(df_data):
    # 按列求和为市场总值的Series
    market_total = df_data.sum(axis=1)
    # 最后一行（最后一个DATE）就是最新的市场规模
    market_size = market_total.iloc[-1]
    # 市场按列求和,倒数第5行（倒数第5个DATE）就是同比的市场规模,可以用来求同比增长率
    market_gr = market_total.iloc[-1] / market_total.iloc[-5] - 1
    # 因为数据第一年是四年前的同期季度,时间序列收尾相除后开四次方根可得到年复合增长率
    market_cagr = (market_total.iloc[-1] / market_total.iloc[0]) ** (0.25) - 1
    if market_size == np.inf or market_size == -np.inf:
        market_size = "N/A"
    if market_gr == np.inf or market_gr == -np.inf:
        market_gr = "N/A"
    if market_cagr == np.inf or market_cagr == -np.inf:
        market_cagr = "N/A"

    return {
        "market_size": market_size,
        "market_gr": market_gr,
        "market_cagr": market_cagr,
    }
    # return [market_size, "{0:.1%}".format(market_gr), "{0:.1%}".format(market_cagr)]


# 生成更复杂的结果
def ptable(df_data):
    # 份额
    df_share = df_data.transform(lambda x: x / x.sum(), axis=1)

    # 同比增长率,要考虑分子为0的问题
    df_gr = df_data.pct_change(periods=4)
    df_gr.dropna(how='all', inplace=True)
    df_gr.replace([np.inf, -np.inf], np.nan, inplace=True)

    # 最新滚动年绝对值表现及同比净增长
    df_latest = df_data.iloc[-1, :]
    df_latest_diff = df_data.iloc[-1, :] - df_data.iloc[-5, :]

    # 最新滚动年份额表现及同比份额净增长
    df_share_latest = df_share.iloc[-1, :]
    df_share_latest_diff = df_share.iloc[-1, :] - df_share.iloc[-5, :]

    # 进阶指标EI,衡量与市场增速的对比,高于100则为跑赢大盘
    df_gr_latest = df_gr.iloc[-1, :]
    df_total_gr_latest = df_data.sum(axis=1).iloc[-1] / df_data.sum(axis=1).iloc[-5] - 1
    df_ei_latest = (df_gr_latest + 1) / (df_total_gr_latest + 1) * 100

    df_combined = pd.concat(
        [df_latest, df_latest_diff, df_share_latest, df_share_latest_diff, df_gr_latest, df_ei_latest], axis=1)
    df_combined.columns = ['最新滚动年金额',
                           '净增长',
                           '份额',
                           '份额同比变化',
                           '同比增长率',
                           'EI']

    return df_combined


@login_required
@cache_page(60 * 60 * 24 * 30)
def search(request, column, kw):
    # print('KW:', kw)
    # 最简单的单一字符串like,返回不重复的前10个结果
    # sql_1 = "select distinct \"" + column + "\" from " + DBTABLE + " where \"" + column + "\" like " + "'%%" + kw + "%%'" + " order by \"" + column + "\" desc limit 10"
    sql_1 = "select distinct \"%s\" from %s where \"%s\" like '%%%%%s%%%%' order by \"%s\" desc limit 10" % (
        column, DBTABLE, column, kw, column)
    # print(sql_1)
    try:
        df = pd.read_sql_query(sql_1, ENGINE)
        # print(df)
        list_1 = df.values.flatten().tolist()
        # print(list_1)
        results_list = []
        for element in list_1:
            option_dict = {'name': element,
                           'value': element,
                           }
            results_list.append(option_dict)
        res = {
            "success": True,
            "results": results_list,
            "code": 200,
        }
    except Exception as e:
        res = {
            "success": False,
            "errMsg": e,
            "code": 0,
        }
    # print(res)
    # 返回结果必须是json格式
    return HttpResponse(json.dumps(res, ensure_ascii=False), content_type="application/json charset=utf-8")


def sqlparse(context):
    print('关键词信息:', context)
    sql = """
        select
            "TC I",
            "TC II",
            "TC III",
            "TC IV",
            "molecule",
            "product",
            "package",
            "corporation",
            "manuf_type",
            "formulation",
            "strength",
            "unit",
            "PERIOD",
            "amount"::numeric(18,2) as "amount",
            "DATE"::date as "DATE"
        from
    	    %s
        where
    	    "PERIOD" = '%s'
    	    and "unit" = '%s'
    """ \
          % (DBTABLE, context['PERIOD_select'][0], context['UNIT_select'][0])  # 必选的两个筛选字段

    # 下面循环处理多选部分
    for k, v in context.items():
        if k not in ['csrfmiddlewaretoken', 'DIMENSION_select', 'PERIOD_select', 'UNIT_select']:
            # field_name = k[:-9]  # 字段名
            if k[-2:] == '[]':
                field_name = k[:-9]  # 如果键以[]结尾，删除_select[]取原字段名
            else:
                field_name = k[:-7]  # 如果键不以[]结尾，删除_select取原字段名
            selected = v  # 选择项
            sql = sql_extent(sql, field_name, selected)  # 未来可以通过进一步拼接字符串动态扩展sql语句
    # print('拼接的SQL语句:', sql)
    return sql


def sql_extent(sql, field_name, selected, operator=" AND "):
    if selected is not None:
        statement = ''
        for data in selected:
            statement = statement + "'" + data + "', "
        # print('statement1:', statement)
        statement = statement[:-2]
        # print('statement2:', statement)
        if statement != '':
            sql = sql + operator + "\"" + field_name + "\"" + " in (" + statement + ")"
    return sql


def build_formatters_by_col(df):
    format_abs = lambda x: '{:,.0f}'.format(x)
    format_share = lambda x: '{:.1%}'.format(x)
    format_gr = lambda x: '{:.1%}'.format(x)
    format_currency = lambda x: '¥{:,.0f}'.format(x)
    d = {}
    for column in df.columns:
        if '份额' in column or '贡献' in column:
            d[column] = format_share
        elif '价格' in column or '单价' in column or '金额' in column:
            d[column] = format_currency
        elif '同比增长' in column or '增长率' in column or 'CAGR' in column or '同比变化' in column:
            d[column] = format_gr
        else:
            d[column] = format_abs
    return d


def get_df(form_dict, is_pivoted=True):
    sql = sqlparse(form_dict)  # sql拼接
    df = pd.read_sql_query(sql, ENGINE)  # 将sql语句结果读取至Pandas Dataframe
    # dimension_selected = form_dict['DIMENSION_select'][0]
    # #  如果字段名有空格为了SQL语句在预设字典中加了中括号的,这里要去除
    # if dimension_selected[0] == '[':
    #     column = dimension_selected[1:][:-1]
    # else:
    #     column = dimension_selected
    if is_pivoted is True:
        dimension_selected = form_dict['DIMENSION_select'][0]
        if dimension_selected[0] == '[':

            column = dimension_selected[1:][:-1]
        else:
            column = dimension_selected

        pivoted = pd.pivot_table(df,
                                 values='amount',  # 数据透视汇总值为AMOUNT字段,一般保持不变
                                 index='DATE',  # 数据透视行为DATE字段,一般保持不变
                                 columns=column,  # 数据透视列为前端选择的分析维度
                                 aggfunc=np.sum)  # 数据透视汇总方式为求和,一般保持不变
        # print(pivoted)
        if pivoted.empty is False:
            pivoted.sort_values(by=pivoted.index[-1], axis=1, ascending=False, inplace=True)  # 结果按照最后一个DATE表现排序
        return pivoted
    else:
        return df


@login_required
@cache_page(60 * 60 * 24 * 30)  # 缓存30天
def query(request):
    form_dict = dict(six.iterlists(request.GET))
    pivoted = get_df(form_dict)

    # KPI
    kpi = get_kpi(pivoted)

    table = ptable(pivoted)
    table = table.to_html(
        formatters=build_formatters_by_col(table),
        classes='ui selectable celled table',
        table_id='ptable'
    )
    # Pyecharts交互图表
    bar_total_trend = json.loads(prepare_chart(pivoted, 'bar_total_trend', form_dict))

    context = {
        "market_size": kpi["market_size"],  # 总滚动年金额
        "market_gr": kpi["market_gr"],  # 同比增长
        "market_cagr": kpi["market_cagr"],  # 4年CAGR
        # 'ptable': ptable(pivoted).to_html()
        'ptable': table,
        'bar_total_trend': bar_total_trend,
    }

    return HttpResponse(json.dumps(context, ensure_ascii=False),
                        content_type="application/json charset=utf-8")  # 返回结果必须是json格式


@login_required
@cache_page(60 * 60 * 24 * 30)
def export(request, type):
    form_dict = dict(six.iterlists(request.GET))

    if type == 'pivoted':
        df = get_df(form_dict)  # 透视后的数据
    elif type == 'raw':
        df = get_df(form_dict, is_pivoted=False)  # 原始数

    excel_file = IO()

    xlwriter = pd.ExcelWriter(excel_file, engine='xlsxwriter')

    df.to_excel(xlwriter, 'data', index=True)

    xlwriter.save()
    xlwriter.close()

    excel_file.seek(0)

    # 设置浏览器mime类型
    response = HttpResponse(excel_file.read(),
                            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

    # 设置文件名
    now = datetime.datetime.now().strftime("%Y%m%d%H%M%S")  # 当前精确时间不会重复，适合用来命名默认导出文件
    response['Content-Disposition'] = 'attachment; filename=' + now + '.xlsx'
    return response


def prepare_chart(df,  # 输入经过pivoted方法透视过的df,不是原始df
                  chart_type,  # 图表类型字符串,人为设置,根据图表类型不同做不同的Pandas数据处理,及生成不同的Pyechart对象
                  form_dict,  # 前端表单字典,用来获得一些变量作为图表的标签如单位
                  ):
    label = D_TRANS[form_dict['PERIOD_select'][0]] + ' ' + D_TRANS[form_dict['UNIT_select'][0]]

    if chart_type == 'bar_total_trend':
        df_abs = df.sum(axis=1)  # Pandas列汇总,返回一个N行1列的series,每行是一个date的市场综合
        # print(df_abs.index, type(df_abs.index))
        df_abs.index = pd.to_datetime(df_abs.index).strftime("%Y-%m")  # 行索引日期数据变成2020-06的形式
        df_abs = df_abs.to_frame()  # series转换成df
        df_abs.columns = [label]  # 用一些设置变量为系列命名,准备作为图表标签
        df_gr = df_abs.pct_change(periods=4)  # 获取同比增长率
        df_gr.dropna(how='all', inplace=True)  # 删除没有同比增长率的行,也就是时间序列数据的最前面几行,他们没有同比
        df_gr.replace([np.inf, -np.inf, np.nan], '-', inplace=True)  # 所有分母为0或其他情况导致的inf和nan都转换为'-'
        chart = echarts_stackbar(df=df_abs,
                                 df_gr=df_gr
                                 )  # 调用stackbar方法生成Pyecharts图表对象
        return chart.dump_options()  # 用json格式返回Pyecharts图表对象的全局设置
    else:
        return None


@login_required
def index(request):
    # # 标准sql语句,此处为测试返回数据库中sqldemo_data表的数据条目n,之后可以用python处理字符串的方式动态扩展
    # sql = "select count(*) as 总数 from sqldemo_data;"
    # # 将sql语句结果读取至Pandas Dataframe
    # df = pd.read_sql_query(sql, ENGINE)
    # # # 渲染,这里暂时渲染为最简单的HttpResponse,以后可以扩展
    # # return HttpResponse(df.to_html())
    # context = {'data': df}
    # return render(request, 'sqldemo/display.html', context)

    # # 读取ARB市场的滚动年销售额数据
    # sql_1 = sqlparse(
    #     'MAT',
    #     'Value',
    #     """
    #         "TC III" = 'C09C ANGIOTENS-II ANTAG, PLAIN|血管紧张素II拮抗剂,单一用药'
    #     """
    # )
    # df_1 = pd.read_sql_query(sql_1, ENGINE)
    # # print('原数据:', df_1)
    # # pivoted_table()快速创建透视数据获取结果
    # df_2 = pd.pivot_table(df_1,
    #                       values='amount',  # 数据透视汇总值为AMOUNT字段,一般保持不变
    #                       index='DATE',  # 数据透视行为DATE字段,一般保持不变
    #                       columns='molecule',  # 数据透视列为MOLECULE字段,该字段以后应跟随分析需要动态传参
    #                       aggfunc=np.sum)  # 数据透视汇总方式为求和,一般保持不变
    # # print('透视数据:', df_2)
    # # 结果按照最后一个DATE表现排序
    # if df_2.empty is False:
    #     df_2.sort_values(by=df_2.index[-1], axis=1, ascending=False, inplace=True)
    # # KPI
    # kpi_1 = get_kpi(df_2)
    # # print('定义市场当前表现:', kpi_1)
    # # print('竞争现状:', ptable(df_2))

    mselect_dict = {}
    for key, value in D_MULTI_SELECT.items():
        mselect_dict[key] = {}
        mselect_dict[key]['select'] = value
        # 以后可以后端通过列表为每个多选控件传递备选项
        # mselect_dict[key]['options'] = option_list
    # print(mselect_dict)

    # context = {
    #     "market_size": kpi_1["market_size"],
    #     "market_gr": kpi_1["market_gr"],
    #     "market_cagr": kpi_1["market_cagr"],
    #     'ptable': ptable(df_2).to_html(),
    #     'mselect_dict': mselect_dict,
    # }
    context = {
        'mselect_dict': mselect_dict
    }
    return render(request, 'sqldemo/display.html', context)
