package com.tourism.tourismspringboot.service;

import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.stereotype.Service;

import java.util.Set;
import java.util.concurrent.TimeUnit;

/**
 * Redis缓存服务
 */
@Slf4j
@Service
public class RedisCacheService {

    @Autowired
    private RedisTemplate<String, Object> redisTemplate;

    private static final long DEFAULT_EXPIRE_TIME = 24 * 60 * 60;

    public Object get(String key) {
        try {
            return redisTemplate.opsForValue().get(key);
        } catch (Exception e) {
            log.error("Redis获取缓存失败: key={}", key, e);
            return null;
        }
    }

    public void set(String key, Object value) {
        set(key, value, DEFAULT_EXPIRE_TIME);
    }

    public void set(String key, Object value, long expireSeconds) {
        try {
            redisTemplate.opsForValue().set(key, value, expireSeconds, TimeUnit.SECONDS);
            log.debug("Redis缓存设置成功: key={}, expire={}s", key, expireSeconds);
        } catch (Exception e) {
            log.error("Redis设置缓存失败: key={}", key, e);
        }
    }

    public void delete(String key) {
        try {
            redisTemplate.delete(key);
            log.info("Redis删除缓存: key={}", key);
        } catch (Exception e) {
            log.error("Redis删除缓存失败: key={}", key, e);
        }
    }

    public void deleteByPattern(String pattern) {
        try {
            Set<String> keys = redisTemplate.keys(pattern);
            if (keys != null && !keys.isEmpty()) {
                Long deleted = redisTemplate.delete(keys);
                log.info("Redis批量删除缓存: pattern={}, count={}", pattern, deleted);
            }
        } catch (Exception e) {
            log.error("Redis批量删除缓存失败: pattern={}", pattern, e);
        }
    }

    public boolean exists(String key) {
        try {
            return Boolean.TRUE.equals(redisTemplate.hasKey(key));
        } catch (Exception e) {
            log.error("Redis检查key存在失败: key={}", key, e);
            return false;
        }
    }

    public void clearScenicCache() {
        deleteByPattern("scenic:*");
    }

    public void clearAnalysisCache() {
        deleteByPattern("analysis:*");
    }

    public void clearAllCache() {
        clearScenicCache();
        clearAnalysisCache();
        log.info("清除所有景区数据缓存");
    }
}
