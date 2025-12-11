"""
数据清洗工具
"""
import re
import json
from datetime import datetime
from utils.logger import logger

class DataCleaner:
    """数据清洗工具类"""
    
    @staticmethod
    def clean_review_data(raw_data):
        """
        清洗评价数据
        
        Args:
            raw_data: 原始数据字典
            
        Returns:
            dict: 清洗后的数据，失败返回None
        """
        try:
            cleaned_data = {
                'scenic_spot': DataCleaner.clean_text(raw_data.get('scenic_spot', '')),
                'city': DataCleaner.clean_text(raw_data.get('city', '福州')),
                'rating': DataCleaner.validate_rating(raw_data.get('rating')),
                'visitor_name': DataCleaner.clean_text(raw_data.get('visitor_name', '匿名用户')),
                'review_content': DataCleaner.clean_text(raw_data.get('review_content', '')),
                'travel_date': DataCleaner.parse_date(raw_data.get('travel_date')),
                'review_date': DataCleaner.parse_date(raw_data.get('review_date')),
                'data_source': raw_data.get('data_source', ''),
                'crawl_time': raw_data.get('crawl_time', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            }
            
            # 验证必填字段
            if not cleaned_data['scenic_spot']:
                logger.warning("景区名称为空，跳过该数据")
                return None
            
            return cleaned_data
            
        except Exception as e:
            logger.error(f"清洗评价数据失败: {str(e)}, 原始数据: {raw_data}")
            return None
    
    @staticmethod
    def clean_scenic_info_data(raw_data):
        """
        清洗景区信息数据
        
        Args:
            raw_data: 原始数据字典
            
        Returns:
            dict: 清洗后的数据，失败返回None
        """
        try:
            cleaned_data = {
                'spot_id': raw_data.get('spot_id', ''),
                'spot_name': DataCleaner.clean_text(raw_data.get('spot_name', '')),
                'spot_type': raw_data.get('spot_type', ''),
                'location': DataCleaner.clean_text(raw_data.get('location', '')),
                'address': DataCleaner.clean_text(raw_data.get('address', '')),
                'longitude': float(raw_data.get('longitude', 0)) if raw_data.get('longitude') else None,
                'latitude': float(raw_data.get('latitude', 0)) if raw_data.get('latitude') else None,
                'open_time': raw_data.get('open_time', ''),
                'ticket_price': DataCleaner.validate_price(raw_data.get('ticket_price')),
                'description': DataCleaner.clean_text(raw_data.get('description', '')),
                'images': raw_data.get('images', '[]') if isinstance(raw_data.get('images'), str) else json.dumps(raw_data.get('images', []), ensure_ascii=False),
                'contact_phone': raw_data.get('contact_phone', ''),
                'official_website': raw_data.get('official_website', ''),
                'rating': DataCleaner.validate_rating(raw_data.get('rating')),
                'data_source': raw_data.get('data_source', ''),
                'crawl_time': raw_data.get('crawl_time', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            }
            
            # 验证必填字段
            if not cleaned_data['spot_name']:
                logger.warning("景区名称为空，跳过该数据")
                return None
            
            return cleaned_data
            
        except Exception as e:
            logger.error(f"清洗景区信息失败: {str(e)}, 原始数据: {raw_data}")
            return None
    
    @staticmethod
    def clean_text(text):
        """
        清洗文本
        
        Args:
            text: 原始文本
            
        Returns:
            str: 清洗后的文本
        """
        if not text:
            return ''
        
        # 转换为字符串
        text = str(text)
        
        # 去除多余空格和换行
        text = re.sub(r'\s+', ' ', text)
        
        # 去除特殊字符（保留中文、英文、数字和常用标点）
        text = re.sub(r'[^\w\s\u4e00-\u9fff，。！？、；：""''《》（）【】\-—.!?,;:()\[\]]', '', text)
        
        # 去除首尾空格
        text = text.strip()
        
        return text
    
    @staticmethod
    def validate_rating(rating):
        """
        验证评分
        
        Args:
            rating: 评分值
            
        Returns:
            float: 验证后的评分（1-5分），无效值返回5.0
        """
        try:
            rating = float(rating)
            if 1 <= rating <= 5:
                return round(rating, 1)
            return 5.0
        except:
            return 5.0
    
    @staticmethod
    def validate_price(price):
        """
        验证价格
        
        Args:
            price: 价格值
            
        Returns:
            float: 验证后的价格，无效值返回0
        """
        try:
            # 提取数字
            if isinstance(price, str):
                numbers = re.findall(r'\d+\.?\d*', price)
                if numbers:
                    return float(numbers[0])
            return float(price)
        except:
            return 0.0
    
    @staticmethod
    def parse_date(date_str):
        """
        解析日期
        
        Args:
            date_str: 日期字符串
            
        Returns:
            str: 格式化后的日期（YYYY-MM-DD）
        """
        if not date_str:
            return datetime.now().strftime('%Y-%m-%d')
        
        try:
            # 尝试多种日期格式
            formats = [
                '%Y-%m-%d',
                '%Y/%m/%d',
                '%Y年%m月%d日',
                '%Y.%m.%d',
                '%Y-%m-%d %H:%M:%S'
            ]
            
            for fmt in formats:
                try:
                    dt = datetime.strptime(str(date_str), fmt)
                    return dt.strftime('%Y-%m-%d')
                except:
                    continue
            
            # 如果都不匹配，尝试提取数字
            numbers = re.findall(r'\d+', str(date_str))
            if len(numbers) >= 3:
                year, month, day = numbers[0], numbers[1], numbers[2]
                dt = datetime(int(year), int(month), int(day))
                return dt.strftime('%Y-%m-%d')
            
            return datetime.now().strftime('%Y-%m-%d')
            
        except Exception as e:
            logger.warning(f"日期解析失败: {date_str}, {str(e)}")
            return datetime.now().strftime('%Y-%m-%d')
    
    @staticmethod
    def _generate_id():
        """生成唯一ID"""
        import uuid
        return str(uuid.uuid4())
    
    @staticmethod
    def extract_location_parts(location):
        """
        从地址中提取省份和城市
        
        Args:
            location: 地址字符串，如"福建省福州市"
            
        Returns:
            dict: {'province': '福建省', 'city': '福州市'}
        """
        province = ''
        city = ''
        
        if not location:
            return {'province': '', 'city': ''}
        
        # 提取省份
        province_match = re.search(r'([\u4e00-\u9fff]+省|[\u4e00-\u9fff]+自治区|[\u4e00-\u9fff]+特别行政区)', location)
        if province_match:
            province = province_match.group(1)
        
        # 提取城市
        city_match = re.search(r'([\u4e00-\u9fff]+市|[\u4e00-\u9fff]+县|[\u4e00-\u9fff]+区)', location)
        if city_match:
            city = city_match.group(1)
        
        return {'province': province, 'city': city}
