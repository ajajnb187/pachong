"""
设置类
想添加列名的话先在init函数中对应的字典中按照数字顺序添加字符串，再修改调用write_csv函数的入参
"""
import os
import csv
import sys
import time
import chardet
from datetime import datetime

import requests
from fake_useragent import UserAgent

class Settings:
    def __init__(self, main_instance):
        """参数设置"""
        # 自动爬取开关（True为开启，开启后请求失败的程序会接着异常时候的页数运行直到数据全部爬取）
        self.voluntarily = True
        # 主程序暂停开关（不可修改）
        self.suspend = False
        # 爬取最大页数设置
        self.max_page = 100
        # 请求超时时间
        self.timeout = 20
        # 详情页面超时时间
        self.timeout_detail = 15
        # 详情页面资源不足500等待时间
        self.timeout_detail_500 = 60
        # 详情页面资源不足500请求次数
        self.request_detail_500 = 0
        # 热门商圈页面请求失败等待时间
        self.timeout_wait = 2600

        # 主程序实例化对象
        self.main_instance = main_instance

        """请求参数设置"""
        self.url = "https://m.ctrip.com/restapi/soa2/18109/json/getAttractionList"
        self.cookies = {
            'UBT_VID': '1731476947273.a7b45HPTkTVR',
            'GUID': '09031076110042895602',
            'MKT_CKID': '1731476948365.c1kab.34ag',
            '_RSG': 'GTagMfp4rWEXAJL7ZC63HA',
            '_RDG': '288775a6efa26f2d75343ff87fdeb2fc86',
            '_RGUID': 'e835133a-56aa-4750-a443-18c8c75532a1',
            'StartCity_Pkg': 'PkgStartCity=6',
            'nfes_isSupportWebP': '1',
            '_bfaStatusPVSend': '1',
            '_RF1': '123.177.53.139',
            '_ubtstatus': '%7B%22vid%22%3A%221731476947273.a7b45HPTkTVR%22%2C%22sid%22%3A18%2C%22pvid%22%3A10%2C%22pid%22%3A600001375%7D',
            '_bfaStatus': 'success',
            'ibulanguage': 'CN',
            'ibulocale': 'zh_cn',
            'cookiePricesDisplayed': 'CNY',
            '_abtest_userid': 'f2d1418a-1dd3-4b74-a2ab-40cbb53019e2',
            'appFloatCnt': '1',
            'Hm_lvt_a8d6737197d542432f4ff4abc6e06384': '1731476947,1731835830,1731920792,1732847172',
            '_ga': 'GA1.1.851142854.1731476948',
            'Session': 'smartlinkcode=U130727&smartlinklanguage=zh&SmartLinkKeyWord=&SmartLinkQuary=&SmartLinkHost=',
            'Union': 'AllianceID=4902&SID=130727&OUID=&createtime=1732847175&Expires=1733451974870',
            'MKT_Pagesource': 'PC',
            '_ga_9BZF483VNQ': 'GS1.1.1732860047.4.1.1732860071.0.0.0',
            '_ga_5DVRDQD429': 'GS1.1.1732860047.4.1.1732860071.0.0.0',
            '_ga_B77BES1Z8Z': 'GS1.1.1732860047.4.1.1732860071.36.0.0',
            '_jzqco': '%7C%7C%7C%7C1732875288179%7C1.1595707400.1732875276978.1732875276978.1732875342323.1732875276978.1732875342323.0.0.0.2.2',
            '_bfa': '1.1731476947273.a7b45HPTkTVR.1.1732875293312.1732875345206.1.2.10650142842',
        }
        self.headers = {
            'accept': '*/*',
            'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
            'content-type': 'application/json',
            # 'cookie': 'Hm_lvt_a8d6737197d542432f4ff4abc6e06384=1731476947; Hm_lpvt_a8d6737197d542432f4ff4abc6e06384=1731476947; HMACCOUNT=90ADBB02DA26C77F; UBT_VID=1731476947273.a7b45HPTkTVR; _ga=GA1.1.851142854.1731476948; GUID=09031076110042895602; MKT_CKID=1731476948365.c1kab.34ag; Session=smartlinkcode=U130727&smartlinklanguage=zh&SmartLinkKeyWord=&SmartLinkQuary=&SmartLinkHost=; Union=AllianceID=4902&SID=130727&OUID=&createtime=1731476949&Expires=1732081748592; _RF1=175.170.154.113; _RSG=GTagMfp4rWEXAJL7ZC63HA; _RDG=288775a6efa26f2d75343ff87fdeb2fc86; _RGUID=e835133a-56aa-4750-a443-18c8c75532a1; MKT_Pagesource=PC; _ga_5DVRDQD429=GS1.1.1731476948.1.1.1731477013.0.0.0; _ga_B77BES1Z8Z=GS1.1.1731476948.1.1.1731477013.60.0.0; _ga_9BZF483VNQ=GS1.1.1731476948.1.1.1731477013.0.0.0; StartCity_Pkg=PkgStartCity=6; nfes_isSupportWebP=1; _jzqco=%7C%7C%7C%7C1731476949536%7C1.29963991.1731476948363.1731477240401.1731477323478.1731477240401.1731477323478.undefined.0.0.7.7; _bfa=1.1731476947273.a7b45HPTkTVR.1.1731477242992.1731477324168.1.12.10650142842',
            'cookieorigin': 'https://you.ctrip.com',
            'origin': 'https://you.ctrip.com',
            'priority': 'u=1, i',
            'referer': 'https://you.ctrip.com/',
            'sec-ch-ua': '"Chromium";v="130", "Microsoft Edge";v="130", "Not?A_Brand";v="99"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-site',
            'user-agent': UserAgent().edge,
        }
        self.params = {
            '_fxpcqlniredt': '09031076110042895602',
            'x-traceID': '09031076110042895602-1731477326751-3722506',
        }
        self.json_data = {
            'head': {
                'cid': '09031076110042895602',
                'ctok': '',
                'cver': '1.0',
                'lang': '01',
                'sid': '8888',
                'syscode': '999',
                'auth': '',
                'xsid': '',
                'extension': [],
            },
            'scene': 'online',
            # 代表城市id
            'districtId': 4,
            # 代表页数（超过页数返回数据为空）
            'index': 1,
            'sortType': 1,
            # 代表返回数量（正常每页10个，最多可选20个（包含本页和下一页的））
            'count': 10,
            'filter': {
                'filterItems': [],
            },
            'coordinate': {
                'latitude': 38.8879,
                'longitude': 121.5447,
                'coordinateType': 'WGS84',
            },
            'returnModuleType': 'all',
        }

        """定义文件 路径 以及 列名"""
        # 定义异常文件 路径 以及 列名
        self.files_error = "log"
        if not os.path.exists(self.files_error):
            # 如果文件夹不存在，则创建它
            os.makedirs(self.files_error)
        self.error_file_path = os.path.join(self.files_error, "error.csv")
        self.columns_error = {
            "column1_error": "异常信息",
            "column2_error": "城市id",
            "column3_error": "城市名称",
            "column4_error": "景区id",
            "column5_error": "景区名称",
            "column6_error": "热门商圈页面所在页数",
            "column7_error": "第几个景区",
            "column8_error": "错误日志",
            "column9_error": "景区详细链接",
            "column10_error": "记录时间",
        }
        for attr, value in self.columns_error.items():
            setattr(self, attr, value)

        # 定义数据文件 路径 以及 列名
        self.files_path = "data"
        if not os.path.exists(self.files_path):
            # 如果文件夹不存在，则创建它
            os.makedirs(self.files_path)
        self.data_file_path = os.path.join(self.files_path, "data.csv")
        self.columns_data = {
            "column1_data": "景区id",
            "column2_data": "区域名称",
            "column3_data": "景区名称",
            "column4_data": "景区评论得分",
            "column5_data": "星级",
            "column6_data": "景区展示图片",
            "column7_data": "景区标签列表",
            "column8_data": "景区门票价格",
            "column9_data": "景区是否免费",
            "column10_data": "景区特点描述",
            "column11_data": "景区榜单",
            "column12_data": "景区纬度",
            "column13_data": "景区经度",
            "column14_data": "景区热度",
            "column15_data": "景区地址",
            "column16_data": "联系电话",
            "column17_data": "开放时间",
            "column18_data": "介绍",
            "column19_data": "优待政策",
            "column20_data": "服务设施"
        }

        for attr, value in self.columns_data.items():
            setattr(self, attr, value)

        # choice错误提示
        self.choice_error = "\n不是哥们，有这功能吗，代码给你你来写呗。"


    def change_city(self, city_id, city_name):
        self.json_data["districtId"] = city_id
        self.data_file_path = os.path.join(self.files_path, f"{city_name}.csv")

    def change_page(self, page):
        self.json_data["index"] = page

    def gold_text(self, text):
        # 使用 ANSI 转义序列设置文本颜色为金色
        gold_color_code = "\033[38;2;255;215;0m"  # 金色 (RGB: 255, 215, 0)
        reset_color_code = "\033[0m"  # 重置颜色
        print(f"{gold_color_code}{text}{reset_color_code}")

    def red_text(self, text):
        # 使用ANSI转义序列设置文本颜色为红色
        red_color_code = "\033[31m"  # 红色
        reset_color_code = "\033[0m"  # 重置颜色
        print(f"{red_color_code}{text}{reset_color_code}")
    def blue_text(self, text):
        # 使用ANSI转义序列设置文本颜色为蓝色
        blue_color_code = "\033[34m"  # 蓝色
        reset_color_code = "\033[0m"  # 重置颜色
        print(f"{blue_color_code}{text}{reset_color_code}")

    def purple_text(self, text):
        # 使用ANSI转义序列设置文本颜色为紫色
        purple_color_code = "\033[35m"  # 紫色
        reset_color_code = "\033[0m"  # 重置颜色
        print(f"{purple_color_code}{text}{reset_color_code}")

    # 接收文件路径、列名后缀、列名字典、数据列表
    def write_csv(self, file_path, column_suffix, column_dict, list_data):
        # 检查文件是否存在
        file_exists = os.path.isfile(file_path)
        encoding = 'utf-8'
        if file_exists:
            # 检测文件编码
            encoding = self.detect_encoding(file_path)
        # 打开 CSV 文件并写入数据（有续写功能）
        with open(file_path, mode='a' if file_exists else 'w', newline='', encoding=encoding) as file:
            fieldnames = [getattr(self, f'column{i}_{column_suffix}') for i in range(1, len(column_dict) + 1)]
            writer = csv.DictWriter(file, fieldnames=fieldnames)

            # 如果文件不存在，写入表头
            if not file_exists:
                writer.writeheader()

            # 写入行
            row_data = {
                getattr(self, f'column{i}_{column_suffix}'): list_data[i - 1]
                for i in range(1, len(column_dict) + 1)
            }
            writer.writerow(row_data)

    # 接收 异常信息 城市id 城市名称 景区id 景区名称 热门商圈页面所在页数 第几个景区 错误日志（是热门商圈还是景区详情报错了） 景区详情链接
    def dispose_abnormal(self, e, city_id, city_name, businessId, poi_name, page, index, message, detail_url):
        # 处理异常情况，请求超时或者请求异常
        # 记录异常日志
        self.write_csv(self.error_file_path, "error", self.columns_error,
                       [e, city_id, city_name, businessId, poi_name, page, index, message, detail_url, datetime.now().strftime("%Y-%m-%d %H:%M")])
        self.red_text(f"异常日志已记录在： {self.error_file_path}")
        # 重置会话（防止长时间连接）
        self.main_instance.session = requests.session()
        if e == "暂停程序":
            sys.exit()
        # 热门商圈页面请求失败会暂停程序一段时间
        if businessId == "无":
            # 开启全自动则接着爬取
            if self.voluntarily:
                # 热门商圈页面进不去了，暂停1个小时
                time.sleep(self.timeout_wait)
                self.main_instance.run("2")
            else:
                self.main_instance.run(False)
        else:
            if e == "景区详情页面返回数据为None":
                self.red_text('请点击上一景区 "详情链接" 完成图形验证')
                sys.exit()
            # 详情页面请求失败不会重新爬取而是将详情数据赋值为空
            else:
                pass

    def read_error(self):
        # 检测文件编码
        encoding = self.detect_encoding(self.error_file_path)
        with open(self.error_file_path, mode='r', newline='', encoding=encoding) as file:
            reader = csv.DictReader(file)
            for row in reader:
                last_row = row

            if last_row:
                return last_row[self.column3_error], last_row[self.column2_error], last_row[self.column6_error]

    def detect_encoding(self, file_path):
        # 读取文件内容的前 1024 字节来检测编码
        with open(file_path, 'rb') as f:
            raw_data = f.read(1024)
        result = chardet.detect(raw_data)
        return result['encoding']

    def go_on(self):
        # 若error文件不存在或没有数据则返回1
        try:
            city_name, city_id, start_page = self.read_error()
        except Exception as e:
            self.red_text(f"读取error文件报错：\n{e}")
            return False

        return [city_name, city_id, int(start_page)]

    def fuc_suspend(self, e, city_id, city_name, businessId, poi_name, page, index, message):
        self.blue_text("\n程序已经暂停采集>>>")
        self.dispose_abnormal(e, city_id, city_name, businessId, poi_name, page, index, message, "无")