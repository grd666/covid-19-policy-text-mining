import requests
import time
import random
from pyquery import PyQuery as pq
import re

url = "https://mp.weixin.qq.com/cgi-bin/appmsg"

headers = {
    "Cookie": "appmsglist_action_3860793191=card; appmsglist_action_3933176794=card; pgv_pvi=9728731136; RK=QRicSPDncH; ptcz=1a041b69195b914f33c16fc384308256411c9a4550bbad8164d2deab0578fe4a; iip=0; tvfe_boss_uuid=774be0a5111a8eaa; uin_cookie=o0327236267; ied_qq=o0327236267; o_cookie=327236267; pac_uid=1_327236267; LW_uid=D1L672Y0E9i1A3S1k4b7L5V094; pgv_pvid=9300948330; Qs_lvt_323937=1630301438; Qs_pv_323937=2979582664850066000; LW_sid=W196d417I7A0X986V4Z8r5T0B3; ua_id=vGEJoGqheDeVMsxAAAAAAKHOzu5ApOxJqBCaRdlqajI=; wxuin=51765385463158; ariaDefaultTheme=undefined; mm_lang=zh_CN; uuid=4ce1a3f4254459d9a95a9c46e36acda8; rand_info=CAESIEy7IVx0srQ8WWJ+FYAnIB3w5Mg8T2DuyGQcbX6oxf/T; slave_bizuin=3933176794; data_bizuin=3933176794; bizuin=3933176794; data_ticket=65BadmqnSDmbMgVuA6uMqU9rOW2am2SD2A/O6tzjjjjCxsH77nj/zjihj9fDXx+M; slave_sid=M0dNMVdxT3VEczRIdGtwd0pvREFtQXdCbDBwNjVFYzd6RU1MV05IX0RhZ29jNXYydGlMdjZRQmtNcVFPeUVhVXZiWkx0YUlLMXNXdkhLTlFjNlRYaGtqa3MxcEZ5RXNJQWczR3JsdUFsX0VUX21rcFVkUnRzVXdrWFdSdGhTRUZnYTBLaTFoTXhxQk0yeGtm; slave_user=gh_d6ec6ba96280; xid=b43e40dbb6404f2c0027ab0e0e4221e9",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.54 Safari/537.36"
}

params = {
    "action": "list_ex",
    "begin": "0",
    "count": "5",
    "fakeid": "MzAwNjg3OTE4Ng==",
    "type": "9",
    "token": "1075930062",
    "lang": "zh_CN",
    "f": "json",
    "ajax": "1"
}

with open("app_msg_list.csv", "w", encoding='utf-8') as file:
    file.write("文章标识符aid,标题title,链接url\n")

with open("content_list", "w", encoding='utf-8') as file:
   file.write("title,content,ann_time,ann_department,category,measure\n")

#先要爬取公众号中各篇历史文章的url
#从第一篇疫情相关推送开始到爬取日期（2020-01-22到2022-05-06），共391页，每页5次推送（一次推送有1或者2篇文章，微信公众号平台中文章历史记录是按推送次数而不是文章篇数划分页数的）
i = 0
while i < 391:
    begin = i * 5
    params["begin"] = str(begin)

    # 随机暂停几秒，避免过快的请求导致被查到
    time.sleep(random.randint(1,5))
    response = requests.get(url, headers=headers, params = params, verify=False)

    # 出现微信限流, 暂停爬取
    if response.json()['base_resp']['ret'] == 200013:
        print("frequencey control, stop at {}".format(str(begin)))
        time.sleep(3600)
        continue
        
    msg = response.json()
    if "app_msg_list" in msg:
        for item in msg["app_msg_list"]:
            info = '"{}","{}","{}"'.format(str(item["aid"]), item['title'], item['link'])
            with open("app_msg_list.csv", "a", encoding='utf-8') as f:
                f.write(info+'\n')
        print(f"第{i+1}页爬取成功") 
    
    i+=1


# 开始正式爬取各篇文章的内容
with open("app_msg_list.csv","r",encoding="utf-8") as f:
    data = f.readlines()
n = len(data)
for i in range(n):
    mes = data[i].strip("\n").split(",")
    # url信息不全则跳过该条
    if len(mes)!=3:
        continue
    title, url = mes[1:3]
    if i>0:
        response = requests.get(eval(url), headers=headers)
        if response.status_code == 200:
            html = response.text
            # 本次爬取微信公众号文章各部分在HTML标签结构上基本无规律可循，故只能直接抽取标签中的Text,利用Text本身的特征进行相应字段抽取
            html = pq(html)
            text = html('#js_article').text() 
            
            # 首先判断是否是疫情相关文章，再判断能否截取有效文字、是否含有政策发布时间和机构（目前只实现了依赖发布时间的方式抽取机构，故有时间才有机构）
            if '疫情' in text or '新型冠状' in text: 
                content = re.findall(r'收录于合集(.*?)\n来源：', text, re.S)
                if len(content) > 0 :
                    ann_time = re.findall(r'\n[0-9]{4}年[0-9]{1,2}月[0-9]{1,2}日\n', text, re.S)
                    if len(ann_time) > 0:
                        ann_department = re.findall(r'\n.{0,30}\n[0-9]{4}年[0-9]{1,2}月[0-9]{1,2}日\n', text, re.S)
                        if len(ann_department) > 0:
                            ann_time = ann_time[-1].strip('\n').replace('年','/').replace('月','/').replace('日','')
                            ann_department = ann_department[-1].replace('\n','').split('2')[0]
                            content = content[0].replace('\n','').replace('\xa0','')

                            info = '{},"{}","{}","{}","",""'.format(title, content, ann_time, ann_department)
                            with open("content_list.csv", "a", encoding='utf-8') as f:
                                f.write(info+'\n')

# 如上爬取的文本仍有瑕疵，在标注政策分类和措施的时候顺便手动完善
# 共3297条公众号文章记录，疫情相关的有1417条，而程序最终抽取出的为588条，后续再通过标注时的人工筛选剩240条
# 这次抽到的城市张家口政府官网中信息极度缺少，故全部通过微信公众号“张家口发布”爬取