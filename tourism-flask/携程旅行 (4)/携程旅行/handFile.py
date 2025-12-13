#!/user/bin/env python3
# -*- coding: utf-8 -*-
"""
最好不要自己到文件里面修改东西，可能会出现编码不统一的情况，导致乱码或者不能正常写入的情况。
可以在这里手动处理一些数据、文件。
实在不行就直接删除吧
"""
import os
import csv
import sys

import chardet

class Hand:
    def __init__(self):
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
        }
        for attr, value in self.columns_error.items():
            setattr(self, attr, value)

    def red_text(self, text):
        # 使用ANSI转义序列设置文本颜色为红色
        red_color_code = "\033[31m"  # 红色
        reset_color_code = "\033[0m"  # 重置颜色
        print(f"{red_color_code}{text}{reset_color_code}")

    def detect_encoding(self, file_path):
        # 读取文件内容的前 1024 字节来检测编码
        with open(file_path, 'rb') as f:
            raw_data = f.read(1024)
        result = chardet.detect(raw_data)
        return result['encoding']
    def write_error_hand(self, error_list):
        # 构建 error.csv 的绝对路径
        # 检查文件是否存在
        file_exists = os.path.isfile(self.error_file_path)
        # 打开 CSV 文件并写入数据（有续写功能）
        encoding = 'utf-8'
        if file_exists:
            # 检测文件编码
            encoding = self.detect_encoding(self.error_file_path)

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
        self.red_text(f"异常日志已记录在： {self.error_file_path}")

    def hand_delete_error(self, file_path, start_row, end_row):
        # 读取CSV文件
        with open(file_path, mode='r', newline='', encoding='utf-8') as file:
            reader = csv.reader(file)
            rows = list(reader)

        # 计算要删除的行数
        rows_to_delete = end_row - start_row + 1
        start_row = start_row - 1
        end_row = end_row - 1

        # 检查起始行和结束行是否有效
        if start_row < 0 or end_row >= len(rows) or start_row > end_row:
            print("起始行或结束行无效。")
        else:
            # 删除指定范围内的行
            rows = rows[:start_row] + rows[end_row + 1:]

            # 写回CSV文件
            with open(file_path, mode='w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerows(rows)
            print(f"已成功删除 {file_path} 中从第 {start_row + 1} 行到第 {end_row + 1} 行的数据。")

    def hand_write_error(self, city_id, city_name, page):
        # 手动插入异常数据
        self.write_error_hand(["手动输入", city_id, city_name, "无", "无", page, "无", "手动输入", "无"])

    def view_coding(self, folder_path, file_name):
        # 遍历文件夹中的所有文件
        for filename in os.listdir(folder_path):
            # 检查文件是否为CSV文件
            if filename.endswith(".csv"):
                file_path = os.path.join(folder_path, filename)

                # 读取文件的前1024字节以检测编码格式
                with open(file_path, 'rb') as file:
                    raw_data = file.read(1024)
                    result = chardet.detect(raw_data)
                    encoding = result['encoding']

                # 打印文件名及其编码格式
                if (filename == (file_name + ".csv")) or (file_name == "all"):
                    print(f"文件名: {filename}, 编码格式: {encoding}")

    def view_content(self, file_path):
        # 打开 CSV 文件
        with open(file_path, newline='', encoding='utf-8') as csvfile:
            # 创建 CSV 读取器
            reader = csv.reader(csvfile)
            # 跳过第一行（列名）
            next(reader)
            # 遍历每一行并打印内容
            for row in reader:
                print(row)

    def run(self):
        choice = input("请输入你的选择：\n1.向异常文件中插入一条数据\n2.删除data文件夹中指定城市的部分数据\n3.删除异常文件中的部分数据"
                       "\n4.打印指定文件夹下某个/所有csv文件的编码格式\n5.查看某个景区csv文件的内容\n6.退出")
        if choice == "1":
            # 向异常文件中插入一条数据
            self.hand_write_error(2429, "南昌县", 1)
        elif choice == "2":
            # 删除data文件夹中指定城市的部分数据
            city_name = "甘孜县"
            file_path = os.path.join("data", f"{city_name}.csv")
            start_row = 647  # 起始行（包含）
            end_row = 647  # 结束行（包含）
            self.hand_delete_error(file_path, start_row, end_row)
        elif choice == "3":
            # 删除异常文件中的部分数据
            city_name = "error"
            file_path = os.path.join("log", f"{city_name}.csv")
            start_row = 2  # 起始行（包含）
            end_row = 9032  # 结束行（包含）
            self.hand_delete_error(file_path, start_row, end_row)
        elif choice == "4":
            # 打印指定文件夹下某个/所有csv文件的编码格式
            folder_path = "data"
            # file_name为"all"时候打印所有文件夹下所有文件
            file_name = "保亭"
            self.view_coding(folder_path, file_name)
        elif choice == "5":
            wenjianjia = "data"
            file_path = "保亭"
            file_path = os.path.join(wenjianjia, file_path + ".csv")
            self.view_content(file_path)
        elif choice == "6":
            sys.exit()
        else:
            print("你。。。。。。。")
            self.run()

if __name__ == '__main__':
    hand = Hand()
    hand.run()