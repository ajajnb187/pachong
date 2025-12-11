"""
爬虫基类
实现核心的反爬策略和通用方法
"""
import requests
import random
import time
from abc import ABC, abstractmethod
from fake_useragent import UserAgent
from config import Config
from utils.logger import logger

class BaseCrawler(ABC):
    """爬虫基类"""
    
    def __init__(self):
        """初始化爬虫"""
        self.session = requests.Session()
        self.config = Config()
        self.ua = UserAgent()
        self.request_count = 0  # 请求计数器，用于代理轮换
        
        # 初始化代理（如果启用）
        if self.config.USE_PROXY:
            self._init_proxy()
            logger.info("代理模式已启用")
    
    def _init_proxy(self):
        """初始化代理配置"""
        if self.config.PROXY_SERVER and self.config.PROXY_USERNAME and self.config.PROXY_PASSWORD:
            # 构造代理URL: http://username:password@host:port
            proxy_url = f"{self.config.PROXY_SERVER}"
            if self.config.PROXY_USERNAME:
                # 提取host和port
                server_parts = self.config.PROXY_SERVER.replace('http://', '').replace('https://', '')
                proxy_url = f"http://{self.config.PROXY_USERNAME}:{self.config.PROXY_PASSWORD}@{server_parts}"
            
            self.proxies = {
                'http': proxy_url,
                'https': proxy_url
            }
            logger.info(f"代理配置完成: {self.config.PROXY_SERVER}")
        else:
            self.proxies = None
            logger.warning("代理配置不完整，将不使用代理")
    
    def get_headers(self, custom_headers=None):
        """
        获取请求头，包含随机UA和设备指纹
        
        Args:
            custom_headers: 自定义请求头
            
        Returns:
            dict: 请求头字典
        """
        headers = {
            'User-Agent': self.ua.random if hasattr(self, 'ua') else random.choice(self.config.USER_AGENTS),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1'
        }
        
        # 合并自定义请求头
        if custom_headers:
            headers.update(custom_headers)
        
        return headers
    
    def request_with_retry(self, url, method='GET', **kwargs):
        """
        带重试机制的HTTP请求
        
        Args:
            url: 请求URL
            method: 请求方法 (GET/POST)
            **kwargs: requests库的其他参数
            
        Returns:
            Response: 响应对象，失败返回None
        """
        # 请求计数+1，用于代理轮换
        self.request_count += 1
        
        # 判断是否需要更换代理
        if (self.config.USE_PROXY and 
            self.proxies and 
            self.request_count % self.config.PROXY_CHANGE_INTERVAL == 0):
            logger.info(f"已完成{self.request_count}次请求，建议检查代理状态")
        
        for retry in range(self.config.CRAWLER_MAX_RETRIES):
            try:
                # 合并请求头
                if 'headers' not in kwargs:
                    kwargs['headers'] = self.get_headers()
                else:
                    kwargs['headers'] = self.get_headers(kwargs['headers'])
                
                # 设置超时
                if 'timeout' not in kwargs:
                    kwargs['timeout'] = self.config.CRAWLER_TIMEOUT
                
                # 设置代理
                if self.config.USE_PROXY and self.proxies:
                    kwargs['proxies'] = self.proxies
                
                # 发送请求
                if method.upper() == 'GET':
                    response = self.session.get(url, **kwargs)
                elif method.upper() == 'POST':
                    response = self.session.post(url, **kwargs)
                else:
                    raise ValueError(f"不支持的请求方法: {method}")
                
                # 检查响应状态
                if response.status_code == 200:
                    logger.debug(f"请求成功: {url}")
                    return response
                elif response.status_code == 403:
                    logger.warning(f"请求被拒绝(403): {url}，可能触发反爬机制")
                elif response.status_code == 404:
                    logger.warning(f"页面不存在(404): {url}")
                    return None  # 404不重试
                else:
                    logger.warning(f"请求失败，状态码: {response.status_code}, URL: {url}")
                
            except requests.exceptions.Timeout:
                logger.warning(f"请求超时 (重试 {retry + 1}/{self.config.CRAWLER_MAX_RETRIES}): {url}")
            except requests.exceptions.ConnectionError:
                logger.warning(f"连接错误 (重试 {retry + 1}/{self.config.CRAWLER_MAX_RETRIES}): {url}")
            except Exception as e:
                logger.error(f"请求异常 (重试 {retry + 1}/{self.config.CRAWLER_MAX_RETRIES}): {str(e)}, URL: {url}")
            
            # 重试前延迟
            if retry < self.config.CRAWLER_MAX_RETRIES - 1:
                delay = self.config.CRAWLER_REQUEST_DELAY_MAX * (retry + 1)
                logger.info(f"等待 {delay} 秒后重试...")
                time.sleep(delay)
        
        logger.error(f"请求失败，已重试{self.config.CRAWLER_MAX_RETRIES}次: {url}")
        return None
    
    def delay(self, min_delay=None, max_delay=None):
        """
        随机延迟，模拟人类行为
        
        Args:
            min_delay: 最小延迟时间(秒)，默认使用配置值
            max_delay: 最大延迟时间(秒)，默认使用配置值
        """
        min_d = min_delay if min_delay is not None else self.config.CRAWLER_REQUEST_DELAY_MIN
        max_d = max_delay if max_delay is not None else self.config.CRAWLER_REQUEST_DELAY_MAX
        
        delay_time = random.uniform(min_d, max_d)
        logger.debug(f"延迟 {delay_time:.2f} 秒")
        time.sleep(delay_time)
    
    def extract_text(self, element):
        """
        从BeautifulSoup元素中提取文本
        
        Args:
            element: BeautifulSoup元素
            
        Returns:
            str: 提取的文本，失败返回空字符串
        """
        try:
            if element:
                return element.text.strip()
            return ''
        except:
            return ''
    
    def extract_attr(self, element, attr):
        """
        从BeautifulSoup元素中提取属性
        
        Args:
            element: BeautifulSoup元素
            attr: 属性名
            
        Returns:
            str: 属性值，失败返回空字符串
        """
        try:
            if element and element.has_attr(attr):
                return element[attr]
            return ''
        except:
            return ''
    
    @abstractmethod
    def search_scenic_spot(self, spot_name):
        """
        搜索景区，获取景区ID
        
        Args:
            spot_name: 景区名称
            
        Returns:
            str: 景区ID，失败返回None
        """
        pass
    
    @abstractmethod
    def crawl_reviews(self, spot_id, spot_name, target_count):
        """
        爬取评价数据
        
        Args:
            spot_id: 景区ID
            spot_name: 景区名称
            target_count: 目标爬取数量
            
        Yields:
            dict: 评价数据
        """
        pass
    
    @abstractmethod
    def crawl_info(self, spot_id, spot_name):
        """
        爬取景区基本信息
        
        Args:
            spot_id: 景区ID
            spot_name: 景区名称
            
        Returns:
            dict: 景区信息，失败返回None
        """
        pass
