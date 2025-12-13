# Redis缓存使用说明

## 缓存策略

### 1. 缓存Key设计
- **景区列表**: `scenic:list:{page}:{pageSize}:{keyword}`
- **景区详情**: `scenic:detail:{spotName}`
- **数据分析**: `analysis:{methodName}:{params...}`

### 2. 缓存过期时间
- 默认TTL: 1小时 (3600秒)
- 数据查询缓存可根据业务调整

### 3. 缓存清除策略
当Flask爬虫完成数据采集并上传到HDFS后，会自动清除相关Redis缓存：
- 清除所有景区相关缓存: `scenic:*`
- 清除所有分析相关缓存: `analysis:*`

## 实现说明

### Spring Boot端
1. **RedisConfig**: Redis连接和序列化配置
2. **RedisCacheService**: 统一的缓存服务，提供增删查改接口
3. **Service层**: 在查询前先检查缓存，查询后写入缓存

### Flask端
在数据上传完成后调用Redis清除接口：
```python
import redis

redis_client = redis.Redis(host='localhost', port=6379, password='redis123456', db=0)

# 清除景区数据缓存
redis_client.delete('scenic:*')
redis_client.delete('analysis:*')
```

## 使用效果
- 首次查询: 直接从Hive查询，耗时较长
- 后续查询: 从Redis读取，响应时间<10ms
- 数据更新: 爬虫完成后自动清除缓存，下次查询获取最新数据
