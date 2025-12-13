"""
写入 读取 所有城市id以及对应name
手动终止程序不会写入进度以及数据！（因为手动终止的时候数据可能只爬取了某页的一半，不方便记录）
按下^（shift+6）会等待爬取完当前页后结束爬取并记录爬取进度!
全自动爬取，打开 self.voluntarily 开关可实现解放双手：“点击一次，爬取所有”
当爬取失败的时候会记录进度，运行程序后可以选择读取上次的进度继续爬取或从头开始爬取
想添加列名的话直接在init函数中对应的字典中按照数字顺序添加字符串即可（如果修改列名，那么代码中使用字典的地方也需要修改,方法传参数的时候）
"""
import random
import sys
from lxml import etree
import requests
from fake_useragent import UserAgent
from tqdm import tqdm
import urllib3
import re
import csv
import os
from datetime import datetime
import chardet

class City:
    def __init__(self, files_path):
        # 自动爬取开关（True为开启，开启后请求失败的程序会接着异常时候的页数运行直到数据全部爬取）
        self.voluntarily = True
        # 程序运行开关
        self.suspend = False

        # Session对象
        self.session = requests.session()
        # 全国城市所在页面的url
        self.url = "https://you.ctrip.com/countrysightlist/china110000/p1.html"

        # 生成随机UA列表
        ua = UserAgent()
        self.list_ua = []
        for i in range(100):
            self.list_ua.append(ua.edge)

        # 请求超时时间
        self.timeout = 20

        # 检测文件夹是否存在
        if not os.path.exists(files_path):
            # 如果文件夹不存在，则创建它
            os.makedirs(files_path)
        # 定义CSV文件 路径 以及 列名
        self.csv_file_path = os.path.join(files_path, "cities.csv")
        self.columns_csv = {
            "column1_csv": "城市名称",
            "column2_csv": "城市ID",
        }
        for attr, value in self.columns_csv.items():
            setattr(self, attr, value)

        # 定义日志文件 路径 以及 列名
        self.error_file_path = os.path.join(files_path, "error.csv")
        self.columns_error = {
            "column1_error": "类名",
            "column2_error": "时间",
            "column3_error": "page",
            "column4_error": "error"
        }
        for attr, value in self.columns_error.items():
            setattr(self, attr, value)

    def get_class_name(self):
        return self.__class__.__name__

    def stop_loop(self):
        self.suspend = True

    def fuc_suspend(self, page, city_dict):
        self.blue_text("\n程序已经暂停采集>>>")
        self.dispose_abnormal("暂停程序", page, city_dict)

    # 爬取城市名称和城市ID
    def crawlling_cityid(self, start_page):
        # 设置请求头
        headers = {
            'User-Agent': random.choice(self.list_ua)
        }

        response = self.session.get(self.url, headers=headers, verify=False)

        html = etree.HTML(response.text)
        page_total = html.xpath('//*[@id="content"]/div[4]/div/div[2]/div/div[2]/div[11]/div/span/b/text()')[0]
        # 爬取城市名称和城市ID
        city_dict = {}
        for page in tqdm(range(start_page, int(page_total) + 1)):
            if not self.suspend:
                url = "https://you.ctrip.com/countrysightlist/china110000/p{0}.html".format(page)
                # 设置请求头
                headers = {
                    'User-Agent': random.choice(self.list_ua)
                }

                try:
                    response = self.session.get(url, headers=headers, verify=False, timeout=self.timeout)
                    response.raise_for_status()  # 检查响应状态码
                except requests.exceptions.Timeout:
                    self.dispose_abnormal("超时", page, city_dict)
                except requests.exceptions.RequestException as e:
                    self.dispose_abnormal(e, page, city_dict)

                html = etree.HTML(response.text)
                big_div = html.xpath('//*[@id="content"]/div[4]/div/div[2]/div/div[2]/div[@class="list_mod1"]')
                for small_div in big_div:
                    cityid = small_div.xpath('./dl/dt/a/@href')[0]
                    cityname = small_div.xpath('./dl/dt/a/text()')[0]
                    # 提取路径中的城市id
                    cityid = re.search(r'\d+', cityid).group()
                    city_dict[cityname] = cityid
            else:
                self.fuc_suspend(page, city_dict)
        return city_dict


    def dispose_abnormal(self, e, page, city_dict):
        # 处理异常情况，请求超时或者请求异常
        # 记录异常日志
        self.write_error([self.get_class_name(), datetime.now().strftime("%Y-%m-%d %H:%M:%S"), page, e])
        # 将当前爬取数据写入csv文件
        self.write_csv(city_dict)
        if e == "暂停程序":
            sys.exit()
        # 开启全自动则接着爬取
        if self.voluntarily:
            self.run("2")
        else:
            self.run(False)

    def write_error(self, error_list):
        # 检查文件是否存在
        file_exists = os.path.isfile(self.error_file_path)
        encoding = 'utf-8'
        if file_exists:
            # 检测文件编码
            encoding = self.detect_encoding(self.error_file_path)
        # 打开 CSV 文件并写入数据（有续写功能）
        with open(self.error_file_path, mode='a' if file_exists else 'w', newline='', encoding=encoding) as file:
            fieldnames = [getattr(self, f'column{i}_error') for i in range(1, len(self.columns_error) + 1)]
            writer = csv.DictWriter(file, fieldnames=fieldnames)

            # 如果文件不存在，写入表头
            if not file_exists:
                writer.writeheader()
            # 写入行
            row_data = {
                getattr(self, f'column{i}_error'): error_list[i - 1]
                for i in range(1, len(self.columns_error) + 1)
            }
            writer.writerow(row_data)
        self.red_text(f"在 {error_list[1]}\t'{error_list[0]}' 类采集第 '{error_list[2]}' 页时发生了异常：'{error_list[3]}'")
        self.red_text(f"异常日志已记录在： {self.error_file_path}")

    def read_error(self):
        # 检测文件编码
        encoding = self.detect_encoding(self.error_file_path)
        with open(self.error_file_path, mode='r', newline='', encoding=encoding) as file:
            reader = csv.DictReader(file)
            for row in reader:
                last_row = row

            if last_row:
                return last_row[self.column3_error]

    def write_csv(self, city_dict):
        # 检查文件是否存在
        file_exists = os.path.isfile(self.csv_file_path)
        encoding = 'utf-8'
        if file_exists:
            # 检测文件编码
            encoding = self.detect_encoding(self.csv_file_path)
        # 打开 CSV 文件并写入数据（有续写功能）
        with open(self.csv_file_path, mode='a' if file_exists else 'w', newline='', encoding=encoding) as file:
            fieldnames = [getattr(self, f'column{i}_csv') for i in range(1, len(self.columns_csv) + 1)]
            writer = csv.DictWriter(file, fieldnames=fieldnames)

            # 如果文件不存在，写入表头
            if not file_exists:
                writer.writeheader()

            # 写入数据
            # 将字典转换为 [[key1, value1], [key2, value2], ...] 形式
            city_lists = [[key, value] for key, value in city_dict.items()]
            for city_list in city_lists:
                # 写入数据
                row_data = {
                    getattr(self, f'column{i}_csv'): city_list[i - 1]
                    for i in range(1, len(self.columns_csv) + 1)
                }
                writer.writerow(row_data)

        self.gold_text(f"数据已成功写入到 {self.csv_file_path}")

    def read_csv(self):
        # 初始化两个列表
        city_ids = []
        city_names = []

        encoding = self.detect_encoding(self.csv_file_path)
        # 打开 CSV 文件并读取数据
        with open(self.csv_file_path, mode='r', encoding=encoding) as file:
            reader = csv.DictReader(file)

            # 遍历每一行数据
            for row in reader:
                city_names.append(row[self.column1_csv])
                city_ids.append(row[self.column2_csv])

        return city_names, city_ids

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

    def detect_encoding(self, file_path):
        # 读取文件内容的前 1024 字节来检测编码
        with open(file_path, 'rb') as f:
            raw_data = f.read(1024)
        result = chardet.detect(raw_data)
        return result['encoding']

    def go_on(self):
        # 若error文件不存在或没有数据则返回1
        try:
            start_page = self.read_error()
        except:
            return 1

        return int(start_page)

    def run(self, choice):
        # 爬取城市id以及对应name
        if not choice:
            choice = input(f"\n请选择你要进行的操作：\n1.从头开始采集数据\n2.继续上次异常进度（第{self.go_on()}页）\n3.退出")

        start_page = 1
        if choice == "1":
            try:
                os.remove(self.csv_file_path)
                print("已删除cities.csv文件!")
            except:
                pass
        elif choice == "2":
            start_page = self.go_on()
        elif choice == "3":
            print("\n退出程序！")
            sys.exit()
        else:
            self.red_text("\n不是哥们，有这功能吗，代码给你你来写呗。")
            self.run(False)

        print("\n爬取中：")
        city_dict = self.crawlling_cityid(start_page)
        # 写入CSV文件
        self.write_csv(city_dict)


if __name__ == '__main__':
    import threading
    import keyboard
    # city = City("files")
    # city.run(False)
    # 防止InsecureRequestWarning 警告出现
    urllib3.disable_warnings()
    # 启动主程序
    city = City("files")
    loop_thread = threading.Thread(target=city.run, args=(False, ))
    loop_thread.start()
    # 监听键盘事件
    def on_key_press(event):
        if event.name == '^':
            city.stop_loop()
            # 停止监听键盘事件
            keyboard.unhook_all()
    # 注册键盘事件监听器
    keyboard.on_press(on_key_press)
    # 等待线程结束
    loop_thread.join()