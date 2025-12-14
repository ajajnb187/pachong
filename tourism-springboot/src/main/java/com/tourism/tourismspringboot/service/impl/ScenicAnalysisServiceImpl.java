package com.tourism.tourismspringboot.service.impl;

import com.tourism.tourismspringboot.service.IScenicAnalysisService;
import com.tourism.tourismspringboot.service.RedisCacheService;
import com.tourism.tourismspringboot.vo.AnalysisOverviewVO;
import com.tourism.tourismspringboot.vo.ScenicVO;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.*;
import java.util.stream.Collectors;

/**
 * 景区数据分析服务实现
 * 包含所有Hive查询接口
 */
@Slf4j
@Service
public class ScenicAnalysisServiceImpl implements IScenicAnalysisService {

    @Autowired
    @Qualifier("hiveJdbcTemplate")
    private JdbcTemplate hiveJdbcTemplate;
    
    @Autowired
    private RedisCacheService redisCacheService;
    
    private String getLatestPartition(String tableName) {
        try {
            hiveJdbcTemplate.execute("SET hive.fetch.task.conversion=more");
            String sql = "SHOW PARTITIONS tourism_db." + tableName;
            List<String> partitions = hiveJdbcTemplate.queryForList(sql, String.class);
            if (partitions.isEmpty()) {
                return "";
            }
            partitions.sort(String::compareTo);
            String latestPartition = partitions.get(partitions.size() - 1);
            return latestPartition.replace("dt=", "");
        } catch (Exception e) {
            log.error("获取最新分区失败: {}", e.getMessage());
            return "";
        }
    }

    @Override
    public AnalysisOverviewVO getOverview() {
        log.info("查询数据概览");
        
        String cacheKey = "analysis:overview";
        Object cached = redisCacheService.get(cacheKey);
        if (cached != null && cached instanceof AnalysisOverviewVO) {
            log.info("从Redis缓存获取数据概览");
            return (AnalysisOverviewVO) cached;
        }
        
        AnalysisOverviewVO overview = new AnalysisOverviewVO();

        try {
            // 设置Hive参数避免MapReduce任务
            hiveJdbcTemplate.execute("SET hive.fetch.task.conversion=more");
            hiveJdbcTemplate.execute("SET hive.fetch.task.aggr=true");
            hiveJdbcTemplate.execute("SET hive.fetch.task.conversion.threshold=1073741824");
            
            String latestPartition = getLatestPartition("scenic_spots");
            if (latestPartition.isEmpty()) {
                throw new RuntimeException("未找到景区数据分区");
            }
            
            String scenicSql = "SELECT COUNT(*) as count, AVG(comment_score) as avg_rating " +
                              "FROM tourism_db.scenic_spots " +
                              "WHERE dt = '" + latestPartition + "' AND comment_score IS NOT NULL";
            List<Map<String, Object>> scenicStats = hiveJdbcTemplate.queryForList(scenicSql);
            
            if (scenicStats != null && !scenicStats.isEmpty()) {
                Map<String, Object> stats = scenicStats.get(0);
                Long totalSpots = ((Number) stats.get("count")).longValue();
                Double avgRating = stats.get("avg_rating") != null ? 
                    ((Number) stats.get("avg_rating")).doubleValue() : 0.0;
                
                overview.setTotalSpots(totalSpots);
                overview.setAverageRating(Math.round(avgRating * 10.0) / 10.0);
            } else {
                overview.setTotalSpots(0L);
                overview.setAverageRating(0.0);
            }

            // 从评论表统计评论数和游客数
            String reviewSql = "SELECT COUNT(*) as review_count, COUNT(DISTINCT visitor_name) as visitor_count " +
                              "FROM tourism_db.fuzhou_reviews_latest";
            List<Map<String, Object>> reviewStats = hiveJdbcTemplate.queryForList(reviewSql);
            
            if (reviewStats != null && !reviewStats.isEmpty()) {
                Map<String, Object> stats = reviewStats.get(0);
                Long totalReviews = ((Number) stats.get("review_count")).longValue();
                Long totalReviewers = ((Number) stats.get("visitor_count")).longValue();
                
                overview.setTotalReviews(totalReviews);
                overview.setTotalReviewers(totalReviewers);
            } else {
                overview.setTotalReviews(0L);
                overview.setTotalReviewers(0L);
            }

            overview.setDataUpdateTime(LocalDateTime.now().format(DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss")));

            String hotSpotSql = 
                "SELECT scenic_spot, comment_score " +
                "FROM tourism_db.scenic_spots " +
                "WHERE dt = '" + latestPartition + "' AND comment_score IS NOT NULL " +
                "ORDER BY comment_score DESC " +
                "LIMIT 5";

            List<AnalysisOverviewVO.HotSpot> hotSpots = hiveJdbcTemplate.query(hotSpotSql, (rs, rowNum) -> {
                AnalysisOverviewVO.HotSpot spot = new AnalysisOverviewVO.HotSpot();
                spot.setName(rs.getString("scenic_spot"));
                spot.setRating(Math.round(rs.getDouble("comment_score") * 10.0) / 10.0);
                return spot;
            });
            overview.setHotSpots(hotSpots != null ? hotSpots : new ArrayList<>());

            log.info("数据概览查询成功: 景区{}个, 评分{}", overview.getTotalSpots(), overview.getAverageRating());
            redisCacheService.set(cacheKey, overview, 3600);

        } catch (Exception e) {
            log.error("查询数据概览失败", e);
            overview.setTotalSpots(0L);
            overview.setTotalReviews(0L);
            overview.setAverageRating(0.0);
            overview.setTotalReviewers(0L);
            overview.setHotSpots(new ArrayList<>());
        }

        return overview;
    }

    @Override
    public List<ScenicVO> getScenicList(Integer page, Integer pageSize) {
        log.info("查询景区列表: page={}, pageSize={}", page, pageSize);
        
        // 检查Redis缓存
        String cacheKey = "scenic:list:" + page + ":" + pageSize;
        Object cached = redisCacheService.get(cacheKey);
        if (cached != null) {
            log.info("从Redis缓存获取景区列表");
            return (List<ScenicVO>) cached;
        }

        try {
            // 先检查是否有数据
            String checkSql = "SELECT COUNT(*) as cnt FROM tourism_db.scenic_spots_latest LIMIT 1";
            Long dataCheck = hiveJdbcTemplate.queryForObject(checkSql, Long.class);
            
            if (dataCheck == null || dataCheck == 0) {
                log.warn("scenic_spots表中没有数据");
                return new ArrayList<>();
            }

            // 计算偏移量
            int offset = (page - 1) * pageSize;
            
            String sql = 
                "SELECT " +
                "    business_id, " +
                "    scenic_spot, " +
                "    city, " +
                "    zone_name, " +
                "    comment_score, " +
                "    heat_score, " +
                "    sight_level, " +
                "    market_price, " +
                "    is_free, " +
                "    cover_image_url, " +
                "    latitude, " +
                "    longitude " +
                "FROM tourism_db.scenic_spots_latest " +
                "ORDER BY heat_score DESC " +
                "LIMIT " + pageSize + " OFFSET " + offset;


            List<ScenicVO> list = hiveJdbcTemplate.query(sql, (rs, rowNum) -> {
                ScenicVO vo = new ScenicVO();
                vo.setBusinessId(rs.getInt("business_id"));
                vo.setScenicSpot(rs.getString("scenic_spot"));
                vo.setCity(rs.getString("city"));
                vo.setZoneName(rs.getString("zone_name"));
                vo.setCommentScore(rs.getDouble("comment_score"));
                vo.setHeatScore(rs.getDouble("heat_score"));
                vo.setSightLevel(rs.getString("sight_level"));
                vo.setMarketPrice(rs.getString("market_price"));
                vo.setIsFree(rs.getString("is_free"));
                vo.setCoverImageUrl(rs.getString("cover_image_url"));
                vo.setLatitude(rs.getDouble("latitude"));
                vo.setLongitude(rs.getDouble("longitude"));
                return vo;
            });
            
            // 写入Redis缓存
            redisCacheService.set(cacheKey, list, 3600);
            
            return list;
        } catch (Exception e) {
            log.error("查询景区列表失败: {}", e.getMessage());
            log.debug("详细错误信息", e);
            return new ArrayList<>();
        }
    }

    @Override
    public Map<String, Object> getScenicListWithPage(Integer page, Integer pageSize) {
        log.info("查询景区列表（分页）: page={}, pageSize={}", page, pageSize);
        
        String cacheKey = "analysis:scenic:page:" + page + ":" + pageSize;
        Object cached = redisCacheService.get(cacheKey);
        if (cached != null && cached instanceof Map) {
            log.info("从Redis缓存获取景区列表（分页）");
            @SuppressWarnings("unchecked")
            Map<String, Object> cachedMap = (Map<String, Object>) cached;
            return cachedMap;
        }
        
        try {
            String countSql = "SELECT COUNT(*) as total FROM tourism_db.scenic_spots_latest";
            Long total = hiveJdbcTemplate.queryForObject(countSql, Long.class);
            
            String sql = 
                "SELECT " +
                "    business_id, " +
                "    scenic_spot, " +
                "    city, " +
                "    zone_name, " +
                "    comment_score, " +
                "    heat_score, " +
                "    sight_level, " +
                "    cover_image_url, " +
                "    latitude, " +
                "    longitude " +
                "FROM tourism_db.scenic_spots_latest " +
                "ORDER BY heat_score DESC " +
                "LIMIT " + pageSize;
            
            List<ScenicVO> list = hiveJdbcTemplate.query(sql, (rs, rowNum) -> {
                ScenicVO vo = new ScenicVO();
                vo.setBusinessId(rs.getInt("business_id"));
                vo.setScenicSpot(rs.getString("scenic_spot"));
                vo.setCity(rs.getString("city"));
                vo.setZoneName(rs.getString("zone_name"));
                vo.setCommentScore(rs.getDouble("comment_score"));
                vo.setHeatScore(rs.getDouble("heat_score"));
                vo.setSightLevel(rs.getString("sight_level"));
                vo.setCoverImageUrl(rs.getString("cover_image_url"));
                vo.setLatitude(rs.getDouble("latitude"));
                vo.setLongitude(rs.getDouble("longitude"));
                return vo;
            });
            
            Map<String, Object> result = new HashMap<>();
            result.put("total", total != null ? total : 0);
            result.put("page", page);
            result.put("page_size", pageSize);
            result.put("list", list);
            
            redisCacheService.set(cacheKey, result, 3600);
            return result;
        } catch (Exception e) {
            log.error("分页查询景区列表失败", e);
            Map<String, Object> result = new HashMap<>();
            result.put("total", 0);
            result.put("page", page);
            result.put("page_size", pageSize);
            result.put("list", new ArrayList<>());
            return result;
        }
    }

    @Override
    public Map<String, Object> getScenicDetail(String spotId) {
        log.info("查询景区详情: spotId={}", spotId);
        
        String cacheKey = "analysis:scenic:detail:" + spotId;
        Object cached = redisCacheService.get(cacheKey);
        if (cached != null && cached instanceof Map) {
            log.info("从Redis缓存获取景区详情: {}", spotId);
            @SuppressWarnings("unchecked")
            Map<String, Object> cachedMap = (Map<String, Object>) cached;
            return cachedMap;
        }

        Map<String, Object> detail = new HashMap<>();

        try {
            String sql = 
                "SELECT " +
                "    scenic_spot, " +
                "    COUNT(*) as total_reviews, " +
                "    AVG(rating) as avg_rating " +
                "FROM tourism_db.fuzhou_reviews_latest " +
                "WHERE scenic_spot = ? " +
                "GROUP BY scenic_spot";

            Map<String, Object> basic = hiveJdbcTemplate.queryForMap(sql, spotId);
            detail.putAll(basic);
            
            Double avgRating = ((Number) basic.get("avg_rating")).doubleValue();
            detail.put("avg_rating", Math.round(avgRating * 10.0) / 10.0);
            
            redisCacheService.set(cacheKey, detail, 3600);

        } catch (Exception e) {
            log.error("查询景区详情失败", e);
        }

        return detail;
    }

    @Override
    public List<Map<String, Object>> getVisitorCount(String spotId, String startDate, String endDate) {
        log.info("查询客流量统计: spotId={}, startDate={}, endDate={}", spotId, startDate, endDate);
        
        String cacheKey = "analysis:visitor:count:" + spotId + ":" + startDate + ":" + endDate;
        Object cached = redisCacheService.get(cacheKey);
        if (cached != null && cached instanceof List) {
            log.info("从Redis缓存获取客流量统计");
            @SuppressWarnings("unchecked")
            List<Map<String, Object>> cachedList = (List<Map<String, Object>>) cached;
            return cachedList;
        }

        String sql = 
            "SELECT " +
            "    travel_date as stat_date, " +
            "    COUNT(*) as visitor_count " +
            "FROM tourism_db.fuzhou_reviews_latest " +
            "WHERE scenic_spot = ? " +
            "  AND travel_date >= ? " +
            "  AND travel_date <= ? " +
            "GROUP BY travel_date " +
            "ORDER BY travel_date " +
            "LIMIT 1000";

        try {
            List<Map<String, Object>> list = hiveJdbcTemplate.query(sql, 
                new Object[]{spotId, startDate, endDate},
                (rs, rowNum) -> {
                    Map<String, Object> map = new HashMap<>();
                    map.put("date", rs.getString("stat_date"));
                    map.put("visitorCount", rs.getLong("visitor_count"));
                    map.put("isHoliday", 0);
                    return map;
                });
            redisCacheService.set(cacheKey, list, 3600);
            return list;
        } catch (Exception e) {
            log.error("查询客流量统计失败", e);
            return new ArrayList<>();
        }
    }

    @Override
    public Map<String, Object> getVisitorTrendCompare(List<String> spotIds, String startDate, String endDate) {
        log.info("查询客流量趋势对比: spotIds={}, startDate={}, endDate={}", spotIds, startDate, endDate);
        
        String cacheKey = "analysis:visitor:trend:" + String.join(",", spotIds) + ":" + startDate + ":" + endDate;
        Object cached = redisCacheService.get(cacheKey);
        if (cached != null && cached instanceof Map) {
            log.info("从Redis缓存获取客流量趋势对比");
            @SuppressWarnings("unchecked")
            Map<String, Object> cachedMap = (Map<String, Object>) cached;
            return cachedMap;
        }

        Map<String, Object> result = new HashMap<>();
        
        try {
            // 获取日期列表
            String dateSql = 
                "SELECT DISTINCT travel_date " +
                "FROM tourism_db.fuzhou_reviews_latest " +
                "WHERE travel_date >= ? AND travel_date <= ? " +
                "LIMIT 1000";
            
            List<String> dates = hiveJdbcTemplate.queryForList(dateSql, new Object[]{startDate, endDate}, String.class);
            result.put("dates", dates);

            // 查询每个景区的数据
            List<Map<String, Object>> series = new ArrayList<>();
            
            for (String spotId : spotIds) {
                String sql = 
                    "SELECT " +
                    "    scenic_spot, " +
                    "    travel_date, " +
                    "    COUNT(*) as count " +
                    "FROM tourism_db.fuzhou_reviews_latest " +
                    "    WHERE scenic_spot = ? " +
                    "      AND travel_date >= ? " +
                    "      AND travel_date <= ? " +
                    "    GROUP BY scenic_spot, travel_date " +
                    "LIMIT 1000";
                
                List<Map<String, Object>> records = hiveJdbcTemplate.queryForList(sql, spotId, startDate, endDate);
                
                Map<String, Object> spotData = new HashMap<>();
                spotData.put("name", spotId);
                
                List<Long> data = new ArrayList<>();
                for (String date : dates) {
                    Long count = 0L;
                    for (Map<String, Object> record : records) {
                        if (date.equals(record.get("travel_date"))) {
                            count = ((Number) record.get("count")).longValue();
                            break;
                        }
                    }
                    data.add(count);
                }
                spotData.put("data", data);
                series.add(spotData);
            }
            
            result.put("series", series);
            
            redisCacheService.set(cacheKey, result, 3600);

        } catch (Exception e) {
            log.error("查询客流量趋势对比失败", e);
        }

        return result;
    }

    @Override
    public Map<String, Object> getReviewStats(String spotId) {
        log.info("查询评价统计: spotId={}", spotId);
        
        String cacheKey = "analysis:review:stats:" + spotId;
        Object cached = redisCacheService.get(cacheKey);
        if (cached != null && cached instanceof Map) {
            log.info("从Redis缓存获取评价统计");
            @SuppressWarnings("unchecked")
            Map<String, Object> cachedMap = (Map<String, Object>) cached;
            return cachedMap;
        }

        Map<String, Object> result = new HashMap<>();

        try {
            String sql = 
                "SELECT " +
                "    scenic_spot, " +
                "    COUNT(*) as total_reviews, " +
                "    AVG(rating) as avg_rating " +
                "FROM tourism_db.fuzhou_reviews_latest " +
                "WHERE scenic_spot = ? " +
                "GROUP BY scenic_spot";

            Map<String, Object> stats = hiveJdbcTemplate.queryForMap(sql, spotId);
            result.put("spotName", stats.get("scenic_spot"));
            result.put("totalReviews", stats.get("total_reviews"));
            
            Double avgRating = ((Number) stats.get("avg_rating")).doubleValue();
            result.put("avgRating", Math.round(avgRating * 10.0) / 10.0);

            // 评分分布
            String distSql = 
                "SELECT " +
                "    CAST(rating AS INT) as rating_level, " +
                "    COUNT(*) as count " +
                "FROM tourism_db.fuzhou_reviews_latest " +
                "WHERE scenic_spot = ? " +
                "GROUP BY CAST(rating AS INT)";

            List<Map<String, Object>> distribution = hiveJdbcTemplate.queryForList(distSql, spotId);
            Map<String, Long> ratingDist = new HashMap<>();
            long totalCount = 0;
            long positiveCount = 0;

            for (Map<String, Object> row : distribution) {
                String level = row.get("rating_level").toString();
                Long count = ((Number) row.get("count")).longValue();
                ratingDist.put(level, count);
                totalCount += count;
                
                if ("4".equals(level) || "5".equals(level)) {
                    positiveCount += count;
                }
            }

            result.put("ratingDistribution", ratingDist);
            result.put("positiveRate", totalCount > 0 ? Math.round(positiveCount * 1000.0 / totalCount) / 10.0 : 0.0);
            
            redisCacheService.set(cacheKey, result, 3600);

        } catch (Exception e) {
            log.error("查询评价统计失败", e);
        }

        return result;
    }

    @Override
    public Map<String, Object> getReviews(String spotId, Integer page, Integer pageSize, Integer rating, String sort) {
        log.info("查询评价列表: spotId={}, page={}, rating={}", spotId, page, rating);
        
        String cacheKey = "analysis:review:list:" + spotId + ":" + page + ":" + pageSize + ":" + rating + ":" + sort;
        Object cached = redisCacheService.get(cacheKey);
        if (cached != null && cached instanceof Map) {
            log.info("从Redis缓存获取评价列表");
            @SuppressWarnings("unchecked")
            Map<String, Object> cachedMap = (Map<String, Object>) cached;
            return cachedMap;
        }

        Map<String, Object> result = new HashMap<>();

        try {
            StringBuilder sql = new StringBuilder(
                "SELECT " +
                "    visitor_name, " +
                "    rating, " +
                "    review_content, " +
                "    travel_date " +
                "FROM tourism_db.fuzhou_reviews_latest " +
                "WHERE scenic_spot = ? ");

            List<Object> params = new ArrayList<>();
            params.add(spotId);

            if (rating != null) {
                sql.append("AND CAST(rating AS INT) = ? ");
                params.add(rating);
            }

            sql.append("ORDER BY travel_date DESC ");

            sql.append("LIMIT ?");
            params.add(pageSize);

            List<Map<String, Object>> list = hiveJdbcTemplate.queryForList(sql.toString(), params.toArray());
            
            result.put("total", list.size());
            result.put("page", page);
            result.put("page_size", pageSize);
            result.put("list", list);
            
            redisCacheService.set(cacheKey, result, 3600);

        } catch (Exception e) {
            log.error("查询评价列表失败", e);
        }

        return result;
    }

    @Override
    public Map<String, Object> getReviewKeywords(String spotId, Integer limit) {
        log.info("查询评价关键词: spotId={}", spotId);
        
        String cacheKey = "analysis:review:keywords:" + spotId + ":" + limit;
        Object cached = redisCacheService.get(cacheKey);
        if (cached != null && cached instanceof Map) {
            log.info("从Redis缓存获取评价关键词");
            @SuppressWarnings("unchecked")
            Map<String, Object> cachedMap = (Map<String, Object>) cached;
            return cachedMap;
        }

        Map<String, Object> result = new HashMap<>();

        try {
            // 简化实现：统计高频词（实际应使用分词工具）
            String sql = 
                "SELECT review_content FROM tourism_db.fuzhou_reviews_latest WHERE scenic_spot = ? LIMIT 100";

            List<String> contents = hiveJdbcTemplate.queryForList(sql, new Object[]{spotId}, String.class);
            
            // 简单的关键词提取（实际应使用jieba等分词工具）
            List<Map<String, Object>> keywords = Arrays.asList(
                createKeyword("风景优美", 120, "positive"),
                createKeyword("交通便利", 95, "positive"),
                createKeyword("值得推荐", 88, "positive"),
                createKeyword("人多拥挤", 45, "negative")
            );

            result.put("spotName", "景区");
            result.put("keywords", keywords.subList(0, Math.min(limit, keywords.size())));
            
            redisCacheService.set(cacheKey, result, 3600);

        } catch (Exception e) {
            log.error("查询评价关键词失败", e);
        }

        return result;
    }

    private Map<String, Object> createKeyword(String word, int count, String sentiment) {
        Map<String, Object> keyword = new HashMap<>();
        keyword.put("word", word);
        keyword.put("count", count);
        keyword.put("sentiment", sentiment);
        return keyword;
    }

    @Override
    public Map<String, Object> getSeasonPattern(String spotId, Integer year) {
        log.info("查询季节性分析: spotId={}, year={}", spotId, year);
        
        String cacheKey = "analysis:season:" + spotId + ":" + year;
        Object cached = redisCacheService.get(cacheKey);
        if (cached != null && cached instanceof Map) {
            log.info("从Redis缓存获取季节性分析");
            @SuppressWarnings("unchecked")
            Map<String, Object> cachedMap = (Map<String, Object>) cached;
            return cachedMap;
        }

        Map<String, Object> result = new HashMap<>();

        try {
            StringBuilder sql = new StringBuilder(
                "SELECT " +
                "    MONTH(travel_date) as month, " +
                "    COUNT(*) as visitor_count " +
                "FROM tourism_db.fuzhou_reviews_latest " +
                "WHERE 1=1 ");
            
            List<Object> params = new ArrayList<>();
            
            // 如果spotId不为空，则分析单个景点；否则分析福州全域
            if (spotId != null && !spotId.isEmpty()) {
                sql.append("AND scenic_spot = ? ");
                params.add(spotId);
            }
            
            sql.append("AND YEAR(travel_date) = ? ");
            params.add(year);
            
            sql.append("GROUP BY MONTH(travel_date) ");
            sql.append("LIMIT 12");

            List<Map<String, Object>> monthlyStats = hiveJdbcTemplate.query(sql.toString(),
                params.toArray(),
                (rs, rowNum) -> {
                    Map<String, Object> map = new HashMap<>();
                    int month = rs.getInt("month");
                    map.put("month", month);
                    map.put("visitorCount", rs.getLong("visitor_count"));
                    
                    String seasonType;
                    if (month >= 3 && month <= 5) {
                        seasonType = "春季";
                    } else if (month >= 6 && month <= 8) {
                        seasonType = "夏季";
                    } else if (month >= 9 && month <= 11) {
                        seasonType = "秋季";
                    } else {
                        seasonType = "冬季";
                    }
                    map.put("seasonType", seasonType);
                    
                    return map;
                });

            result.put("year", year);
            result.put("monthlyStats", monthlyStats);
            
            redisCacheService.set(cacheKey, result, 3600);

        } catch (Exception e) {
            log.error("查询季节性分析失败", e);
        }

        return result;
    }

    @Override
    public Map<String, Object> getHolidayImpact(String spotId, Integer year) {
        log.info("查询节假日影响: spotId={}, year={}", spotId, year);
        
        String cacheKey = "analysis:holiday:" + spotId + ":" + year;
        Object cached = redisCacheService.get(cacheKey);
        if (cached != null && cached instanceof Map) {
            log.info("从Redis缓存获取节假日影响");
            @SuppressWarnings("unchecked")
            Map<String, Object> cachedMap = (Map<String, Object>) cached;
            return cachedMap;
        }

        Map<String, Object> result = new HashMap<>();

        try {
            // 计算平均日客流量
            String avgSql = 
                "SELECT AVG(cnt) as avg_visitors FROM (" +
                "    SELECT COUNT(*) as cnt " +
                "    FROM tourism_db.fuzhou_reviews_latest " +
                "    WHERE scenic_spot = ? AND YEAR(travel_date) = ? " +
                "    GROUP BY travel_date" +
                ") t";

            Double avgVisitors = hiveJdbcTemplate.queryForObject(avgSql, new Object[]{spotId, year}, Double.class);
            result.put("avgDailyVisitors", avgVisitors != null ? avgVisitors.intValue() : 0);

            // 模拟节假日数据（实际应从节假日配置表查询）
            List<Map<String, Object>> holidays = Arrays.asList(
                createHoliday("春节", year + "-02-10~" + year + "-02-17", avgVisitors, 2.18),
                createHoliday("国庆节", year + "-10-01~" + year + "-10-07", avgVisitors, 2.59)
            );

            result.put("spotName", "景区");
            result.put("year", year);
            result.put("holidays", holidays);
            
            redisCacheService.set(cacheKey, result, 3600);

        } catch (Exception e) {
            log.error("查询节假日影响失败", e);
        }

        return result;
    }

    private Map<String, Object> createHoliday(String name, String dateRange, Double avgVisitors, double rate) {
        Map<String, Object> holiday = new HashMap<>();
        holiday.put("holidayName", name);
        holiday.put("dateRange", dateRange);
        holiday.put("avgVisitors", (int)(avgVisitors * rate));
        holiday.put("increaseRate", "+" + (int)((rate - 1) * 100) + "%");
        return holiday;
    }

    @Override
    public List<Map<String, Object>> getScenicRanking(String rankType, Integer limit) {
        log.info("查询景区排行榜: rankType={}, limit={}", rankType, limit);
        
        // 设置Hive参数避免MapReduce任务
        try {
            hiveJdbcTemplate.execute("SET hive.fetch.task.conversion=more");
            hiveJdbcTemplate.execute("SET hive.fetch.task.aggr=true");
            hiveJdbcTemplate.execute("SET hive.fetch.task.conversion.threshold=1073741824");
        } catch (Exception e) {
            log.warn("设置Hive参数失败，继续执行查询", e);
        }
        
        String cacheKey = "analysis:ranking:" + rankType + ":" + limit;
        Object cached = redisCacheService.get(cacheKey);
        if (cached != null && cached instanceof List) {
            log.info("从Redis缓存获取景区排行榜");
            @SuppressWarnings("unchecked")
            List<Map<String, Object>> cachedList = (List<Map<String, Object>>) cached;
            return cachedList;
        }

        String sql;
        String orderField;
        
        if ("visitor".equals(rankType)) {
            // 游客流量：按独立游客数量排序（使用DISTINCT visitor_name统计真实游客数）
            sql = 
                "SELECT " +
                "    scenic_spot, " +
                "    COUNT(DISTINCT visitor_name) as visitor_count " +
                "FROM tourism_db.fuzhou_reviews_latest " +
                "GROUP BY scenic_spot " +
                "ORDER BY visitor_count DESC " +
                "LIMIT " + limit;
            orderField = "visitor";
        } else if ("review".equals(rankType)) {
            // 评论体量：按评论总数排序（使用COUNT(*)统计评论数量）
            sql = 
                "SELECT " +
                "    scenic_spot, " +
                "    COUNT(*) as review_count " +
                "FROM tourism_db.fuzhou_reviews_latest " +
                "GROUP BY scenic_spot " +
                "ORDER BY review_count DESC " +
                "LIMIT " + limit;
            orderField = "review";
        } else {
            // 评分热度（rating）：从评论表统计平均评分，与visitor/review使用相同的表
            sql = 
                "SELECT " +
                "    scenic_spot, " +
                "    AVG(rating) as avg_rating, " +
                "    COUNT(*) as review_count " +
                "FROM tourism_db.fuzhou_reviews_latest " +
                "WHERE rating IS NOT NULL " +
                "GROUP BY scenic_spot " +
                "ORDER BY avg_rating DESC " +
                "LIMIT " + limit;
            orderField = "rating";
        }

        try {
            List<Map<String, Object>> rankingList = hiveJdbcTemplate.query(sql, (rs, rowNum) -> {
                Map<String, Object> map = new HashMap<>();
                map.put("rankNo", rowNum + 1);
                map.put("scenic_spot", rs.getString("scenic_spot"));
                map.put("spot_name", rs.getString("scenic_spot"));
                
                if ("visitor".equals(orderField)) {
                    map.put("visitor_count", rs.getLong("visitor_count"));
                    map.put("total_visitors", rs.getLong("visitor_count"));
                } else if ("review".equals(orderField)) {
                    map.put("review_count", rs.getLong("review_count"));
                    map.put("total_reviews", rs.getLong("review_count"));
                } else {
                    double avgRating = rs.getDouble("avg_rating");
                    map.put("avg_rating", Math.round(avgRating * 10.0) / 10.0);
                    map.put("rating", Math.round(avgRating * 10.0) / 10.0);
                }
                return map;
            });
            
            redisCacheService.set(cacheKey, rankingList, 3600);
            return rankingList;
        } catch (Exception e) {
            log.error("查询景区排行榜失败", e);
            return new ArrayList<>();
        }
    }

    @Override
    public Map<String, Object> getScenicRankingWithPeriod(String rankType, String rankPeriod, Integer limit) {
        List<Map<String, Object>> ranking = getScenicRanking(rankType, limit);
        
        Map<String, Object> result = new HashMap<>();
        result.put("rankType", rankType);
        result.put("rankPeriod", rankPeriod);
        result.put("statDate", LocalDateTime.now().format(DateTimeFormatter.ofPattern("yyyy-MM")));
        result.put("list", ranking);
        
        return result;
    }

    @Override
    public Map<String, Object> getVisitorSource(String spotId, String startDate, String endDate) {
        log.info("查询客源地分布: spotId={}", spotId);
        
        String cacheKey = "analysis:visitor:source:" + spotId + ":" + startDate + ":" + endDate;
        Object cached = redisCacheService.get(cacheKey);
        if (cached != null && cached instanceof Map) {
            log.info("从Redis缓存获取客源地分布");
            @SuppressWarnings("unchecked")
            Map<String, Object> cachedMap = (Map<String, Object>) cached;
            return cachedMap;
        }

        Map<String, Object> result = new HashMap<>();

        try {
            // 使用IP属地字段统计客源地分布
            StringBuilder sql = new StringBuilder(
                "SELECT " +
                "    ip_location, " +
                "    COUNT(*) as visitor_count " +
                "FROM tourism_db.fuzhou_reviews_latest " +
                "WHERE ip_location IS NOT NULL AND ip_location != '' ");

            List<Object> params = new ArrayList<>();

            if (spotId != null && !spotId.isEmpty()) {
                sql.append("AND scenic_spot = ? ");
                params.add(spotId);
            }

            sql.append("GROUP BY ip_location ");
            sql.append("LIMIT 10");

            List<Map<String, Object>> locationData = hiveJdbcTemplate.queryForList(sql.toString(), params.toArray());
            
            long totalVisitors = locationData.stream()
                .mapToLong(m -> ((Number) m.get("visitor_count")).longValue())
                .sum();

            List<Map<String, Object>> provinceDistribution = locationData.stream()
                .map(m -> {
                    Map<String, Object> province = new HashMap<>();
                    String locationName = m.get("ip_location") != null ? m.get("ip_location").toString() : "未知";
                    // 清理省份名称，去掉"省"、"市"等后缀
                    String provinceName = locationName.replaceAll("省$", "").replaceAll("市$", "");
                    province.put("province", provinceName);
                    province.put("source_province", provinceName);
                    province.put("city", provinceName);
                    province.put("source_city", provinceName);
                    province.put("visitor_count", m.get("visitor_count"));
                    province.put("count", m.get("visitor_count"));
                    long count = ((Number) m.get("visitor_count")).longValue();
                    province.put("percentage", totalVisitors > 0 ? Math.round(count * 1000.0 / totalVisitors) / 10.0 : 0.0);
                    return province;
                }).collect(Collectors.toList());
            
            List<Map<String, Object>> cityDistribution = locationData.stream()
                .map(m -> {
                    Map<String, Object> city = new HashMap<>();
                    String locationName = m.get("ip_location") != null ? m.get("ip_location").toString() : "未知";
                    String cityName = locationName.replaceAll("省$", "").replaceAll("市$", "");
                    city.put("city", cityName);
                    city.put("source_city", cityName);
                    city.put("visitor_count", m.get("visitor_count"));
                    city.put("count", m.get("visitor_count"));
                    return city;
                }).collect(Collectors.toList());

            result.put("totalVisitors", totalVisitors);
            result.put("provinceDistribution", provinceDistribution);
            result.put("cityDistribution", cityDistribution);
            
            redisCacheService.set(cacheKey, result, 3600);

        } catch (Exception e) {
            log.error("查询客源地分布失败", e);
        }

        return result;
    }

    @Override
    public Map<String, Object> getVisitorDemographics(String spotId, String startDate, String endDate) {
        log.info("查询游客年龄性别分布: spotId={}, startDate={}, endDate={}", spotId, startDate, endDate);
        
        // 注意：携程评论数据不包含用户年龄和性别信息
        // 这些信息需要通过NLP分析、用户画像推断或第三方数据源获取
        // 当前系统基于公开评论数据，无法提供真实的人口学特征分析
        Map<String, Object> result = new HashMap<>();
        result.put("available", false);
        result.put("message", "评论数据中不包含年龄性别信息，需要额外的数据源或NLP分析支持");
        result.put("genderDistribution", new HashMap<>());
        result.put("ageDistribution", new ArrayList<>());
        result.put("averageAge", 0);
        
        return result;
    }

    @Override
    public Map<String, Object> getReviewUserCount(String spotId) {
        log.info("查询打分人数统计: spotId={}", spotId);
        
        String cacheKey = "analysis:review:usercount:" + spotId;
        Object cached = redisCacheService.get(cacheKey);
        if (cached != null && cached instanceof Map) {
            log.info("从Redis缓存获取打分人数统计");
            @SuppressWarnings("unchecked")
            Map<String, Object> cachedMap = (Map<String, Object>) cached;
            return cachedMap;
        }

        Map<String, Object> result = new HashMap<>();

        try {
            // 查询所有景区的打分人数TOP10
            String sql = 
                "SELECT " +
                "    scenic_spot, " +
                "    COUNT(DISTINCT visitor_name) as unique_reviewers, " +
                "    COUNT(*) as total_reviews " +
                "FROM tourism_db.fuzhou_reviews_latest " +
                "GROUP BY scenic_spot " +
                "ORDER BY unique_reviewers DESC " +
                "LIMIT 10";
            
            List<Map<String, Object>> topList = hiveJdbcTemplate.queryForList(sql);
            result.put("topSpots", topList);
            
            // 计算总体统计
            String totalSql = 
                "SELECT " +
                "    COUNT(DISTINCT visitor_name) as total_unique_reviewers, " +
                "    COUNT(*) as total_reviews " +
                "FROM tourism_db.fuzhou_reviews_latest";
            Map<String, Object> totalStats = hiveJdbcTemplate.queryForMap(totalSql);
            result.put("totalUniqueReviewers", totalStats.get("total_unique_reviewers"));
            result.put("totalReviews", totalStats.get("total_reviews"));
            
            redisCacheService.set(cacheKey, result, 3600);

        } catch (Exception e) {
            log.error("查询打分人数统计失败", e);
        }

        return result;
    }
    
    @Override
    public Map<String, Object> getRecommendVisitTime(String spotId) {
        log.info("查询建议游玩时间(智能推荐算法): spotId={}", spotId);
        
        String cacheKey = "analysis:recommend:time:" + (spotId == null ? "all" : spotId);
        Object cached = redisCacheService.get(cacheKey);
        if (cached != null) {
            Map<String, Object> cachedMap = (Map<String, Object>) cached;
            return cachedMap;
        }

        Map<String, Object> result = new HashMap<>();

        try {
            if (spotId == null || spotId.trim().isEmpty()) {
                result.put("spotName", "福州全域");
            } else {
                result.put("spotName", spotId);
            }

            StringBuilder sql = new StringBuilder(
                "SELECT " +
                "    MONTH(travel_date) as month, " +
                "    COUNT(*) as visitor_count, " +
                "    AVG(rating) as avg_rating " +
                "FROM tourism_db.fuzhou_reviews_latest " +
                "WHERE 1=1 ");
            
            List<Object> params = new ArrayList<>();
            if (spotId != null && !spotId.trim().isEmpty()) {
                sql.append("AND scenic_spot = ? ");
                params.add(spotId);
            }
            
            sql.append("GROUP BY MONTH(travel_date) LIMIT 12");

            List<Map<String, Object>> monthlyData = hiveJdbcTemplate.query(
                sql.toString(), 
                params.toArray(),
                (rs, rowNum) -> {
                    Map<String, Object> map = new HashMap<>();
                    map.put("month", rs.getInt("month"));
                    map.put("visitor_count", rs.getLong("visitor_count"));
                    map.put("avg_rating", rs.getDouble("avg_rating"));
                    return map;
                });

            if (!monthlyData.isEmpty()) {
                Map<String, Object> forecastData = null;
                try {
                    forecastData = getTrafficForecast(spotId, 12);
                } catch (Exception e) {
                    log.warn("获取人流量预测数据失败，使用历史数据: {}", e.getMessage());
                }
                
                List<Map<String, Object>> monthScores = calculateMonthlyScores(monthlyData, forecastData);
                
                List<Map<String, Object>> recommendedMonths = monthScores.stream()
                    .sorted((a, b) -> Double.compare(
                        ((Number) b.get("totalScore")).doubleValue(),
                        ((Number) a.get("totalScore")).doubleValue()
                    ))
                    .limit(6)
                    .collect(Collectors.toList());

                long avgVisitors = monthlyData.stream()
                    .mapToLong(m -> ((Number) m.get("visitor_count")).longValue())
                    .sum() / monthlyData.size();
                
                List<Map<String, Object>> peakMonthsData = findPeakMonths(monthlyData, avgVisitors);
                List<Map<String, Object>> offPeakMonthsData = findOffPeakMonths(monthlyData, avgVisitors);
                
                List<String> peakMonths = peakMonthsData.stream()
                    .map(m -> (String) m.get("monthName"))
                    .collect(Collectors.toList());
                List<String> offPeakMonths = offPeakMonthsData.stream()
                    .map(m -> (String) m.get("monthName"))
                    .collect(Collectors.toList());
                
                result.put("recommendedMonths", recommendedMonths);
                result.put("peakMonths", peakMonths);
                result.put("peakMonthsDetail", peakMonthsData);
                result.put("offPeakMonths", offPeakMonths);
                result.put("offPeakMonthsDetail", offPeakMonthsData);
                result.put("bestVisitTime", recommendedMonths.isEmpty() ? "春秋季节" : 
                    recommendedMonths.get(0).get("monthName"));
                result.put("avgVisitors", avgVisitors);
                result.put("algorithmVersion", "综合评分模型v1.0");
            } else {
                result.put("recommendedMonths", new ArrayList<>());
                result.put("peakMonths", new ArrayList<>());
                result.put("offPeakMonths", new ArrayList<>());
                result.put("bestVisitTime", "暂无数据");
            }
            
            redisCacheService.set(cacheKey, result, 3600);

        } catch (Exception e) {
            log.error("查询建议游玩时间失败", e);
        }

        return result;
    }
    
    private List<Map<String, Object>> calculateMonthlyScores(
            List<Map<String, Object>> monthlyData, 
            Map<String, Object> forecastData) {
        
        List<Map<String, Object>> result = new ArrayList<>();
        
        long maxVisitors = monthlyData.stream()
            .mapToLong(m -> ((Number) m.get("visitor_count")).longValue())
            .max().orElse(1);
        long minVisitors = monthlyData.stream()
            .mapToLong(m -> ((Number) m.get("visitor_count")).longValue())
            .min().orElse(0);
        double avgVisitors = monthlyData.stream()
            .mapToLong(m -> ((Number) m.get("visitor_count")).longValue())
            .average().orElse(0);
        
        Map<Integer, Long> forecastMap = new HashMap<>();
        if (forecastData != null && forecastData.get("data") != null) {
            Map<String, Object> data = (Map<String, Object>) forecastData.get("data");
            if (data.get("forecast") != null) {
                List<Map<String, Object>> forecasts = (List<Map<String, Object>>) data.get("forecast");
                for (Map<String, Object> f : forecasts) {
                    String monthStr = (String) f.get("month");
                    if (monthStr != null && monthStr.contains("-")) {
                        int month = Integer.parseInt(monthStr.split("-")[1]);
                        Object predictedObj = f.get("predicted_visitors");
                        if (predictedObj != null) {
                            long predicted = ((Number) predictedObj).longValue();
                            forecastMap.put(month, predicted);
                        }
                    }
                }
            }
        }
        
        for (Map<String, Object> data : monthlyData) {
            int month = ((Number) data.get("month")).intValue();
            long visitorCount = ((Number) data.get("visitor_count")).longValue();
            double avgRating = ((Number) data.get("avg_rating")).doubleValue();
            
            double crowdScore = 0;
            if (maxVisitors > minVisitors) {
                crowdScore = 100 * (1 - (double)(visitorCount - minVisitors) / (maxVisitors - minVisitors));
            }
            
            double satisfactionScore = (avgRating / 5.0) * 100;
            
            double comfortScore = getSeasonComfortScore(month);
            
            double trendScore = 50;
            if (forecastMap.containsKey(month)) {
                long predictedVisitors = forecastMap.get(month);
                double growthRate = (double)(predictedVisitors - visitorCount) / visitorCount;
                if (growthRate < 0) {
                    trendScore = 100;
                } else if (growthRate < 0.1) {
                    trendScore = 80;
                } else if (growthRate < 0.3) {
                    trendScore = 60;
                } else {
                    trendScore = 40;
                }
            }
            
            double totalScore = crowdScore * 0.3 + satisfactionScore * 0.3 + 
                               comfortScore * 0.2 + trendScore * 0.2;
            
            String crowdLevel;
            if (visitorCount < avgVisitors * 0.7) {
                crowdLevel = "舒适";
            } else if (visitorCount < avgVisitors * 1.3) {
                crowdLevel = "适中";
            } else {
                crowdLevel = "拥挤";
            }
            
            Map<String, Object> monthScore = new HashMap<>();
            monthScore.put("month", month);
            monthScore.put("monthName", getMonthName(month));
            monthScore.put("visitorCount", visitorCount);
            monthScore.put("avgRating", Math.round(avgRating * 10.0) / 10.0);
            monthScore.put("crowdLevel", crowdLevel);
            monthScore.put("seasonType", getSeasonType(month));
            monthScore.put("totalScore", Math.round(totalScore * 10.0) / 10.0);
            monthScore.put("crowdScore", Math.round(crowdScore * 10.0) / 10.0);
            monthScore.put("satisfactionScore", Math.round(satisfactionScore * 10.0) / 10.0);
            monthScore.put("comfortScore", Math.round(comfortScore * 10.0) / 10.0);
            monthScore.put("trendScore", Math.round(trendScore * 10.0) / 10.0);
            
            if (forecastMap.containsKey(month)) {
                monthScore.put("predictedVisitors", forecastMap.get(month));
            }
            
            result.add(monthScore);
        }
        
        return result;
    }
    
    private double getSeasonComfortScore(int month) {
        if (month >= 3 && month <= 5) {
            return 90;
        } else if (month >= 9 && month <= 11) {
            return 95;
        } else if (month >= 6 && month <= 8) {
            return 60;
        } else {
            return 55;
        }
    }
    
    private String getMonthName(int month) {
        String[] months = {"", "1月", "2月", "3月", "4月", "5月", "6月", 
                          "7月", "8月", "9月", "10月", "11月", "12月"};
        return month >= 1 && month <= 12 ? months[month] : "";
    }

    private String getSeasonType(int month) {
        if (month >= 3 && month <= 5) return "春季";
        if (month >= 6 && month <= 8) return "夏季";
        if (month >= 9 && month <= 11) return "秋季";
        return "冬季";
    }

    private List<Map<String, Object>> findPeakMonths(List<Map<String, Object>> monthlyData, long avgVisitors) {
        return monthlyData.stream()
            .filter(m -> ((Number) m.get("visitor_count")).longValue() > avgVisitors * 1.5)
            .map(m -> {
                Map<String, Object> peak = new HashMap<>();
                int month = ((Number) m.get("month")).intValue();
                peak.put("month", month);
                peak.put("monthName", getMonthName(month));
                peak.put("visitorCount", m.get("visitor_count"));
                return peak;
            })
            .collect(Collectors.toList());
    }

    private List<Map<String, Object>> findOffPeakMonths(List<Map<String, Object>> monthlyData, long avgVisitors) {
        return monthlyData.stream()
            .filter(m -> ((Number) m.get("visitor_count")).longValue() < avgVisitors * 0.6)
            .map(m -> {
                Map<String, Object> offPeak = new HashMap<>();
                int month = ((Number) m.get("month")).intValue();
                offPeak.put("month", month);
                offPeak.put("monthName", getMonthName(month));
                offPeak.put("visitorCount", m.get("visitor_count"));
                return offPeak;
            })
            .collect(Collectors.toList());
    }

    @Override
    public Map<String, Object> getRatingDistribution(String spotId) {
        log.info("查询景区评分分布统计: spotId={}", spotId);
        
        // 设置Hive参数避免MapReduce任务
        try {
            hiveJdbcTemplate.execute("SET hive.fetch.task.conversion=more");
            hiveJdbcTemplate.execute("SET hive.fetch.task.aggr=true");
            hiveJdbcTemplate.execute("SET hive.fetch.task.conversion.threshold=1073741824");
        } catch (Exception e) {
            log.warn("设置Hive参数失败，继续执行查询", e);
        }
        
        String cacheKey = "analysis:rating:distribution:" + (spotId == null ? "all" : spotId);
        Object cached = redisCacheService.get(cacheKey);
        if (cached != null && cached instanceof Map) {
            log.info("从Redis缓存获取评分分布统计");
            return (Map<String, Object>) cached;
        }
        
        Map<String, Object> result = new HashMap<>();
        
        try {
            String latestPartition = getLatestPartition("scenic_spots");
            if (latestPartition.isEmpty()) {
                result.put("distribution", new ArrayList<>());
                result.put("totalCount", 0);
                return result;
            }
            
            // 查询分区表
            StringBuilder sql = new StringBuilder(
                "SELECT " +
                "    comment_score, " +
                "    COUNT(*) as count " +
                "FROM tourism_db.scenic_spots " +
                "WHERE dt = '" + latestPartition + "' AND comment_score IS NOT NULL ");
            
            List<Object> params = new ArrayList<>();
            
            if (spotId != null && !spotId.isEmpty()) {
                sql.append("AND scenic_spot = ? ");
                params.add(spotId);
            }
            
            sql.append("GROUP BY comment_score LIMIT 100");
            
            List<Map<String, Object>> rawData = hiveJdbcTemplate.queryForList(sql.toString(), params.toArray());
            
            // 统计总数
            long totalCount = rawData.stream()
                .mapToLong(m -> ((Number) m.get("count")).longValue())
                .sum();
            
            // 按评分区间分组统计
            Map<String, Integer> rangeCount = new LinkedHashMap<>();
            rangeCount.put("4.5-5.0分", 0);
            rangeCount.put("4.0-4.5分", 0);
            rangeCount.put("3.5-4.0分", 0);
            rangeCount.put("3.0-3.5分", 0);
            rangeCount.put("3.0分以下", 0);
            
            for (Map<String, Object> row : rawData) {
                double score = ((Number) row.get("comment_score")).doubleValue();
                int count = ((Number) row.get("count")).intValue();
                
                if (score >= 4.5) {
                    rangeCount.put("4.5-5.0分", rangeCount.get("4.5-5.0分") + count);
                } else if (score >= 4.0) {
                    rangeCount.put("4.0-4.5分", rangeCount.get("4.0-4.5分") + count);
                } else if (score >= 3.5) {
                    rangeCount.put("3.5-4.0分", rangeCount.get("3.5-4.0分") + count);
                } else if (score >= 3.0) {
                    rangeCount.put("3.0-3.5分", rangeCount.get("3.0-3.5分") + count);
                } else {
                    rangeCount.put("3.0分以下", rangeCount.get("3.0分以下") + count);
                }
            }
            
            // 构建返回结果
            List<Map<String, Object>> distribution = new ArrayList<>();
            for (Map.Entry<String, Integer> entry : rangeCount.entrySet()) {
                Map<String, Object> item = new HashMap<>();
                int count = entry.getValue();
                double percentage = totalCount > 0 ? (count * 100.0 / totalCount) : 0;
                
                item.put("label", entry.getKey());
                item.put("count", count);
                item.put("percentage", Math.round(percentage * 100.0) / 100.0);
                distribution.add(item);
            }
            
            result.put("distribution", distribution);
            result.put("totalCount", totalCount);
            result.put("spotId", spotId);
            
            log.info("景区评分分布统计完成: 总数={}", totalCount);
            redisCacheService.set(cacheKey, result, 3600);
            
        } catch (Exception e) {
            log.error("查询景区评分分布统计失败", e);
            result.put("distribution", new ArrayList<>());
            result.put("totalCount", 0);
        }
        
        return result;
    }

    @Override
    public Map<String, Object> getTrafficAnalysis(String spotId, Integer year) {
        log.info("查询人流量分析: spotId={}, year={}", spotId, year);
        
        // 设置Hive参数避免MapReduce任务
        try {
            hiveJdbcTemplate.execute("SET hive.fetch.task.conversion=more");
            hiveJdbcTemplate.execute("SET hive.fetch.task.aggr=true");
            hiveJdbcTemplate.execute("SET hive.fetch.task.conversion.threshold=1073741824");
        } catch (Exception e) {
            log.warn("设置Hive参数失败，继续执行查询", e);
        }
        
        String cacheKey = "analysis:traffic:" + spotId + ":" + year;
        Object cached = redisCacheService.get(cacheKey);
        if (cached != null && cached instanceof Map) {
            log.info("从Redis缓存获取人流量分析");
            return (Map<String, Object>) cached;
        }
        
        Map<String, Object> result = new HashMap<>();
        
        try {
            // 使用字符串匹配替代YEAR()函数避免MapReduce任务
            // 移除ORDER BY避免触发MapReduce，数据排序交给Flask处理
            String sql = "SELECT scenic_spot, city, rating, travel_date, review_date, visitor_name " +
                         "FROM tourism_db.fuzhou_reviews_latest " +
                         "WHERE 1=1 ";
            
            List<Object> params = new ArrayList<>();
            
            if (spotId != null && !spotId.isEmpty()) {
                sql += "AND scenic_spot = ? ";
                params.add(spotId);
            }
            
            if (year != null) {
                // 使用字符串匹配年份，避免YEAR()函数触发MapReduce
                sql += "AND travel_date >= ? AND travel_date < ? ";
                params.add(year + "-01-01");
                params.add((year + 1) + "-01-01");
            }
            
            // 添加LIMIT保护，防止数据量过大
            sql += "LIMIT 50000";
            
            List<Map<String, Object>> reviews = hiveJdbcTemplate.queryForList(sql, params.toArray());
            
            String flaskUrl = "http://localhost:5000/api/analysis/traffic";
            
            org.springframework.web.client.RestTemplate restTemplate = new org.springframework.web.client.RestTemplate();
            Map<String, Object> requestBody = new HashMap<>();
            requestBody.put("reviews", reviews);
            requestBody.put("year", year);
            
            Map<String, Object> response = restTemplate.postForObject(flaskUrl, requestBody, Map.class);
            
            if (response != null && "200".equals(String.valueOf(response.get("code")))) {
                result = (Map<String, Object>) response.get("data");
                result.put("spotId", spotId);
                result.put("year", year);
                
                redisCacheService.set(cacheKey, result, 3600);
            } else {
                result.put("success", false);
                result.put("message", response != null ? response.get("msg") : "分析失败");
            }
            
        } catch (Exception e) {
            log.error("人流量分析失败", e);
            result.put("success", false);
            result.put("message", "分析失败: " + e.getMessage());
        }
        
        return result;
    }

    @Override
    public Map<String, Object> getTrafficForecast(String spotId, Integer monthsAhead) {
        log.info("查询人流量预测: spotId={}, monthsAhead={}", spotId, monthsAhead);
        
        String cacheKey = "forecast:traffic:" + spotId + ":" + monthsAhead;
        Object cached = redisCacheService.get(cacheKey);
        if (cached != null && cached instanceof Map) {
            log.info("从Redis缓存获取人流量预测");
            return (Map<String, Object>) cached;
        }
        
        Map<String, Object> result = new HashMap<>();
        
        try {
            // 查询历史评论数据（至少需要12个月数据）
            // 移除ORDER BY避免触发MapReduce，数据排序交给Flask处理
            String sql = "SELECT scenic_spot, city, rating, travel_date, review_date, visitor_name " +
                         "FROM tourism_db.fuzhou_reviews_latest " +
                         "WHERE 1=1 ";
            
            List<Object> params = new ArrayList<>();
            
            if (spotId != null && !spotId.isEmpty()) {
                sql += "AND scenic_spot = ? ";
                params.add(spotId);
            }
            
            // 添加LIMIT保护，防止数据量过大
            sql += "LIMIT 50000";
            
            List<Map<String, Object>> reviews = hiveJdbcTemplate.queryForList(sql, params.toArray());
            
            if (reviews.size() < 12) {
                result.put("success", false);
                result.put("message", "历史数据不足12个月，无法进行预测");
                return result;
            }
            
            // 调用Flask Python服务进行预测
            String flaskUrl = "http://localhost:5000/api/forecast/traffic";
            
            org.springframework.web.client.RestTemplate restTemplate = new org.springframework.web.client.RestTemplate();
            Map<String, Object> requestBody = new HashMap<>();
            requestBody.put("reviews", reviews);
            requestBody.put("months_ahead", monthsAhead);
            
            Map<String, Object> response = restTemplate.postForObject(flaskUrl, requestBody, Map.class);
            
            if (response != null && "200".equals(String.valueOf(response.get("code")))) {
                result = (Map<String, Object>) response.get("data");
                result.put("spotId", spotId);
                result.put("monthsAhead", monthsAhead);
                
                // 缓存结果（预测结果缓存时间较短）
                redisCacheService.set(cacheKey, result, 1800);
            } else {
                result.put("success", false);
                result.put("message", response != null ? response.get("msg") : "预测失败");
            }
            
        } catch (Exception e) {
            log.error("人流量预测失败", e);
            result.put("success", false);
            result.put("message", "预测失败: " + e.getMessage());
        }
        
        return result;
    }
}
