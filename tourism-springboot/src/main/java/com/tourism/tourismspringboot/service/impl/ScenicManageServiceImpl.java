package com.tourism.tourismspringboot.service.impl;

import com.tourism.tourismspringboot.service.IScenicManageService;
import com.tourism.tourismspringboot.service.RedisCacheService;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;

import java.util.*;

@Slf4j
@Service
public class ScenicManageServiceImpl implements IScenicManageService {

    @Autowired
    @Qualifier("hiveJdbcTemplate")
    private JdbcTemplate hiveJdbcTemplate;
    
    @Autowired
    private RedisCacheService redisCacheService;

    @Override
    public Map<String, Object> getScenicList(Integer page, Integer pageSize, String keyword, String sightLevel) {
        log.info("景区管理-查询景区列表: page={}, pageSize={}, keyword={}, sightLevel={}", page, pageSize, keyword, sightLevel);
        
        String cacheKey = "scenic:list:" + page + ":" + pageSize + ":" + (keyword != null ? keyword : "all") + ":" + (sightLevel != null ? sightLevel : "all");
        Object cached = redisCacheService.get(cacheKey);
        if (cached != null) {
            log.info("从Redis缓存获取景区列表");
            // 类型安全检查
            if (cached instanceof Map) {
                @SuppressWarnings("unchecked")
                Map<String, Object> cachedMap = (Map<String, Object>) cached;
                return cachedMap;
            } else {
                log.warn("缓存数据类型不匹配，删除旧缓存: cacheKey={}, type={}", cacheKey, cached.getClass().getName());
                redisCacheService.delete(cacheKey);
            }
        }
        
        Map<String, Object> result = new HashMap<>();
        
        try {
            // 获取最新分区
            String latestPartition = getLatestPartition("scenic_spots");
            log.info("使用景点数据分区: {}", latestPartition);
            
            // 从scenic_spots表获取景点基本信息，关联fuzhou_reviews获取评论统计
            StringBuilder countSql = new StringBuilder(
                "SELECT COUNT(DISTINCT s.scenic_spot) as total " +
                "FROM tourism_db.scenic_spots s " +
                "WHERE s.dt = '" + latestPartition + "'"
            );
            
            StringBuilder dataSql = new StringBuilder(
                "SELECT " +
                "    s.scenic_spot as scenicspot, " +
                "    s.business_id as businessid, " +
                "    s.city, " +
                "    s.zone_name as zonename, " +
                "    s.comment_score as commentscore, " +
                "    s.heat_score as heatscore, " +
                "    s.sight_level as sightlevel, " +
                "    s.market_price as marketprice, " +
                "    s.is_free as isfree, " +
                "    s.cover_image_url as coverimageurl, " +
                "    s.detail_url as detailurl, " +
                "    s.latitude, " +
                "    s.longitude, " +
                "    s.tag_name_list as tagnamelist, " +
                "    s.short_features as shortfeatures, " +
                "    COUNT(r.review_content) as reviewcount, " +
                "    ROUND(AVG(r.rating), 1) as avgrating, " +
                "    COUNT(DISTINCT r.visitor_name) as visitorcount " +
                "FROM tourism_db.scenic_spots s " +
                "LEFT JOIN tourism_db.fuzhou_reviews r ON s.scenic_spot = r.scenic_spot " +
                "WHERE s.dt = '" + latestPartition + "'"
            );
            
            if (keyword != null && !keyword.trim().isEmpty()) {
                String condition = " AND s.scenic_spot LIKE '%" + keyword.replace("'", "''") + "%'";
                countSql.append(condition);
                dataSql.append(condition);
            }
            
            if (sightLevel != null && !sightLevel.trim().isEmpty()) {
                String levelCondition = " AND s.sight_level = '" + sightLevel.replace("'", "''") + "'";
                countSql.append(levelCondition);
                dataSql.append(levelCondition);
            }
            
            dataSql.append(" GROUP BY s.scenic_spot, s.business_id, s.city, s.zone_name, s.comment_score, ");
            dataSql.append("s.heat_score, s.sight_level, s.market_price, s.is_free, s.cover_image_url, s.detail_url, ");
            dataSql.append("s.latitude, s.longitude, s.tag_name_list, s.short_features ");
            
            int offset = (page - 1) * pageSize;
            dataSql.append("ORDER BY reviewcount DESC LIMIT ").append(pageSize).append(" OFFSET ").append(offset);
            
            Long total = hiveJdbcTemplate.queryForObject(countSql.toString(), Long.class);
            
            List<Map<String, Object>> rawList = hiveJdbcTemplate.queryForList(dataSql.toString());
            
            // 转换字段名为驼峰命名
            List<Map<String, Object>> list = rawList.stream()
                .map(row -> {
                    Map<String, Object> item = new HashMap<>();
                    row.forEach((key, value) -> {
                        // 将Hive返回的小写字段名转为驼峰
                        String camelKey = toCamelCase(key.toString());
                        item.put(camelKey, value);
                    });
                    return item;
                })
                .collect(java.util.stream.Collectors.toList());
            
            result.put("total", total != null ? total : 0);
            result.put("page", page);
            result.put("pageSize", pageSize);
            result.put("list", list);
            
            redisCacheService.set(cacheKey, result, 3600);
            
        } catch (Exception e) {
            log.error("查询景区列表失败", e);
            result.put("total", 0);
            result.put("page", page);
            result.put("pageSize", pageSize);
            result.put("list", new ArrayList<>());
        }
        
        return result;
    }

    @Override
    public Map<String, Object> getScenicDetail(String spotName) {
        log.info("景区管理-查询景区详情: spotName={}", spotName);
        
        String cacheKey = "scenic:detail:" + spotName;
        Object cached = redisCacheService.get(cacheKey);
        if (cached != null) {
            log.info("从Redis缓存获取景区详情: {}", spotName);
            if (cached instanceof Map) {
                @SuppressWarnings("unchecked")
                Map<String, Object> cachedMap = (Map<String, Object>) cached;
                return cachedMap;
            } else {
                log.warn("缓存数据类型不匹配，删除旧缓存: cacheKey={}, type={}", cacheKey, cached.getClass().getName());
                redisCacheService.delete(cacheKey);
            }
        }
        
        Map<String, Object> result = new HashMap<>();
        
        try {
            // 获取最新分区
            String latestPartition = getLatestPartition("scenic_spots");
            
            // 从scenic_spots表获取景点完整信息
            String spotSql = 
                "SELECT " +
                "    s.scenic_spot as scenicSpot, " +
                "    s.business_id as businessId, " +
                "    s.city, " +
                "    s.zone_name as zoneName, " +
                "    s.comment_score as commentScore, " +
                "    s.heat_score as heatScore, " +
                "    s.sight_level as sightLevel, " +
                "    s.tag_name_list as tagNameList, " +
                "    s.sight_category_info as sightCategoryInfo, " +
                "    s.cover_image_url as coverImageUrl, " +
                "    s.market_price as marketPrice, " +
                "    s.is_free as isFree, " +
                "    s.short_features as shortFeatures, " +
                "    s.latitude, " +
                "    s.longitude, " +
                "    s.detail_url as detailUrl " +
                "FROM tourism_db.scenic_spots s " +
                "WHERE s.dt = '" + latestPartition + "' AND s.scenic_spot = '" + spotName.replace("'", "''") + "'";
            
            Map<String, Object> spotInfo = hiveJdbcTemplate.queryForMap(spotSql);
            result.putAll(spotInfo);
            
            // 关联评论统计数据
            String reviewStatSql = 
                "SELECT " +
                "    COUNT(*) as reviewCount, " +
                "    ROUND(AVG(rating), 1) as avgRating, " +
                "    COUNT(DISTINCT visitor_name) as visitorCount, " +
                "    MIN(travel_date) as firstReviewDate, " +
                "    MAX(travel_date) as lastReviewDate " +
                "FROM tourism_db.fuzhou_reviews " +
                "WHERE scenic_spot = '" + spotName.replace("'", "''") + "'";
            
            Map<String, Object> reviewStats = hiveJdbcTemplate.queryForMap(reviewStatSql);
            result.putAll(reviewStats);
            
            redisCacheService.set(cacheKey, result, 3600);
            
            String ratingDistSql = 
                "SELECT " +
                "    CAST(rating AS INT) as rating_level, " +
                "    COUNT(*) as count " +
                "FROM tourism_db.fuzhou_reviews " +
                "WHERE scenic_spot = ? " +
                "GROUP BY CAST(rating AS INT) " +
                "ORDER BY rating_level DESC";
            
            List<Map<String, Object>> ratingDist = hiveJdbcTemplate.queryForList(ratingDistSql, spotName);
            result.put("ratingDistribution", ratingDist);
            
        } catch (Exception e) {
            log.error("查询景区详情失败", e);
        }
        
        return result;
    }

    private String toCamelCase(String input) {
        if (input == null || input.isEmpty()) {
            return input;
        }
        // 已经是驼峰就直接返回
        if (!input.contains("_")) {
            return input;
        }
        StringBuilder result = new StringBuilder();
        boolean capitalizeNext = false;
        for (char c : input.toCharArray()) {
            if (c == '_') {
                capitalizeNext = true;
            } else {
                if (capitalizeNext) {
                    result.append(Character.toUpperCase(c));
                    capitalizeNext = false;
                } else {
                    result.append(c);
                }
            }
        }
        return result.toString();
    }
    
    private String getLatestPartition(String tableName) {
        try {
            String sql = "SHOW PARTITIONS tourism_db." + tableName;
            List<String> partitions = hiveJdbcTemplate.queryForList(sql, String.class);
            if (partitions.isEmpty()) {
                return "";
            }
            // 获取最新分区（排序后的最后一个）
            partitions.sort(String::compareTo);
            String latestPartition = partitions.get(partitions.size() - 1);
            // 提取dt=xxx中的值
            return latestPartition.replace("dt=", "");
        } catch (Exception e) {
            log.error("获取最新分区失败: {}", e.getMessage());
            return "20251213_170012"; // 默认分区
        }
    }

    @Override
    public Map<String, Object> getReviews(String spotName, Integer page, Integer pageSize) {
        log.info("景区管理-查询景区评论: spotName={}, page={}, pageSize={}", spotName, page, pageSize);
        
        String cacheKey = "scenic:reviews:" + spotName + ":" + page + ":" + pageSize;
        Object cached = redisCacheService.get(cacheKey);
        if (cached != null && cached instanceof Map) {
            log.info("从Redis缓存获取景区评论: {}", spotName);
            @SuppressWarnings("unchecked")
            Map<String, Object> cachedMap = (Map<String, Object>) cached;
            return cachedMap;
        }
        
        Map<String, Object> result = new HashMap<>();
        
        try {
            String countSql = "SELECT COUNT(*) as total FROM tourism_db.fuzhou_reviews WHERE scenic_spot = ?";
            Long total = hiveJdbcTemplate.queryForObject(countSql, new Object[]{spotName}, Long.class);
            
            // Hive不支持LIMIT使用占位符，需要使用字符串拼接
            int offset = (page - 1) * pageSize;
            String dataSql = 
                "SELECT " +
                "    visitor_name as userName, " +
                "    rating as score, " +
                "    review_content as content, " +
                "    travel_date as time " +
                "FROM tourism_db.fuzhou_reviews " +
                "WHERE scenic_spot = '" + spotName.replace("'", "''") + "' " +
                "ORDER BY time DESC " +
                "LIMIT " + pageSize + " OFFSET " + offset;
            
            List<Map<String, Object>> list = hiveJdbcTemplate.queryForList(dataSql);
            
            log.info("查询到{}的评论数据: total={}, 返回{}条", spotName, total, list.size());
            
            result.put("total", total != null ? total : 0);
            result.put("page", page);
            result.put("pageSize", pageSize);
            result.put("list", list);
            
            // 写入Redis缓存
            redisCacheService.set(cacheKey, result, 3600);
            
        } catch (Exception e) {
            log.error("查询景区评论失败: spotName={}", spotName, e);
            result.put("total", 0);
            result.put("page", page);
            result.put("pageSize", pageSize);
            result.put("list", new ArrayList<>());
        }
        
        return result;
    }
}
