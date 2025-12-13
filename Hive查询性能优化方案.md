# Hive查询性能优化方案

## 🔍 当前性能问题

**现象**: Hive查询需要3-4秒才能返回结果，影响用户体验

**原因分析**:
1. **MapReduce启动开销**: Hive默认使用MapReduce引擎，每次查询都要启动MR任务
2. **小数据量问题**: 当前数据量仅90条评论，不适合分布式计算
3. **未启用本地模式**: 小数据查询应该走本地模式而非集群模式
4. **缺少索引和统计信息**: 表统计信息未更新
5. **跨表JOIN**: `scenic_spots_latest` 和 `fuzhou_reviews` 的JOIN增加延迟

---

## ✅ 优化方案

### 方案一：启用Hive本地模式 ⭐⭐⭐⭐⭐

**适用场景**: 数据量小于128MB且少于4个文件

#### 1. 修改Hive配置
在SpringBoot连接Hive时自动设置本地模式：

```java
// ScenicAnalysisServiceImpl.java
@PostConstruct
public void initHiveLocalMode() {
    try {
        // 启用Hive本地模式（自动判断）
        hiveJdbcTemplate.execute("SET hive.exec.mode.local.auto=true");
        
        // 设置本地模式的数据量阈值（128MB）
        hiveJdbcTemplate.execute("SET hive.exec.mode.local.auto.inputbytes.max=134217728");
        
        // 设置本地模式的文件数阈值（4个文件）
        hiveJdbcTemplate.execute("SET hive.exec.mode.local.auto.input.files.max=4");
        
        // 启用fetch任务优化（简单查询直接fetch，不启动MR）
        hiveJdbcTemplate.execute("SET hive.fetch.task.conversion=more");
        
        // 启用并行执行
        hiveJdbcTemplate.execute("SET hive.exec.parallel=true");
        
        log.info("Hive本地模式优化配置已启用");
    } catch (Exception e) {
        log.warn("Hive本地模式配置失败，将使用默认配置", e);
    }
}
```

**预期效果**: 查询时间从3-4秒降至0.5-1秒 ⚡

---

### 方案二：优化查询SQL ⭐⭐⭐⭐

#### 1. 减少JOIN操作
```sql
-- 优化前：每次查询都JOIN两张表
SELECT s.*, COUNT(r.*) 
FROM scenic_spots_latest s 
LEFT JOIN fuzhou_reviews r ON s.scenic_spot = r.scenic_spot
GROUP BY ...

-- 优化后：直接查询单表
SELECT scenic_spot, COUNT(*) as review_count
FROM fuzhou_reviews
GROUP BY scenic_spot
```

#### 2. 使用分区裁剪
```sql
-- 如果查询涉及时间范围，使用分区过滤
SELECT * FROM fuzhou_reviews 
WHERE dt = '20251213_170012'  -- 只扫描特定分区
AND travel_date >= '2024-01-01'
```

#### 3. 避免SELECT *
```sql
-- 优化前
SELECT * FROM fuzhou_reviews

-- 优化后：只查询需要的字段
SELECT scenic_spot, rating, visitor_name
FROM fuzhou_reviews
```

---

### 方案三：使用Hive视图预聚合 ⭐⭐⭐

在Hive中创建预聚合视图，减少实时计算：

```sql
-- 创建景区统计视图
CREATE VIEW IF NOT EXISTS scenic_review_stats AS
SELECT 
    scenic_spot,
    COUNT(*) as review_count,
    ROUND(AVG(rating), 1) as avg_rating,
    COUNT(DISTINCT visitor_name) as visitor_count,
    MIN(travel_date) as first_review_date,
    MAX(travel_date) as last_review_date
FROM tourism_db.fuzhou_reviews
GROUP BY scenic_spot;

-- 查询时直接使用视图
SELECT * FROM tourism_db.scenic_review_stats
WHERE scenic_spot = '三坊七巷';
```

**注意**: Hive视图不是物化视图，仍需实时计算，但SQL更简洁。

---

### 方案四：缓存查询结果 ⭐⭐⭐⭐

在SpringBoot中使用Redis缓存热点数据：

```java
@Service
public class ScenicAnalysisServiceImpl {
    
    @Autowired
    private RedisTemplate<String, Object> redisTemplate;
    
    @Cacheable(value = "scenic:ranking", key = "#rankType + ':' + #limit", unless = "#result == null")
    public List<Map<String, Object>> getScenicRanking(String rankType, Integer limit) {
        // Hive查询逻辑
        return hiveJdbcTemplate.query(...);
    }
    
    @CacheEvict(value = "scenic:*", allEntries = true)
    public void refreshCache() {
        log.info("缓存已清空，下次查询将重新从Hive获取");
    }
}
```

**配置Redis缓存**:
```yaml
# application.yml
spring:
  cache:
    type: redis
  redis:
    host: localhost
    port: 6379
    timeout: 3000ms
    cache-expire: 1800  # 30分钟过期
```

**预期效果**: 缓存命中后查询时间 < 100ms 🚀

---

### 方案五：升级到Spark执行引擎 ⭐⭐⭐⭐⭐

**长期方案**: 将Hive从MapReduce引擎切换到Spark引擎

#### 1. 修改Hive配置
```bash
# 进入hive-server容器
docker exec -it hive-server bash

# 配置Spark为执行引擎
hive --hiveconf hive.execution.engine=spark
```

#### 2. Docker Compose添加Spark支持
```yaml
# docker-compose.yml
services:
  spark-master:
    image: bitnami/spark:3.3.0
    environment:
      - SPARK_MODE=master
    ports:
      - "8090:8080"
      - "7077:7077"
  
  spark-worker:
    image: bitnami/spark:3.3.0
    environment:
      - SPARK_MODE=worker
      - SPARK_MASTER_URL=spark://spark-master:7077
```

#### 3. 修改Hive配置连接Spark
```xml
<!-- hive-site.xml -->
<property>
    <name>hive.execution.engine</name>
    <value>spark</value>
</property>
<property>
    <name>spark.master</name>
    <value>spark://spark-master:7077</value>
</property>
```

**预期效果**: 查询时间降至1秒内 ⚡⚡

**优点**:
- 内存计算，速度快
- DAG优化，减少磁盘I/O
- 适合迭代查询

**缺点**:
- 需要额外资源（Spark集群）
- 配置复杂度增加

---

### 方案六：使用Presto/Impala作为查询引擎 ⭐⭐⭐⭐

**替代方案**: 使用专门的交互式查询引擎

#### Presto优势
- 专为低延迟交互式查询设计
- 纯内存计算，无MapReduce开销
- 支持SQL on Hadoop
- 查询速度比Hive快10-100倍

#### 集成方式
```yaml
# docker-compose.yml
services:
  presto-coordinator:
    image: prestodb/presto:latest
    ports:
      - "8089:8080"
    volumes:
      - ./presto/config:/opt/presto-server/etc
```

#### SpringBoot集成Presto
```java
@Configuration
public class PrestoConfig {
    @Bean
    public DataSource prestoDataSource() {
        DriverManagerDataSource dataSource = new DriverManagerDataSource();
        dataSource.setDriverClassName("com.facebook.presto.jdbc.PrestoDriver");
        dataSource.setUrl("jdbc:presto://localhost:8089/hive/tourism_db");
        return dataSource;
    }
}
```

**预期效果**: 查询时间 < 1秒 🚀

---

## 📊 性能对比

| 优化方案 | 查询时间 | 实施难度 | 推荐指数 |
|---------|---------|---------|---------|
| **当前（MapReduce）** | 3-4秒 | - | ⭐ |
| **启用本地模式** | 0.5-1秒 | 简单 | ⭐⭐⭐⭐⭐ |
| **优化SQL** | 1-2秒 | 简单 | ⭐⭐⭐⭐ |
| **Redis缓存** | <100ms（缓存命中） | 中等 | ⭐⭐⭐⭐ |
| **Hive视图** | 2-3秒 | 简单 | ⭐⭐⭐ |
| **Spark引擎** | <1秒 | 复杂 | ⭐⭐⭐⭐⭐ |
| **Presto引擎** | <500ms | 复杂 | ⭐⭐⭐⭐ |

---

## 🎯 推荐实施路线

### 阶段一：立即优化（0成本）✅
1. ✅ **启用Hive本地模式** - 在`ScenicAnalysisServiceImpl`添加`@PostConstruct`初始化
2. ✅ **优化SQL查询** - 减少JOIN，只查询必要字段
3. ✅ **使用分区过滤** - 查询时指定`dt`分区

**预期**: 查询时间降至1秒内

### 阶段二：缓存优化（1-2天）
1. 集成Redis缓存
2. 为热点查询添加`@Cacheable`注解
3. 定时刷新缓存（每30分钟）

**预期**: 缓存命中率80%+，查询时间<100ms

### 阶段三：引擎升级（1-2周，可选）
1. 评估数据量增长趋势
2. 如果未来数据量>10万条，考虑升级到Spark
3. 如果需要实时查询，考虑引入Presto

---

## 💻 代码实现

### 1. 启用Hive本地模式优化

```java
package com.tourism.tourismspringboot.service.impl;

import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;
import javax.annotation.PostConstruct;

@Slf4j
@Service
public class ScenicAnalysisServiceImpl implements IScenicAnalysisService {

    @Autowired
    @Qualifier("hiveJdbcTemplate")
    private JdbcTemplate hiveJdbcTemplate;
    
    /**
     * 初始化Hive性能优化配置
     * 在Service启动时自动执行
     */
    @PostConstruct
    public void initHiveOptimization() {
        try {
            log.info("开始配置Hive性能优化参数...");
            
            // 1. 启用本地模式（小数据量自动使用本地模式）
            hiveJdbcTemplate.execute("SET hive.exec.mode.local.auto=true");
            hiveJdbcTemplate.execute("SET hive.exec.mode.local.auto.inputbytes.max=134217728"); // 128MB
            hiveJdbcTemplate.execute("SET hive.exec.mode.local.auto.input.files.max=4");
            
            // 2. Fetch任务转换（简单查询直接fetch，不启动MR任务）
            hiveJdbcTemplate.execute("SET hive.fetch.task.conversion=more");
            hiveJdbcTemplate.execute("SET hive.fetch.task.conversion.threshold=1073741824"); // 1GB
            
            // 3. 并行执行优化
            hiveJdbcTemplate.execute("SET hive.exec.parallel=true");
            hiveJdbcTemplate.execute("SET hive.exec.parallel.thread.number=8");
            
            // 4. JVM重用（减少JVM启动开销）
            hiveJdbcTemplate.execute("SET mapreduce.job.jvm.numtasks=10");
            
            // 5. 压缩输出（减少网络传输）
            hiveJdbcTemplate.execute("SET hive.exec.compress.intermediate=true");
            hiveJdbcTemplate.execute("SET hive.exec.compress.output=true");
            
            // 6. 谓词下推（减少数据扫描量）
            hiveJdbcTemplate.execute("SET hive.optimize.ppd=true");
            
            // 7. 列裁剪（只读取需要的列）
            hiveJdbcTemplate.execute("SET hive.optimize.cp=true");
            
            log.info("✅ Hive性能优化配置完成");
            
        } catch (Exception e) {
            log.warn("⚠️ Hive性能优化配置失败，将使用默认配置: {}", e.getMessage());
        }
    }
}
```

### 2. 优化景区排行榜查询

```java
@Override
public List<Map<String, Object>> getScenicRanking(String rankType, Integer limit) {
    log.info("查询景区排行榜: rankType={}, limit={}", rankType, limit);

    String sql;
    
    if ("visitor".equals(rankType)) {
        // 游客流量：直接从fuzhou_reviews统计，不JOIN
        sql = 
            "SELECT " +
            "    scenic_spot, " +
            "    COUNT(DISTINCT visitor_name) as visitor_count " +
            "FROM tourism_db.fuzhou_reviews " +
            "GROUP BY scenic_spot " +
            "ORDER BY visitor_count DESC " +
            "LIMIT " + limit;
    } else if ("review".equals(rankType)) {
        // 评论体量
        sql = 
            "SELECT " +
            "    scenic_spot, " +
            "    COUNT(*) as review_count " +
            "FROM tourism_db.fuzhou_reviews " +
            "GROUP BY scenic_spot " +
            "ORDER BY review_count DESC " +
            "LIMIT " + limit;
    } else {
        // 评分热度
        sql = 
            "SELECT " +
            "    scenic_spot, " +
            "    AVG(rating) as avg_rating, " +
            "    COUNT(*) as review_count " +
            "FROM tourism_db.fuzhou_reviews " +
            "GROUP BY scenic_spot " +
            "ORDER BY avg_rating DESC " +
            "LIMIT " + limit;
    }

    try {
        return hiveJdbcTemplate.query(sql, (rs, rowNum) -> {
            Map<String, Object> map = new HashMap<>();
            map.put("rankNo", rowNum + 1);
            map.put("scenic_spot", rs.getString("scenic_spot"));
            map.put("spot_name", rs.getString("scenic_spot"));
            
            if ("visitor".equals(rankType)) {
                map.put("visitor_count", rs.getLong("visitor_count"));
                map.put("total_visitors", rs.getLong("visitor_count"));
            } else if ("review".equals(rankType)) {
                map.put("review_count", rs.getLong("review_count"));
                map.put("total_reviews", rs.getLong("review_count"));
            } else {
                double avgRating = rs.getDouble("avg_rating");
                map.put("avg_rating", Math.round(avgRating * 10.0) / 10.0);
                map.put("rating", Math.round(avgRating * 10.0) / 10.0);
                map.put("review_count", rs.getLong("review_count"));
            }
            return map;
        });
    } catch (Exception e) {
        log.error("查询景区排行榜失败", e);
        return new ArrayList<>();
    }
}
```

---

## 🔍 验证优化效果

### 测试方法
```bash
# 1. 进入hive-server容器
docker exec -it hive-server bash

# 2. 执行查询并查看执行计划
hive -e "
SET hive.exec.mode.local.auto=true;
SET hive.fetch.task.conversion=more;

EXPLAIN 
SELECT scenic_spot, COUNT(*) as cnt 
FROM tourism_db.fuzhou_reviews 
GROUP BY scenic_spot;
"

# 3. 查看是否使用本地模式
# 输出中如果包含 "Local work" 说明启用了本地模式
```

### SpringBoot日志验证
```
开始配置Hive性能优化参数...
✅ Hive性能优化配置完成
查询景区排行榜: rankType=visitor, limit=10
查询耗时: 521ms  ← 优化前是3000ms+
```

---

## ⚠️ 注意事项

1. **本地模式限制**: 只适用于小数据量（<128MB），数据增长后需切换到分布式模式
2. **分区表优化**: 确保查询时使用分区过滤（`WHERE dt=...`）
3. **统计信息**: 定期执行 `ANALYZE TABLE` 更新表统计信息
4. **监控查询**: 使用Hive WebUI（http://localhost:10002）监控查询执行情况

---

## 📚 参考资料

1. [Hive Performance Tuning](https://cwiki.apache.org/confluence/display/Hive/PerformanceTuning)
2. [Improving Performance Using Partitions](https://docs.cloudera.com/documentation/enterprise/latest/topics/hive_partitions.html)
3. [Hive Local Mode](https://cwiki.apache.org/confluence/display/Hive/GettingStarted#GettingStarted-LocalMode)
4. [DZone: How to Improve Hive Query Performance](https://dzone.com/articles/how-to-improve-hive-query-performance-with-hadoop)
