"""
携程爬虫 V2 - 完整重构版
分离景点数据和评论数据，正确对应Hive表结构

Hive表设计：
1. scenic_spots: 景点基本信息表
   - scenic_spot, city, review_count, avg_rating, last_review_date
   
2. fuzhou_reviews: 评论数据表
   - scenic_spot, city, rating, visitor_name, review_content, 
     travel_date, review_date, data_source, crawl_time
"""
import time
import json
import requests
import re
from datetime import datetime
from utils.logger import logger
from config import Config

class CtripCrawlerV2:
    """携程爬虫V2 - 正确分离景点和评论数据"""
    
    def __init__(self):
        self.config = Config()
        self.api_url = "https://m.ctrip.com/restapi/soa2/18109/json/getAttractionList"
        self.comment_api = "https://m.ctrip.com/restapi/soa2/13444/json/getCommentCollapseList"
        self.fuzhou_city_id = 164
        self.session = requests.session()
        logger.info(f"携程爬虫V2初始化完成（福州城市ID: {self.fuzhou_city_id}）")
    
    def crawl_all_scenic_spots(self, max_spots=500, max_pages=100):
        """
        爬取福州景点基本信息 -> scenic_spots表
        
        Args:
            max_spots: 最多爬取景点数量（达到即停止）
            max_pages: 最多爬取页数
            
        Returns:
            list: 景点数据列表，每个元素包含景点基本信息
        """
        logger.info(f"开始爬取福州景点数据，目标{max_spots}个景点")
        
        all_spots = []
        page = 1
        
        while page <= max_pages and len(all_spots) < max_spots:
            try:
                logger.info(f"正在爬取景点列表第 {page} 页... (已获取{len(all_spots)}/{max_spots})")
                
                # 调用景点列表API
                spots_data = self._fetch_spots_page(page)
                
                if not spots_data or len(spots_data) == 0:
                    logger.info(f"第{page}页无数据，景点爬取完成")
                    break
                
                logger.info(f"第{page}页获取到 {len(spots_data)} 个景点")
                
                # 处理每个景点
                for spot_data in spots_data:
                    if len(all_spots) >= max_spots:
                        logger.info(f"已达到目标数量{max_spots}，停止爬取")
                        break
                    
                    try:
                        spot_info = self._parse_spot_info(spot_data)
                        if spot_info:
                            all_spots.append(spot_info)
                    except Exception as e:
                        logger.warning(f"解析景点数据失败: {str(e)}")
                        continue
                
                if len(all_spots) >= max_spots:
                    break
                
                page += 1
                time.sleep(2)  # 延迟避免请求过快
                
            except Exception as e:
                logger.error(f"爬取第{page}页时出错: {str(e)}")
                break
        
        logger.info(f"景点数据爬取完成: 共 {len(all_spots)} 个景点")
        return all_spots
    
    def crawl_reviews_for_spot(self, spot_id, spot_name, max_reviews=50):
        """
        爬取指定景点的用户评论 -> fuzhou_reviews表
        
        Args:
            spot_id: 景点ID
            spot_name: 景点名称
            max_reviews: 最多爬取评论数
            
        Returns:
            list: 评论数据列表
        """
        logger.info(f"开始爬取景点【{spot_name}】的用户评论，目标{max_reviews}条")
        
        reviews = []
        page = 1
        page_size = 10
        max_pages = (max_reviews // page_size) + 1
        
        while len(reviews) < max_reviews and page <= max_pages:
            try:
                # 调用评论API
                page_reviews = self._fetch_reviews_page(spot_id, spot_name, page, page_size)
                
                if not page_reviews:
                    break
                
                reviews.extend(page_reviews)
                logger.info(f"【{spot_name}】已爬取 {len(reviews)}/{max_reviews} 条评论")
                
                page += 1
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"爬取【{spot_name}】评论失败: {str(e)}")
                break
        
        return reviews[:max_reviews]
    
    def _fetch_spots_page(self, page):
        """获取景点列表某一页的数据"""
        headers = {
            'accept': '*/*',
            'accept-language': 'zh-CN,zh;q=0.9',
            'content-type': 'application/json',
            'origin': 'https://you.ctrip.com',
            'referer': 'https://you.ctrip.com/',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        }
        
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
            'districtId': self.fuzhou_city_id,
            'index': page,
            'sortType': 1,
            'count': 10,
            'filter': {'filterItems': []},
            'coordinate': {
                'latitude': 26.0745,
                'longitude': 119.2965,
                'coordinateType': 'WGS84',
            },
            'returnModuleType': 'all',
        }
        
        response = self.session.post(
            self.api_url,
            headers=headers,
            json=json_data,
            timeout=30
        )
        
        if response.status_code == 200:
            response_json = response.json()
            return response_json.get("attractionList", [])
        
        return []
    
    def _parse_spot_info(self, data):
        """
        解析景点完整信息 - 参考携程旅行代码
        
        返回完整景点字段（参考main.py第156-202行）：
        businessId, zone_name, poi_name, comment_score, sight_level, 
        cover_image_url, tag_name_list, market_price, is_free, 
        short_features, sight_category_info, latitude, longitude, heat_score
        """
        card = data.get("card", {})
        
        # 基础字段
        business_id = card.get("businessId")
        poi_name = card.get("poiName")
        
        if not poi_name:
            return None
        
        # 位置信息
        coordinate = card.get("coordinate", {})
        
        # 构造完整景点数据（参考携程旅行main.py）
        spot_info = {
            # 基础信息
            'business_id': business_id,
            'scenic_spot': poi_name,
            'city': '福州',
            'zone_name': card.get("zoneName", ""),
            
            # 评分相关
            'comment_score': float(card.get("commentScore")) if card.get("commentScore") else 0.0,
            'heat_score': float(card.get("heatScore")) if card.get("heatScore") else 0.0,
            
            # 分类标签
            'sight_level': card.get("sightLevelStr", ""),
            'tag_name_list': str(card.get("tagNameList", [])),
            'sight_category_info': str(card.get("sightCategoryInfo", "")),
            
            # 图片
            'cover_image_url': card.get("coverImageUrl", ""),
            
            # 价格
            'market_price': card.get("marketPrice", ""),
            'is_free': str(card.get("isFree", False)),
            
            # 描述（转为字符串）
            'short_features': str(card.get("shortFeatures", [])),
            
            # 坐标
            'latitude': coordinate.get("latitude", 0.0),
            'longitude': coordinate.get("longitude", 0.0),
            
            # 详情链接（用于后续爬取）
            'detail_url': card.get("detailUrl", ""),
            
            # 时间戳
            'crawl_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # 存储spot_id用于后续爬评论
        spot_info['_spot_id'] = business_id
        
        return spot_info
    
    def _fetch_reviews_page(self, spot_id, spot_name, page, page_size):
        """获取某景点评论的某一页数据"""
        payload = {
            "arg": {
                "businessType": 2,
                "resourceId": int(spot_id),
                "resourceType": 11,
                "pageIndex": page,
                "pageSize": page_size,
                "sortType": 3,
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
            'Referer': 'https://m.ctrip.com/'
        }
        
        response = self.session.post(
            self.comment_api,
            json=payload,
            headers=headers,
            timeout=15
        )
        
        if response.status_code != 200:
            return []
        
        data = response.json()
        
        if not data or 'result' not in data:
            return []
        
        items = data.get('result', {}).get('items', [])
        reviews = []
        
        for item in items:
            try:
                review = self._parse_review(item, spot_name)
                if review:
                    reviews.append(review)
            except Exception as e:
                logger.debug(f"解析评论失败: {str(e)}")
                continue
        
        return reviews
    
    def _parse_review(self, item, spot_name):
        """
        解析评论数据 -> fuzhou_reviews表格式
        
        返回格式：
        {
            'scenic_spot': '景点名',
            'city': '福州',
            'rating': 评分,
            'visitor_name': '游客名',
            'review_content': '评论内容',
            'travel_date': '旅游日期',
            'review_date': '评论日期',
            'data_source': 'ctrip',
            'crawl_time': '爬取时间'
        }
        """
        content = item.get('content', '').strip()
        if len(content) < 5:  # 过滤太短的评论
            return None
        
        # 用户信息
        user_info = item.get('userInfo', {})
        user_name = user_info.get('userNick', '携程用户')
        
        # 评分
        rating = float(item.get('score', 5.0))
        
        # 日期解析
        publish_time = item.get('publishTime', '')
        publish_tag = item.get('publishTypeTag', '')
        review_date = self._parse_date(publish_time, publish_tag)
        travel_date = review_date  # 使用评论时间作为旅游时间
        
        review = {
            'scenic_spot': spot_name,
            'city': '福州',
            'rating': rating,
            'visitor_name': user_name,
            'review_content': content[:500],  # 限制长度
            'travel_date': travel_date,
            'review_date': review_date,
            'data_source': 'ctrip',
            'crawl_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        return review
    
    def _parse_date(self, date_str, tag_str=''):
        """解析携程日期格式"""
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
        
        return datetime.now().strftime('%Y-%m-%d')
