import datetime
import json
import os
import uuid

import requests
import tqdm


def get_cal_head(name: str = '日历名称'):
    """
    获取日历开始的头
    :param name: 日历名称
    :return: 日历开始的头
    """
    res = f'''BEGIN:VCALENDAR
VERSION:2.0
X-WR-CALNAME:{name}
'''
    return res


def get_vevent(summary: str = '标题', location: str = '位置',
               start_date: str = '20231008T090000', end_date: str = '20231008T090000',
               description: str = '备注', url: str = 'url'):
    """
    获取日历的一个事件
    :param summary: 标题
    :param location: 位置
    :param start_date: 20231008T090000
    :param end_date: 20231008T090000
    :param description: 备注
    :param url: url
    :return: 日历的一个事件
    """
    summary = summary.replace('\n', ' ')
    location = location.replace('\n', ' ')
    start_date = start_date.replace('\n', ' ')
    end_date = end_date.replace('\n', ' ')
    description = description.replace('\n', ' ')
    url = url.replace('\n', ' ')
    res = f'''BEGIN:VEVENT
CREATED:{datetime.datetime.now().strftime("%Y%m%dT%H%M%SZ")}
UID:{str(uuid.uuid4()).upper()}
SUMMARY:{summary}
LOCATION:{location}
DTSTART;TZID=Asia/Shanghai:{start_date}
DTEND;TZID=Asia/Shanghai:{end_date}
DESCRIPTION:{description}
URL;VALUE=URI:{url}
END:VEVENT
'''
    return res


def get_html_data(url='', cookie='JSESSIONID='):
    """
    获取url内容
    :param url: url
    :param cookie: 登陆后的凭证
    :return: 页面
    """
    t_url = url
    t_header = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;'
                  'q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Encoding': 'gzip, deflate',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
        'Cookie': cookie,
        'Dnt': '1',
        'Host': 'xinxi.yjsy.wmu.edu.cn',
        'Pragma': 'no-cache',
        'Referer': t_url,
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/111.0.0.0 Safari/537.36 Edg/111.0.1661.41'

    }
    t_resp = requests.get(url=t_url, headers=t_header)
    if t_resp.status_code == 200:
        return t_resp.text
    return ''


def get_kb_data(xn='2023', xj='11', zc='3', cookie='JSESSIONID='):
    """
    获取课程信息的界面
    :param xn: 年份
    :param xj: 学期
    :param zc: 周次
    :param cookie: 登陆后的凭证
    :return: 页面
    """
    t_url = f'http://xinxi.yjsy.wmu.edu.cn/py/page/student/grkcb.htm?xn={xn}&xj={xj}&zc={zc}'
    return get_html_data(url=t_url, cookie=cookie)


def get_k_json_list(html_str):
    """
    从html中提取课程信息
    :param html_str: 课程页面
    :return: json格式的课程列表，可以为空[]
    """
    res = []
    t_time_zou = html_str.split('<select name="zc" id="zc" class="w80 chzn-select change">')[1]
    t_time_zou = t_time_zou.replace(' ', '').split('selected="selected">')[1].split('</option>')[0]

    kb_table = html_str.split('<table class="table table-bordered table-course" id="">')[1].split('</table>')[0]
    kb_table = kb_table.split('<tr>')[2:]
    xq_map = {0: '星期一', 1: '星期二', 2: '星期三', 3: '星期四', 4: '星期五', 5: '星期六', 6: '星期七'}
    for jie, d in enumerate(kb_table):
        xq_list = d.split('<td ')[3:]
        for xq, xq_d in enumerate(xq_list):
            t_1 = xq_d.split('<a  class="c666"')[1:]
            for i in t_1:
                i = '<a  class="c666"' + i
                t_href = i.split('href="')[1].split('"')[0]
                t_class_name = i.split('<strong class="f14">')[1].split('</strong>')[0].strip()
                t_other = i.split('&nbsp;')[1].split('</a>')[0]
                t_other_list = t_other.split('<br />')
                t_time_jie = t_other_list[2].replace('第', '').replace('节', '').strip().split(' -- ')
                t_time_jie_list = []
                for p in range(int(t_time_jie[0]), int(t_time_jie[1]) + 1):
                    t_time_jie_list.append(p)
                t_teacher_name = t_other_list[3].strip()
                t_location = t_other_list[4].strip()
                t_class = {
                    '课程名称': t_class_name,
                    '课程周': t_time_zou,
                    '星期': xq_map[xq],
                    '课程节': t_time_jie_list,
                    '老师': t_teacher_name,
                    '位置': t_location,
                    '课程信息页面': f'http://xinxi.yjsy.wmu.edu.cn{t_href}',
                }
                res.append(t_class)

    return res


def get_student_xh(data: str):
    try:
        return data.split('<span>学号</span><span class="space">|</span><span class="text">')[1].split('</span>')[0]
    except:
        return ''


def get_time(xj, kc_zou, kc_xq, kc_jie_list, is_start=True):
    # xj:11, '课程周': '第3周', '星期': '星期一', '课程节': [14, 15],
    # 2023-09-26
    xq_map = {'星期一': 1, '星期二': 2, '星期三': 3, '星期四': 4, '星期五': 5, '星期六': 6, '星期七': 7}
    day_num = (int(kc_zou.replace('第', '').replace('周', '')) - 1) * 7 + xq_map[kc_xq]

    # 11学期第一周星期0：2023-09-10
    str_time = '2023-09-10'
    start_time = datetime.datetime.strptime(str_time, "%Y-%m-%d")
    after_time = start_time + datetime.timedelta(days=day_num)

    day_str = str(after_time).split(' ')[0].replace('-', '')
    # 20230913

    # 20211102T084000Z
    time_dict = {'1': ['0800', '0840'],
                 '2': ['0845', '0925'],
                 '3': ['0940', '1020'],
                 '4': ['1025', '1105'],
                 '5': ['1110', '1150'],
                 '6': ['1155', '1235'],
                 '7': ['1240', '1320'],
                 '8': ['1330', '1410'],
                 '9': ['1415', '1455'],
                 '10': ['1500', '1540'],
                 '11': ['1545', '1625'],
                 '12': ['1630', '1710'],
                 '13': ['1715', '1755'],
                 '14': ['1820', '1900'],
                 '15': ['1905', '1945'],
                 '16': ['1950', '2030'],
                 '17': ['2035', '2115']}
    if is_start:
        res = f'{day_str}T{time_dict[str(kc_jie_list[0])][0]}00'
    else:
        res = f'{day_str}T{time_dict[str(kc_jie_list[-1])][1]}00'
    return res


def get_ics_str(all_class_list, xn='2023', xj='11', xh=''):
    get_cal_head(name=f'{xh}的课表')
    res = get_cal_head(name=f'{xh}的课表')
    res += '\n'
    for i, d in enumerate(all_class_list):
        res += get_vevent(summary=d['课程名称'], location=d['位置'],
                          start_date=get_time('', d['课程周'], d['星期'], d['课程节'], True),
                          end_date=get_time('', d['课程周'], d['星期'], d['课程节'], False),
                          description=d['课程名称'], url='url')
        res += '\n'
    # res += f'''
    # BEGIN:VEVENT
    # UID:wmu_{xn}_{xj}_{i}
    # DTSTART;TZID=Asia/Shanghai:{get_time('', d['课程周'], d['星期'], d['课程节'], True)}
    # DTEND;TZID=Asia/Shanghai:{get_time('', d['课程周'], d['星期'], d['课程节'], False)}
    # SUMMARY:{d['课程名称']}
    # LOCATION:{d['位置']}
    # END:VEVENT
    # '''
    return res


def get_kb_ics(xn: str, xj: str, cookie: str):
    if os.path.exists("k") is False:
        os.mkdir("k")
    zc = [str(i) for i in range(1, 21)]
    for i in tqdm.tqdm(zc):
        t_html = get_kb_data(xn=xn, xj=xj, zc=i, cookie=cookie)
        with open(f'k/{i}.html', 'w', encoding='utf-8') as f:
            f.write(t_html)
    all_class_list = []
    for i in tqdm.tqdm(zc):
        with open(f'k/{i}.html', 'r', encoding='utf-8') as f:
            t_str = ''.join(f.readlines())
        t_json_list = get_k_json_list(t_str)
        all_class_list.extend(t_json_list)

    with open(f'k/1.html', 'r', encoding='utf-8') as f:
        t_str = ''.join(f.readlines())
    xh = get_student_xh(t_str)

    # 对课程页面去重，获取所有课程页面信息
    class_page = set()
    for i in all_class_list:
        # print(i)
        class_page.add(i['课程信息页面'] + '_' + i['课程名称'])
    class_page = list(class_page)
    for i in tqdm.tqdm(class_page):
        t_html = get_html_data(url=i.split('_')[0], cookie=cookie)
        with open(f'k/kc_{i.split("_")[1]}.html', 'w', encoding='utf-8') as f:
            f.write(t_html)
    with open('kc_location.json', 'r', encoding='utf-8') as f:
        kc_location = json.loads(''.join(f.readlines()))
    with open('kc_sutdent_map.json', 'r', encoding='utf-8') as f:
        kc_sutdent_map = json.loads(''.join(f.readlines()))

    print(all_class_list[0])
    for index, i in enumerate(all_class_list):
        if i['课程名称'] == '生物信息学':
            all_class_list[index]['位置'] = '钉钉'
        elif i['课程名称'] == '知识产权':
            all_class_list[index]['位置'] = '瓯江实验室7010'
        elif i['课程名称'] == '医学研究方法':
            all_class_list[index]['位置'] = '学院路校区综合楼401、402'
        elif i['课程名称'] == '现代生物医学工程概论':
            all_class_list[index]['位置'] = '茶山6A407'
        elif i['位置'] == '(场地详见学院通知)':
            temp_kc_location = '(场地详见学院通知)'
            # 根据课程名称去找kc_loaction
            for kc in kc_location:
                if kc['课程名称'] == i['课程名称']:
                    temp_kc_location = kc['校区、授课教室']
                    break
            # 再去确定一下学号有没有
            is_in_kc = False
            for kc in kc_sutdent_map:
                if kc['课程名称'] == i['课程名称']:
                    for student in kc['学生信息']:
                        if student['学号'] == xh:
                            is_in_kc = True
            if is_in_kc:
                all_class_list[index]['位置'] = temp_kc_location
        print('{: <10} {: <10} {: <10} {: <10}'.format(i['课程名称'], i['课程周'], i['星期'], str(i['课程节'])))
    print(len(all_class_list))

    with open(f'{xh}all_class_list.json', 'w', encoding='utf-8') as f:
        f.write(json.dumps(all_class_list, ensure_ascii=False, indent=4))
    with open(f'{xh}all_class_list.json', 'r', encoding='utf-8') as f:
        all_class_list = json.loads(''.join(f.readlines()))

    ics_str = get_ics_str(all_class_list, xn=xn, xj=xj, xh=xh)
    # print(ics_str)
    with open(f'kcb_{xh}.ics', 'w', encoding='utf-8') as f:
        f.write(ics_str)


if __name__ == '__main__':
    xn = '2023'
    xj = '11'
    # 登录网页获取cookie
    cookie = 'JSESSIONID=B8373CF0D292312CCE0D07D8F13D495F'
    get_kb_ics(xn=xn, xj=xj, cookie=cookie)
