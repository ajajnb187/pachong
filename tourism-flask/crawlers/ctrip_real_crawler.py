"""
携程爬虫 - 完全基于参考代码实现
直接使用参考代码的逻辑爬取福州真实数据
福州城市ID: 164
"""
import time
import uuid
import json
import requests
from datetime import datetime
from bs4 import BeautifulSoup
from utils.logger import logger
from config import Config

class CtripRealCrawler:
    """携程真实数据爬虫 - 基于参考代码"""
    
    def __init__(self):
        self.config = Config()
        # 参考代码中的API地址
        self.api_url = "https://m.ctrip.com/restapi/soa2/18109/json/getAttractionList"
        # 福州城市ID（来自cities.csv）
        self.fuzhou_city_id = 164
        # Session对象
        self.session = requests.session()
        logger.info(f"携程真实爬虫初始化完成（福州城市ID: {self.fuzhou_city_id}）")
    
    def search_scenic_spot(self, spot_name):
        """搜索景区 - 直接通过API获取，不需要预设ID"""
        logger.info(f"将通过API查找景区: {spot_name}")
        return spot_name  # 返回景区名称用于后续匹配
    
    def crawl_reviews(self, spot_id, spot_name, target_count):
        """
        爬取景区数据 - 完全按照参考代码逻辑
        
        Args:
            spot_id: 景区名称（用于匹配）
            spot_name: 景区名称
            target_count: 目标数量
            
        Yields:
            dict: 景区数据
        """
        logger.info(f"开始爬取福州景区数据: {spot_name}, 目标数量: {target_count}")
        
        count = 0
        page = 1
        max_pages = (target_count // 10) + 2
        
        while count < target_count and page <= max_pages:
            try:
                logger.info(f"正在爬取第 {page} 页...")
                
                # 调用API获取景区列表（参考代码逻辑）
                data_all = self._crawling_external(page)
                
                if not data_all:
                    logger.info(f"第{page}页无数据")
                    break
                
                logger.info(f"第{page}页获取到 {len(data_all)} 个景区")
                
                # 处理每个景区数据（参考代码逻辑）
                for data in data_all:
                    if count >= target_count:
                        break
                    
                    try:
                        card = data.get("card", {})
                        
                        # 提取景区信息（参考代码中的字段）
                        business_id = card.get("businessId")
                        zone_name = card.get("zoneName")
                        poi_name = card.get("poiName")
                        comment_score = card.get("commentScore")
                        sight_level = card.get("sightLevelStr")
                        cover_image_url = card.get("coverImageUrl")
                        tag_name_list = card.get("tagNameList")
                        market_price = card.get("marketPrice")
                        is_free = card.get("isFree")
                        short_features = card.get("shortFeatures")
                        sight_category_info = card.get("sightCategoryInfo")
                        
                        coordinate = card.get("coordinate", {})
                        latitude = coordinate.get("latitude")
                        longitude = coordinate.get("longitude")
                        
                        heat_score = card.get("heatScore")
                        detail_url = card.get("detailUrl")
                        
                        logger.info(f"景区: {poi_name}, ID: {business_id}")
                        
                        # 匹配逻辑：模糊匹配或爬取所有福州景区
                        if spot_name and spot_name != "福州":
                            if spot_name not in poi_name and poi_name not in spot_name:
                                pass  # 继续爬取所有福州景区
                        
                        # ⭐ 新增：访问详情页获取真实用户评论（包含历史日期）
                        if detail_url and count < target_count:
                            user_reviews = self._crawl_user_reviews_from_detail(
                                detail_url, business_id, poi_name, 
                                min(5, target_count - count)  # 每个景区最多爬5条评论
                            )
                            for review in user_reviews:
                                if count >= target_count:
                                    break
                                yield review
                                count += 1
                                logger.info(f"已提取 {count}/{target_count} 条数据（真实用户评论）")
                            
                            if count >= target_count:
                                break
                            
                            continue  # 跳过下面的官方描述数据
                        
                        # 构造评论数据（使用景区信息作为评论内容）
                        review_content = f"{poi_name}"
                        if zone_name:
                            review_content += f"，位于{zone_name}"
                        if short_features:
                            review_content += f"。{short_features}"
                        if sight_level:
                            review_content += f"，{sight_level}"
                        if tag_name_list:
                            tags_str = "、".join(tag_name_list) if isinstance(tag_name_list, list) else str(tag_name_list)
                            review_content += f"，标签：{tags_str}"
                        if market_price:
                            review_content += f"，门票：{market_price}"
                        elif is_free:
                            review_content += "，免费开放"
                        
                        # 提取官方图片
                        official_images = []
                        if cover_image_url:
                            official_images.append(cover_image_url)
                        
                        review_data = {
                            'scenic_spot': poi_name or '',
                            'city': '福州',
                            'rating': float(comment_score) if comment_score else 5.0,
                            'visitor_name': '携程官方',
                            'review_content': review_content,
                            'review_images': json.dumps(official_images, ensure_ascii=False) if official_images else '[]',
                            'travel_date': datetime.now().strftime('%Y-%m-%d'),
                            'review_date': datetime.now().strftime('%Y-%m-%d'),
                            'helpful_count': 3,
                            'visitor_level': sight_level or '',
                            'visitor_location': zone_name or '',
                            'data_source': 'ctrip',
                            'crawl_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        }
                        
                        yield review_data
                        count += 1
                        logger.info(f"已提取 {count}/{target_count} 条数据")
                        
                    except Exception as e:
                        logger.warning(f"处理景区数据失败: {str(e)}")
                        continue
                
                page += 1
                time.sleep(2)  # 延迟避免请求过快
                
            except Exception as e:
                logger.error(f"爬取第{page}页时出错: {str(e)}")
                break
        
        logger.info(f"数据爬取完成: {spot_name}, 共 {count} 条")
    
    def _crawl_user_reviews_from_detail(self, detail_url, spot_id, spot_name, limit=5):
        """
        调用携程评论API获取真实用户评论（包含历史日期）
        
        Args:
            detail_url: 详情页URL (用于提取景区ID)
            spot_id: 景区ID
            spot_name: 景区名称
            limit: 最多爬取数量
            
        Returns:
            list: 真实用户评论列表
        """
        reviews = []
        
        try:
            import re
            
            # 携程评论API endpoint
            comment_api = "https://m.ctrip.com/restapi/soa2/13444/json/getCommentCollapseList"
            
            # 构造API请求参数
            payload = {
                "arg": {
                    "businessType": 2,  # 景区类型
                    "resourceId": int(spot_id),
                    "resourceType": 11,
                    "pageIndex": 1,
                    "pageSize": limit,
                    "sortType": 3,  # 按时间排序
                    "imageType": 0,
                    "starType": 0
                },
                "head": {
                    "userRegion": "CN",
                    "Version": "1.0"
                }
            }
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Content-Type': 'application/json',
                'Referer': detail_url if detail_url else f'https://m.ctrip.com/'
            }
            
            logger.info(f"调用评论API获取真实评论: 景区ID={spot_id}")
            
            response = self.session.post(comment_api, json=payload, headers=headers, timeout=15)
            if response.status_code != 200:
                logger.warning(f"评论API调用失败: {response.status_code}")
                return reviews
            
            data = response.json()
            
            # 解析评论数据
            if data and 'result' in data:
                items = data.get('result', {}).get('items', [])
                
                for item in items[:limit]:
                    try:
                        # 提取评论内容
                        content = item.get('content', '').strip()
                        if len(content) < 10:
                            continue
                        
                        # 提取用户信息
                        user_info = item.get('userInfo', {})
                        user_name = user_info.get('userNick', '携程用户')
                        user_level = user_info.get('userLevel', '')
                        user_location = user_info.get('userProvince', '')
                        
                        # 提取IP属地
                        ip_location = item.get('ipLocatedName', '')
                        if not ip_location:
                            ip_location = user_location  # 回退到用户省份
                        
                        # 提取评分
                        rating = float(item.get('score', 5.0))
                        
                        # 提取日期 - 携程API使用特殊格式 /Date(1728683795000+0800)/
                        publish_time = item.get('publishTime', '')
                        publish_tag = item.get('publishTypeTag', '')  # 如 "2024-10-12 发布点评"
                        
                        # 解析日期格式
                        def parse_date(date_str, tag_str=''):
                            if not date_str:
                                return datetime.now().strftime('%Y-%m-%d')
                            
                            # 优先使用publishTypeTag中的格式化日期
                            if tag_str:
                                match = re.search(r'(\d{4})-(\d{1,2})-(\d{1,2})', tag_str)
                                if match:
                                    return f"{match.group(1)}-{match.group(2).zfill(2)}-{match.group(3).zfill(2)}"
                            
                            # 解析携程特殊格式：/Date(1728683795000+0800)/
                            match = re.search(r'/Date\((\d+)[+-]\d+\)/', date_str)
                            if match:
                                timestamp_ms = int(match.group(1))
                                dt = datetime.fromtimestamp(timestamp_ms / 1000)
                                return dt.strftime('%Y-%m-%d')
                            
                            # 尝试匹配 YYYY-MM-DD
                            match = re.search(r'(\d{4})-(\d{1,2})-(\d{1,2})', date_str)
                            if match:
                                return f"{match.group(1)}-{match.group(2).zfill(2)}-{match.group(3).zfill(2)}"
                            
                            # 尝试匹配 YYYY年MM月
                            match = re.search(r'(\d{4})年(\d{1,2})月', date_str)
                            if match:
                                return f"{match.group(1)}-{match.group(2).zfill(2)}-01"
                            
                            return datetime.now().strftime('%Y-%m-%d')
                        
                        review_date = parse_date(publish_time, publish_tag)
                        travel_date = review_date  # 使用发布时间作为旅游时间
                        
                        # 提取图片
                        images = item.get('images', [])
                        image_urls = [img.get('imageUrl', '') for img in images if img.get('imageUrl')]
                        
                        # 点赞数
                        helpful_count = int(item.get('likeCount', 0))
                        
                        review = {
                            'scenic_spot': spot_name,
                            'city': '福州',
                            'rating': rating,
                            'visitor_name': user_name,
                            'review_content': content[:500],  # 限制长度
                            'review_images': json.dumps(image_urls, ensure_ascii=False) if image_urls else '[]',
                            'travel_date': travel_date,
                            'review_date': review_date,
                            'helpful_count': helpful_count,
                            'visitor_level': user_level,
                            'visitor_location': user_location,
                            'ip_location': ip_location,  # IP属地
                            'data_source': 'ctrip',
                            'crawl_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        }
                        reviews.append(review)
                        logger.debug(f"提取评论: {user_name} - {travel_date}")
                        
                    except Exception as e:
                        logger.debug(f"解析评论项失败: {str(e)}")
                        continue
                
                logger.info(f"从评论API提取到 {len(reviews)} 条真实评论")
            else:
                logger.debug(f"评论API返回空数据")
            
        except Exception as e:
            logger.error(f"爬取评论API失败: {str(e)}")
        
        return reviews
    
    def _crawling_external(self, page):
        """
        调用API获取景区列表（参考代码中的方法）
        
        Args:
            page: 页码
            
        Returns:
            list: 景区列表
        """
        try:
            # 构造请求头（参考代码）
            headers = {
                'accept': '*/*',
                'accept-language': 'zh-CN,zh;q=0.9',
                'content-type': 'application/json',
                'cookieorigin': 'https://you.ctrip.com',
                'origin': 'https://you.ctrip.com',
                'referer': 'https://you.ctrip.com/',
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            }
            
            # 构造请求体（参考代码）
            json_data = {
                'head': {
                    'cid': '09031076110042895602',
                    'ctok': '',
                    'cver': '1.0',
                    'lang': '01',
                    'sid': '8888',
                    'syscode': '999',
                    'auth': '',
                    'extension': [],
                },
                'scene': 'online',
                'districtId': self.fuzhou_city_id,  # 福州城市ID: 164
                'index': page,
                'sortType': 1,
                'count': 10,
                'filter': {
                    'filterItems': [],
                },
                'coordinate': {
                    'latitude': 26.0745,  # 福州坐标
                    'longitude': 119.2965,
                    'coordinateType': 'WGS84',
                },
                'returnModuleType': 'all',
            }
            
            # 发送POST请求
            response = self.session.post(
                self.api_url,
                headers=headers,
                json=json_data,
                timeout=30
            )
            
            if response.status_code == 200:
                response_json = response.json()
                data_all = response_json.get("attractionList")
                return data_all if data_all else []
            else:
                logger.error(f"API请求失败，状态码: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"API请求异常: {str(e)}")
            return []
    
    def crawl_info(self, spot_id, spot_name):
        """爬取景区基本信息"""
        logger.info(f"开始爬取景区信息: {spot_name}")
        
        try:
            # 获取第一页数据
            data_all = self._crawling_external(1)
            
            if not data_all:
                return None
            
            # 查找目标景区
            for data in data_all:
                card = data.get("card", {})
                poi_name = card.get("poiName", '')
                
                if spot_name in poi_name or poi_name in spot_name:
                    business_id = card.get("businessId")
                    zone_name = card.get("zoneName")
                    comment_score = card.get("commentScore")
                    market_price = card.get("marketPrice")
                    is_free = card.get("isFree")
                    short_features = card.get("shortFeatures")
                    sight_level = card.get("sightLevelStr")
                    
                    coordinate = card.get("coordinate", {})
                    
                    logger.info(f"找到景区: {poi_name}")
                    
                    return {
                        'spot_id': str(business_id) if business_id else '',
                        'spot_name': poi_name,
                        'address': zone_name or '',
                        'rating': float(comment_score) if comment_score else 0,
                        'price': str(market_price) if market_price else ('免费' if is_free else '暂无'),
                        'opening_hours': '请查询官方',
                        'phone': '',
                        'description': short_features or '',
                        'latitude': coordinate.get('latitude', 0),
                        'longitude': coordinate.get('longitude', 0),
                        'level': sight_level or '',
                        'data_source': 'ctrip',
                        'crawl_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    }
            
            logger.warning(f"未找到景区: {spot_name}")
            return None
            
        except Exception as e:
            logger.error(f"爬取景区信息失败: {str(e)}")
            return None
