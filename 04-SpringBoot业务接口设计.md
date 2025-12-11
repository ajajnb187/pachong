# 福州旅游景区数据分析与可视化系统 - Spring Boot业务接口设计

## 一、Spring Boot服务概述

### 1.1 服务职责
- 用户认证与授权管理
- Hive数据查询和分析
- 数据统计和报表生成
- 业务逻辑处理
- 为前端提供数据API接口

### 1.2 技术栈
- **框架**：Spring Boot 2.7.x
- **ORM**：MyBatis Plus 3.5.x
- **数据库**：MySQL 8.0
- **Hive连接**：Hive JDBC Driver
- **安全认证**：Spring Security + JWT
- **缓存**：Redis（可选）
- **API文档**：Knife4j (Swagger)
- **工具库**：Hutool、Lombok

### 1.3 服务端口
- **开发环境**：http://localhost:8080
- **生产环境**：http://your-server:8080

## 二、API接口设计

### 2.1 统一响应格式

```java
@Data
public class Result<T> {
    private Integer code;
    private String msg;
    private T data;
    
    public static <T> Result<T> success(T data) {
        Result<T> result = new Result<>();
        result.setCode(200);
        result.setMsg("成功");
        result.setData(data);
        return result;
    }
    
    public static <T> Result<T> error(String msg) {
        Result<T> result = new Result<>();
        result.setCode(500);
        result.setMsg(msg);
        return result;
    }
}
```

**状态码说明**：
- `200`：成功
- `400`：请求参数错误
- `401`：未授权
- `403`：无权限
- `500`：服务器内部错误

---

## 三、用户管理模块

### 3.1 用户登录

**接口地址**：`POST /api/auth/login`

**接口描述**：用户登录，返回JWT Token

**请求参数**：

```json
{
    "username": "admin",
    "password": "123456"
}
```

**响应示例**：

```json
{
    "code": 200,
    "msg": "登录成功",
    "data": {
        "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        "userInfo": {
            "id": 1,
            "username": "admin",
            "nickname": "管理员",
            "avatar": "https://example.com/avatar.jpg",
            "role": "admin"
        }
    }
}
```

---

### 3.2 用户注册

**接口地址**：`POST /api/auth/register`

**接口描述**：新用户注册

**请求参数**：

```json
{
    "username": "newuser",
    "password": "123456",
    "nickname": "新用户",
    "email": "newuser@example.com",
    "phone": "13800138000"
}
```

**响应示例**：

```json
{
    "code": 200,
    "msg": "注册成功",
    "data": null
}
```

---

### 3.3 获取当前用户信息

**接口地址**：`GET /api/auth/userinfo`

**接口描述**：获取当前登录用户的详细信息

**请求头**：
```
Authorization: Bearer {token}
```

**响应示例**：

```json
{
    "code": 200,
    "msg": "成功",
    "data": {
        "id": 1,
        "username": "admin",
        "nickname": "管理员",
        "email": "admin@example.com",
        "phone": "13800138000",
        "avatar": "https://example.com/avatar.jpg",
        "role": "admin",
        "create_time": "2024-01-01 00:00:00",
        "last_login_time": "2024-12-10 22:30:00"
    }
}
```

---

### 3.4 修改用户信息

**接口地址**：`PUT /api/auth/update`

**接口描述**：修改当前用户信息

**请求参数**：

```json
{
    "nickname": "新昵称",
    "email": "newemail@example.com",
    "phone": "13900139000",
    "avatar": "https://example.com/new-avatar.jpg"
}
```

**响应示例**：

```json
{
    "code": 200,
    "msg": "修改成功",
    "data": null
}
```

---

## 四、数据分析模块

### 4.1 景区数据分析

#### 4.1.1 获取景区列表

**接口地址**：`GET /api/scenic/list`

**接口描述**：获取所有景区列表及基本统计信息

**请求参数**：

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| page | int | 否 | 页码，默认1 |
| page_size | int | 否 | 每页数量，默认10 |
| spot_type | string | 否 | 景区类型 |

**响应示例**：

```json
{
    "code": 200,
    "msg": "成功",
    "data": {
        "total": 10,
        "page": 1,
        "page_size": 10,
        "list": [
            {
                "spot_id": "fuzhou_sanfangqixiang",
                "spot_name": "三坊七巷",
                "spot_type": "历史文化",
                "location": "福州市鼓楼区",
                "rating": 4.5,
                "total_reviews": 15234,
                "total_visitors": 1250000,
                "ticket_price": 0,
                "images": ["url1", "url2"]
            }
        ]
    }
}
```

---

#### 4.1.2 获取景区详细信息

**接口地址**：`GET /api/scenic/detail/{spot_id}`

**接口描述**：获取指定景区的详细信息

**响应示例**：

```json
{
    "code": 200,
    "msg": "成功",
    "data": {
        "spot_id": "fuzhou_sanfangqixiang",
        "spot_name": "三坊七巷",
        "spot_type": "历史文化",
        "location": "福州市鼓楼区",
        "address": "福州市鼓楼区南后街",
        "longitude": 119.302,
        "latitude": 26.084,
        "open_time": "全天开放",
        "ticket_price": 0,
        "description": "三坊七巷是福州的历史文化街区...",
        "contact_phone": "0591-12345678",
        "official_website": "http://www.sfqx.com",
        "rating": 4.5,
        "total_reviews": 15234,
        "total_visitors": 1250000,
        "images": ["url1", "url2", "url3"]
    }
}
```

---

#### 4.1.3 景区排行榜

**接口地址**：`GET /api/scenic/ranking`

**接口描述**：获取景区排行榜

**请求参数**：

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| rank_type | string | 是 | 排行类型（visitor-游客量/rating-评分/review-评价数） |
| rank_period | string | 是 | 排行周期（daily-日/monthly-月/yearly-年） |
| limit | int | 否 | 返回数量，默认10 |

**响应示例**：

```json
{
    "code": 200,
    "msg": "成功",
    "data": {
        "rank_type": "visitor",
        "rank_period": "monthly",
        "stat_date": "2024-12",
        "list": [
            {
                "rank_no": 1,
                "spot_id": "fuzhou_sanfangqixiang",
                "spot_name": "三坊七巷",
                "metric_value": 105000,
                "change_rate": "+15%"
            },
            {
                "rank_no": 2,
                "spot_id": "fuzhou_gushan",
                "spot_name": "鼓山",
                "metric_value": 89000,
                "change_rate": "+8%"
            }
        ]
    }
}
```

---

### 4.2 游客数量分析

#### 4.2.1 景区客流量统计

**接口地址**：`GET /api/analysis/visitor-count`

**接口描述**：获取指定景区的客流量统计数据

**请求参数**：

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| spot_id | string | 是 | 景区ID |
| start_date | string | 是 | 开始日期（yyyy-MM-dd） |
| end_date | string | 是 | 结束日期（yyyy-MM-dd） |
| group_by | string | 否 | 分组维度（day-日/week-周/month-月），默认day |

**响应示例**：

```json
{
    "code": 200,
    "msg": "成功",
    "data": {
        "spot_name": "三坊七巷",
        "start_date": "2024-12-01",
        "end_date": "2024-12-10",
        "total_visitors": 89500,
        "avg_daily_visitors": 8950,
        "peak_date": "2024-12-08",
        "peak_visitors": 15800,
        "series": [
            {
                "date": "2024-12-01",
                "visitor_count": 8500,
                "is_holiday": false
            },
            {
                "date": "2024-12-08",
                "visitor_count": 15800,
                "is_holiday": true,
                "holiday_name": "周末"
            }
        ]
    }
}
```

---

#### 4.2.2 客流量趋势对比

**接口地址**：`GET /api/analysis/visitor-trend-compare`

**接口描述**：对比多个景区的客流量趋势

**请求参数**：

```json
{
    "spot_ids": ["fuzhou_sanfangqixiang", "fuzhou_gushan"],
    "start_date": "2024-12-01",
    "end_date": "2024-12-10"
}
```

**响应示例**：

```json
{
    "code": 200,
    "msg": "成功",
    "data": {
        "dates": ["2024-12-01", "2024-12-02", "2024-12-03"],
        "series": [
            {
                "spot_name": "三坊七巷",
                "data": [8500, 9200, 8800]
            },
            {
                "spot_name": "鼓山",
                "data": [6800, 7200, 7500]
            }
        ]
    }
}
```

---

### 4.3 景区评价分析

#### 4.3.1 评价统计

**接口地址**：`GET /api/analysis/review-stats`

**接口描述**：获取景区评价统计数据

**请求参数**：

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| spot_id | string | 是 | 景区ID |
| start_date | string | 否 | 开始日期 |
| end_date | string | 否 | 结束日期 |

**响应示例**：

```json
{
    "code": 200,
    "msg": "成功",
    "data": {
        "spot_name": "三坊七巷",
        "total_reviews": 15234,
        "avg_rating": 4.5,
        "rating_distribution": {
            "5": 8500,
            "4": 4200,
            "3": 1800,
            "2": 500,
            "1": 234
        },
        "positive_rate": 83.7,
        "negative_rate": 4.8,
        "neutral_rate": 11.5,
        "recent_trend": "上升"
    }
}
```

---

#### 4.3.2 评价列表

**接口地址**：`GET /api/analysis/reviews`

**接口描述**：获取景区评价列表

**请求参数**：

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| spot_id | string | 是 | 景区ID |
| page | int | 否 | 页码，默认1 |
| page_size | int | 否 | 每页数量，默认10 |
| rating | int | 否 | 筛选评分（1-5） |
| sort | string | 否 | 排序方式（time-时间/helpful-有用数） |

**响应示例**：

```json
{
    "code": 200,
    "msg": "成功",
    "data": {
        "total": 15234,
        "page": 1,
        "page_size": 10,
        "list": [
            {
                "review_id": "r001",
                "visitor_name": "张三",
                "rating": 5,
                "review_content": "三坊七巷非常值得一去，古色古香...",
                "review_images": ["url1", "url2"],
                "travel_date": "2024-12-01",
                "review_date": "2024-12-02",
                "helpful_count": 125,
                "visitor_location": "北京市"
            }
        ]
    }
}
```

---

#### 4.3.3 评价关键词分析

**接口地址**：`GET /api/analysis/review-keywords`

**接口描述**：提取景区评价中的高频关键词

**请求参数**：

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| spot_id | string | 是 | 景区ID |
| limit | int | 否 | 返回数量，默认20 |

**响应示例**：

```json
{
    "code": 200,
    "msg": "成功",
    "data": {
        "spot_name": "三坊七巷",
        "keywords": [
            {
                "word": "历史文化",
                "count": 3567,
                "sentiment": "positive"
            },
            {
                "word": "交通便利",
                "count": 2845,
                "sentiment": "positive"
            },
            {
                "word": "人多拥挤",
                "count": 1234,
                "sentiment": "negative"
            }
        ]
    }
}
```

---

### 4.4 季节性分析

#### 4.4.1 淡旺季分析

**接口地址**：`GET /api/analysis/season-pattern`

**接口描述**：分析景区的淡旺季规律

**请求参数**：

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| spot_id | string | 是 | 景区ID |
| year | int | 是 | 年份 |

**响应示例**：

```json
{
    "code": 200,
    "msg": "成功",
    "data": {
        "spot_name": "三坊七巷",
        "year": 2024,
        "peak_season": {
            "months": ["7", "8", "10"],
            "avg_visitors": 95000,
            "reason": "暑期旅游高峰、国庆黄金周"
        },
        "off_season": {
            "months": ["1", "2", "12"],
            "avg_visitors": 45000,
            "reason": "冬季低温，旅游淡季"
        },
        "monthly_stats": [
            {
                "month": "1",
                "visitor_count": 42000,
                "season_type": "淡季"
            },
            {
                "month": "7",
                "visitor_count": 98000,
                "season_type": "旺季"
            }
        ]
    }
}
```

---

#### 4.4.2 节假日影响分析

**接口地址**：`GET /api/analysis/holiday-impact`

**接口描述**：分析节假日对景区客流的影响

**请求参数**：

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| spot_id | string | 是 | 景区ID |
| year | int | 是 | 年份 |

**响应示例**：

```json
{
    "code": 200,
    "msg": "成功",
    "data": {
        "spot_name": "三坊七巷",
        "year": 2024,
        "avg_daily_visitors": 8500,
        "holidays": [
            {
                "holiday_name": "春节",
                "date_range": "2024-02-10 ~ 2024-02-17",
                "avg_visitors": 18500,
                "increase_rate": "+118%",
                "peak_date": "2024-02-12",
                "peak_visitors": 25000
            },
            {
                "holiday_name": "国庆节",
                "date_range": "2024-10-01 ~ 2024-10-07",
                "avg_visitors": 22000,
                "increase_rate": "+159%",
                "peak_date": "2024-10-02",
                "peak_visitors": 28000
            }
        ]
    }
}
```

---

### 4.5 游客行为分析

#### 4.5.1 客源地分布

**接口地址**：`GET /api/analysis/visitor-source`

**接口描述**：分析游客的地域来源分布

**请求参数**：

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| spot_id | string | 否 | 景区ID，不传则统计所有景区 |
| start_date | string | 否 | 开始日期 |
| end_date | string | 否 | 结束日期 |
| group_by | string | 否 | 分组维度（province-省/city-市），默认province |

**响应示例**：

```json
{
    "code": 200,
    "msg": "成功",
    "data": {
        "total_visitors": 1250000,
        "domestic_rate": 95.5,
        "foreign_rate": 4.5,
        "top_provinces": [
            {
                "province": "福建省",
                "visitor_count": 680000,
                "percentage": 54.4
            },
            {
                "province": "广东省",
                "visitor_count": 125000,
                "percentage": 10.0
            },
            {
                "province": "浙江省",
                "visitor_count": 98000,
                "percentage": 7.8
            }
        ],
        "map_data": [
            {
                "name": "福建",
                "value": 680000
            },
            {
                "name": "广东",
                "value": 125000
            }
        ]
    }
}
```

---

#### 4.5.2 游客年龄性别分布

**接口地址**：`GET /api/analysis/visitor-demographics`

**接口描述**：分析游客的年龄和性别结构

**请求参数**：

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| spot_id | string | 否 | 景区ID |
| start_date | string | 否 | 开始日期 |
| end_date | string | 否 | 结束日期 |

**响应示例**：

```json
{
    "code": 200,
    "msg": "成功",
    "data": {
        "gender_distribution": {
            "male": 48.5,
            "female": 51.5
        },
        "age_distribution": [
            {
                "age_group": "18岁以下",
                "percentage": 8.2
            },
            {
                "age_group": "18-30岁",
                "percentage": 35.8
            },
            {
                "age_group": "31-45岁",
                "percentage": 32.5
            },
            {
                "age_group": "46-60岁",
                "percentage": 18.3
            },
            {
                "age_group": "60岁以上",
                "percentage": 5.2
            }
        ]
    }
}
```

---

### 4.6 数据统计汇总

#### 4.6.1 数据概览

**接口地址**：`GET /api/analysis/overview`

**接口描述**：获取系统数据概览统计

**响应示例**：

```json
{
    "code": 200,
    "msg": "成功",
    "data": {
        "total_scenic_spots": 10,
        "total_reviews": 125000,
        "total_visitors": 2580000,
        "avg_rating": 4.3,
        "data_update_time": "2024-12-10 22:00:00",
        "today_stats": {
            "new_reviews": 356,
            "new_visitors": 15800
        },
        "hot_spots": [
            {
                "spot_name": "三坊七巷",
                "today_visitors": 5200
            },
            {
                "spot_name": "鼓山",
                "today_visitors": 4100
            }
        ]
    }
}
```

---

## 五、Hive查询实现

### 5.1 Hive连接配置

```java
@Configuration
public class HiveConfig {
    
    @Value("${hive.jdbc.url}")
    private String hiveUrl;
    
    @Value("${hive.jdbc.username}")
    private String username;
    
    @Value("${hive.jdbc.password}")
    private String password;
    
    @Bean(name = "hiveJdbcTemplate")
    public JdbcTemplate hiveJdbcTemplate() {
        DriverManagerDataSource dataSource = new DriverManagerDataSource();
        dataSource.setDriverClassName("org.apache.hive.jdbc.HiveDriver");
        dataSource.setUrl(hiveUrl);
        dataSource.setUsername(username);
        dataSource.setPassword(password);
        return new JdbcTemplate(dataSource);
    }
}
```

### 5.2 Hive查询示例

```java
@Service
public class ScenicAnalysisService {
    
    @Autowired
    @Qualifier("hiveJdbcTemplate")
    private JdbcTemplate hiveJdbcTemplate;
    
    /**
     * 查询景区客流量统计
     */
    public List<VisitorCountVO> getVisitorCount(String spotId, String startDate, String endDate) {
        String sql = 
            "SELECT " +
            "    stat_date, " +
            "    visitor_count, " +
            "    is_holiday, " +
            "    holiday_name " +
            "FROM dws_scenic_spot_daily_stats " +
            "WHERE spot_id = ? " +
            "  AND stat_date >= ? " +
            "  AND stat_date <= ? " +
            "  AND dt = (SELECT MAX(dt) FROM dws_scenic_spot_daily_stats) " +
            "ORDER BY stat_date";
        
        return hiveJdbcTemplate.query(sql, 
            new Object[]{spotId, startDate, endDate},
            new BeanPropertyRowMapper<>(VisitorCountVO.class));
    }
    
    /**
     * 查询景区排行榜
     */
    public List<ScenicRankingVO> getScenicRanking(String rankType, String rankPeriod, Integer limit) {
        String sql = 
            "SELECT " +
            "    rank_no, " +
            "    spot_id, " +
            "    spot_name, " +
            "    metric_value " +
            "FROM ads_scenic_spot_ranking " +
            "WHERE rank_type = ? " +
            "  AND rank_period = ? " +
            "  AND dt = (SELECT MAX(dt) FROM ads_scenic_spot_ranking) " +
            "ORDER BY rank_no " +
            "LIMIT ?";
        
        return hiveJdbcTemplate.query(sql,
            new Object[]{rankType, rankPeriod, limit},
            new BeanPropertyRowMapper<>(ScenicRankingVO.class));
    }
}
```

---

## 六、安全认证配置

### 6.1 JWT配置

```java
@Component
public class JwtUtil {
    
    @Value("${jwt.secret}")
    private String secret;
    
    @Value("${jwt.expiration}")
    private Long expiration;
    
    /**
     * 生成Token
     */
    public String generateToken(Long userId, String username) {
        Map<String, Object> claims = new HashMap<>();
        claims.put("userId", userId);
        claims.put("username", username);
        
        return Jwts.builder()
            .setClaims(claims)
            .setSubject(username)
            .setIssuedAt(new Date())
            .setExpiration(new Date(System.currentTimeMillis() + expiration * 1000))
            .signWith(SignatureAlgorithm.HS512, secret)
            .compact();
    }
    
    /**
     * 验证Token
     */
    public boolean validateToken(String token) {
        try {
            Jwts.parser().setSigningKey(secret).parseClaimsJws(token);
            return true;
        } catch (Exception e) {
            return false;
        }
    }
}
```

### 6.2 拦截器配置

```java
@Component
public class JwtInterceptor implements HandlerInterceptor {
    
    @Autowired
    private JwtUtil jwtUtil;
    
    @Override
    public boolean preHandle(HttpServletRequest request, 
                           HttpServletResponse response, 
                           Object handler) throws Exception {
        String token = request.getHeader("Authorization");
        
        if (token != null && token.startsWith("Bearer ")) {
            token = token.substring(7);
            if (jwtUtil.validateToken(token)) {
                return true;
            }
        }
        
        response.setStatus(HttpServletResponse.SC_UNAUTHORIZED);
        response.getWriter().write("{\"code\":401,\"msg\":\"未授权\"}");
        return false;
    }
}
```

---

## 七、异常处理

### 7.1 全局异常处理器

```java
@RestControllerAdvice
public class GlobalExceptionHandler {
    
    @ExceptionHandler(Exception.class)
    public Result<Void> handleException(Exception e) {
        log.error("系统异常", e);
        return Result.error("系统异常：" + e.getMessage());
    }
    
    @ExceptionHandler(IllegalArgumentException.class)
    public Result<Void> handleIllegalArgumentException(IllegalArgumentException e) {
        return Result.error("参数错误：" + e.getMessage());
    }
    
    @ExceptionHandler(SQLException.class)
    public Result<Void> handleSQLException(SQLException e) {
        log.error("数据库异常", e);
        return Result.error("数据库查询失败");
    }
}
```

---

## 八、配置文件

### 8.1 application.yml

```yaml
server:
  port: 8080

spring:
  application:
    name: tourism-springboot
  
  datasource:
    driver-class-name: com.mysql.cj.jdbc.Driver
    url: jdbc:mysql://localhost:3306/tourism_db?useUnicode=true&characterEncoding=utf8&serverTimezone=Asia/Shanghai
    username: root
    password: 123456
  
  jackson:
    date-format: yyyy-MM-dd HH:mm:ss
    time-zone: GMT+8

# Hive配置
hive:
  jdbc:
    url: jdbc:hive2://localhost:10000/default
    username: hadoop
    password: 

# JWT配置
jwt:
  secret: your-secret-key-here
  expiration: 86400  # 24小时

# MyBatis Plus配置
mybatis-plus:
  configuration:
    map-underscore-to-camel-case: true
    log-impl: org.apache.ibatis.logging.stdout.StdOutImpl
  global-config:
    db-config:
      id-type: auto

# Knife4j配置
knife4j:
  enable: true
  setting:
    language: zh-CN
```

---

**文档版本**：V1.0  
**编写日期**：2024-12-10  
**下一步**：前端功能模块设计和数据爬取实现详细指南
