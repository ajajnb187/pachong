"""
主程序
按下^（shift+6）会等待爬取完当前页后结束爬取并记录爬取进度!
手动终止程序不会记录异常日志，写入的数据也可能出现当前页写入小于10个景区的情况
不要手动修改代码需要读取或写入的文件，会导致乱码
"""
import time

import requests
from helper import settings
from bs4 import BeautifulSoup
from helper import crawlingCityId
import sys
import threading
import keyboard

class Main:
    def __init__(self):
        # 实例化
        self.settings = settings.Settings(self)
        self.city_nameids = crawlingCityId.City("helper/files")
        # Session对象
        self.session = requests.session()

    def crawling_external(self, page, city_name, city_id):
        # 设置本次要爬取的页数
        self.settings.change_page(page)
        data_all = None
        try:
            response = self.session.post(
                self.settings.url,
                params=self.settings.params,
                cookies=self.settings.cookies,
                headers=self.settings.headers,
                json=self.settings.json_data,
                timeout=self.settings.timeout
            )
        except requests.exceptions.Timeout:
            self.settings.dispose_abnormal("超时", city_id, city_name, "无", "无", page, "无", "热门商圈页面请求失败", "无")
        except requests.exceptions.RequestException as e:
            self.settings.dispose_abnormal(e, city_id, city_name, "无", "无", page, "无", "热门商圈页面请求失败", "无")
        else:
            try:
                response_json = response.json()
                data_all = response_json.get("attractionList")
            except Exception as e:
                self.settings.dispose_abnormal(e, city_id, city_name, "无", "无", page, "无",
                                               "热门商圈页面进不去了？", "无")

        return data_all

    def crawling_interior(self, city_id, city_name, businessId, poi_name, detail_url, page, index):
        try:
            response = self.session.get(detail_url, timeout=self.settings.timeout_detail)
            response.raise_for_status()  # 检查响应状态码（状态码为失败状态则抛出错误）
        except requests.exceptions.Timeout:
            self.settings.dispose_abnormal("超时", city_id, city_name, businessId, poi_name, page, index, "景区详情页面请求失败", detail_url)
            # 将详情信息赋为空值
            self.settings.red_text(f"景区id：{businessId} 景区名称：{poi_name} 该景区详情页面请求失败")
            [address, phone, opening_hours, introduce] = [""] * 4
            preferential_policies_list, service_facility_list = [], []
        except requests.exceptions.RequestException as e:
            self.settings.dispose_abnormal(e, city_id, city_name, businessId, poi_name, page, index, "景区详情页面请求失败", detail_url)
            # 检查错误信息是否包含 "500 Server Error"
            if "500 Server Error" in str(e):
                # 这种情况为对方服务器资源不足，等待60s后重新请求,只请求3次，不行则跳过该景区
                self.settings.request_detail_500 += 1
                if self.settings.request_detail_500 <= 3:
                    time.sleep(self.settings.timeout_detail_500)
                    self.crawling_interior(city_id, city_name, businessId, poi_name, detail_url, page, index)
                else:
                    self.settings.request_detail_500 = 0

            # 将详情信息赋为空值
            self.settings.red_text(f"景区id：{businessId} 景区名称：{poi_name} 该景区详情页面请求失败")
            [address, phone, opening_hours, introduce] = [""] * 4
            preferential_policies_list, service_facility_list = [], []
        else:
            try:
            # 解析HTML响应
                soup = BeautifulSoup(response.text, 'html.parser')
                base_info_main_div = soup.find('div', class_='baseInfoMain')
                detail_module_normal_module = (soup.find('div', class_='moduleWrap').find("div", class_="mainModule")
                                         .find("div", class_="detailModuleRef").find("div", class_="detailModule normalModule"))
            except:
                self.settings.dispose_abnormal("景区详情页面返回数据为None", city_id, city_name, businessId, poi_name, page, index,
                                               "景区详情页面请求失败", detail_url)

            # 以下数据有的景区没有，没有的会报错
            # 景区地址
            try:
                address = base_info_main_div.find_all("div", class_="baseInfoItem")[0].find('p', class_='baseInfoText').text
            except:
                address = ""
            # 景区官方电话
            try:
                phone = (base_info_main_div.find_all("div", class_="baseInfoItem")[2].
                     find('p', class_='baseInfoText').text)
            except:
                phone = ""
            # 景区开放时间
            try:
                opening_hours = (detail_module_normal_module.find_all("div", class_="moduleContent")[1].text)
            except:
                opening_hours = ""
            # 景区介绍
            try:
                introduce = (detail_module_normal_module.find_all("div", class_="moduleContent")[0].text)
            except:
                introduce = ""
            try:
                # 景区优待政策（为列表，列表中存储了多个数据，每条数据为一行）
                preferential_policies_all = (detail_module_normal_module.find_all("div", class_="moduleContent")[2].
                                         find_all("div", class_="moduleContentRow"))
                preferential_policies_list = []
                for preferential_policies in preferential_policies_all:
                    preferential_policies_list.append(preferential_policies.text)
            except:
                preferential_policies_list = []
            try:
                # 景区服务设施（为列表，列表中存储了多个数据，每条数据为一行）
                service_facility_all = (detail_module_normal_module.find_all("div", class_="moduleContent")[3].
                                    find_all("div", class_="moduleContentRow"))
                service_facility_list = []
                for service_facility in service_facility_all:
                    service_facility_list.append(service_facility.text)
            except:
                service_facility_list = []

            # 待处理数据
            print(f"地址：{address}, 电话：{phone}, 开放时间：{opening_hours}")
            print(f"介绍：{introduce}")
            print(f"优待政策：{preferential_policies_list}")
            print(f"服务设施：{service_facility_list}")

        return address, phone, opening_hours, introduce, preferential_policies_list, service_facility_list


    def processing_data(self, city_name, city_id, start_page):
        self.settings.gold_text(f"正在爬取 {city_name} 城市：")
        # 修改城市id以及名称
        self.settings.change_city(city_id, city_name)

        for page in range(start_page, self.settings.max_page):
            # 若页面没数据，则返回None，结束该城市的循环（因为后面的页数也没有数据了）
            data_all = self.crawling_external(page, city_name, city_id)
            if data_all is None:
                break
            self.settings.purple_text(f"第 {page} 页，该页有 {len(data_all)} 条数据：")
            # 处理每个景区的数据
            index = 0
            if not self.settings.suspend:
                for data in data_all:
                    # 计算本次循环为第几次
                    index += 1
                    # 景区id
                    businessId = data.get("card").get("businessId")
                    # 景区所在区域名称
                    zone_name = data.get("card").get("zoneName")
                    # 景区名称
                    poi_name = data.get("card").get("poiName")
                    # 景区评论得分（5分满分）
                    comment_score = data.get("card").get("commentScore")
                    # 星级（5A最好）
                    sight_level = data.get("card").get("sightLevelStr")
                    # 景区展示图片
                    cover_image_url = data.get("card").get("coverImageUrl")
                    # 景区标签列表
                    tag_name_list = data.get("card").get("tagNameList")
                    # 景区门票价格（免费景区为null）
                    market_price = data.get("card").get("marketPrice")
                    # 景区是否免费（False为不免费，True为免费）
                    is_free = data.get("card").get("isFree")
                    # 景区特点描述（放在景区名称后面）
                    short_features = data.get("card").get("shortFeatures")
                    # 景区榜单（没有榜单的话为null，展示的时候加个榜单特效）
                    sight_category_info = data.get("card").get("sightCategoryInfo")
                    # 景区纬度（该位置是百度坐标系，我使用百度地图计算应该没毛病）
                    latitude = data.get("card").get("coordinate").get("latitude")
                    # 景区经度
                    longitude = data.get("card").get("coordinate").get("longitude")
                    # 景区热度（10分满）
                    heat_score = data.get("card").get("heatScore")
                    # 景区详情链接
                    detail_url = data.get("card").get("detailUrl")

                    self.settings.blue_text(f"\n景区：{poi_name}")
                    print(f"景区id：{businessId}, 景区区域：{zone_name}, 评论得分：{comment_score}, 星级：{sight_level}, "
                          f"展示图片：{cover_image_url}, 标签：{tag_name_list}, 门票：{market_price}, 是否免费：{is_free}, "
                          f"描述：{short_features}, 榜单：{sight_category_info}, 维度：{latitude},"
                          f" 经度：{longitude}, 热度：{heat_score}, 详情链接：{detail_url}")

                    # 爬取景区详情页面数据
                    address, phone, opening_hours, introduce, preferential_policies_list, service_facility_list = (
                        self.crawling_interior(city_id, city_name, businessId, poi_name, detail_url, page, index))

                    # 将数据写入文件
                    self.settings.write_csv(self.settings.data_file_path, "data", self.settings.columns_data,
                                            [businessId, zone_name, poi_name, comment_score, sight_level, cover_image_url,
                                            tag_name_list, market_price, is_free, short_features, sight_category_info,
                                            latitude, longitude, heat_score, address, phone, opening_hours, introduce,
                                            preferential_policies_list, service_facility_list])
                    self.settings.gold_text(f"数据已成功写入到 {self.settings.data_file_path}")
            else:
                # 暂停采集
                self.settings.fuc_suspend("暂停程序", city_id, city_name, "无", "无", page, "无", "暂停程序")

    def read_city_id(self):
        # 读取城市id
        city_names, city_ids = self.city_nameids.read_csv()

        if len(city_names) != len(city_ids):
            # 结束程序
            self.settings.red_text("城市id与名称数量不相符!")
            sys.exit()

        for i in range(0, len(city_ids)):
            self.processing_data(city_names[i], city_ids[i], 1)

    def stop_loop(self):
        self.settings.suspend = True

    def go_on(self, city_id, start_page, single):
        # 读取城市id
        city_names, city_ids = self.city_nameids.read_csv()

        if len(city_names) != len(city_ids):
            # 结束程序
            self.settings.red_text("城市id与名称数量不相符!")
            sys.exit()

        # 单独爬取某个城市
        if single:
            index = city_ids.index(city_id)
            self.processing_data(city_names[index], city_ids[index], 1)
        else:
            for i in range(city_ids.index(city_id), len(city_ids)):
                if i != city_ids.index(city_id):
                    start_page = 1
                self.processing_data(city_names[i], city_ids[i], start_page)


    def run(self, choice):
        if not choice:
            if self.settings.go_on() is not False:
                city_name, city_id, start_page = self.settings.go_on()
                choice = input(f"\n请选择你要进行的操作：\n1.从头开始采集数据\n2.继续上次异常进度（城市：{city_name}，页数："
                               f"第 {start_page} 页）\n3.自己定义起始城市\n4.爬取单个城市\n5.退出")
            else:
                choice = input(
                    f"\n请选择你要进行的操作：\n1.从头开始采集数据\n2.继续上次异常进度（未检测到任何进度）\n3.自己定义起始城市\n"
                    f"4.爬取单个城市\n5.退出")

        if choice == "1":
            self.read_city_id()
        elif choice == "2":
            if self.settings.go_on() is not False:
                city_name, city_id, start_page = self.settings.go_on()
                self.go_on(city_id, start_page, False)
            else:
                self.read_city_id()
        elif choice == "3":
            start_city_id = input("请输入起始城市的id（去helper/files/cities.csv文件中查找）：")
            start_page = int(input("请输入起始页数（起始值为1）："))
            self.go_on(start_city_id, start_page, False)
        elif choice == "4":
            single_city_id = input("请输入单独爬取的城市的id（去helper/files/cities.csv文件中查找）：")
            start_page = int(input("请输入起始页数（起始值为1）："))
            self.go_on(single_city_id, start_page, True)
        elif choice == "5":
            print("\n退出程序！")
            sys.exit()
        else:
            self.settings.red_text(self.settings.choice_error)


if __name__ == '__main__':
    # 启动主程序
    main = Main()
    loop_thread = threading.Thread(target=main.run, args=(False,))
    loop_thread.start()
    # 监听键盘事件
    def on_key_press(event):
        if event.name == '^':
            main.stop_loop()
            # 停止监听键盘事件
            keyboard.unhook_all()
    # 注册键盘事件监听器
    keyboard.on_press(on_key_press)
    # 等待线程结束
    loop_thread.join()