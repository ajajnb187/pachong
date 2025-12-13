"""
Redis缓存清除辅助工具
当爬虫完成数据采集后，清除Spring Boot应用的Redis缓存
"""
import redis
from utils.logger import logger

class RedisCacheHelper:
    """Redis缓存管理助手"""
    
    def __init__(self, host='localhost', port=6379, password=None, db=0):
        """
        初始化Redis连接
        """
        try:
            self.client = redis.Redis(
                host=host,
                port=port,
                password=password,
                db=db,
                decode_responses=True
            )
            # 测试连接
            self.client.ping()
            logger.info(f"✅ Redis连接成功: {host}:{port}")
        except Exception as e:
            logger.warning(f"⚠️  Redis连接失败: {e}，缓存清除功能将不可用")
            self.client = None
    
    def clear_scenic_cache(self):
        """清除所有景区相关缓存"""
        if not self.client:
            logger.warning("Redis未连接，跳过缓存清除")
            return
        
        try:
            # 清除景区列表和详情缓存
            keys = self.client.keys('scenic:*')
            if keys:
                deleted = self.client.delete(*keys)
                logger.info(f"🗑️  已清除 {deleted} 个景区缓存key")
            else:
                logger.info("📝 没有找到景区缓存需要清除")
        except Exception as e:
            logger.error(f"❌ 清除景区缓存失败: {e}")
    
    def clear_analysis_cache(self):
        """清除所有分析相关缓存"""
        if not self.client:
            logger.warning("Redis未连接，跳过缓存清除")
            return
        
        try:
            # 清除数据分析缓存
            keys = self.client.keys('analysis:*')
            if keys:
                deleted = self.client.delete(*keys)
                logger.info(f"🗑️  已清除 {deleted} 个分析缓存key")
            else:
                logger.info("📝 没有找到分析缓存需要清除")
        except Exception as e:
            logger.error(f"❌ 清除分析缓存失败: {e}")
    
    def clear_all_cache(self):
        """清除所有相关缓存"""
        logger.info("🧹 开始清除所有旅游数据缓存...")
        self.clear_scenic_cache()
        self.clear_analysis_cache()
        logger.info("✨ 缓存清除完成！")

# 创建全局Redis助手实例
redis_helper = RedisCacheHelper()
