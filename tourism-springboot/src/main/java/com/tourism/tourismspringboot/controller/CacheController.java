package com.tourism.tourismspringboot.controller;

import com.tourism.tourismspringboot.common.Result;
import com.tourism.tourismspringboot.service.RedisCacheService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

/**
 * 缓存管理控制器
 */
@Slf4j
@Tag(name = "缓存管理接口")
@RestController
@RequestMapping("/api/cache")
@CrossOrigin
public class CacheController {

    @Autowired
    private RedisCacheService redisCacheService;

    @Operation(summary = "清除所有缓存")
    @DeleteMapping("/clear-all")
    public Result<String> clearAll() {
        log.info("清除所有缓存");
        redisCacheService.clearAllCache();
        return Result.success("所有缓存已清除");
    }

    @Operation(summary = "清除景区数据缓存")
    @DeleteMapping("/clear-scenic")
    public Result<String> clearScenic() {
        log.info("清除景区数据缓存");
        redisCacheService.clearScenicCache();
        return Result.success("景区数据缓存已清除");
    }

    @Operation(summary = "清除分析数据缓存")
    @DeleteMapping("/clear-analysis")
    public Result<String> clearAnalysis() {
        log.info("清除分析数据缓存");
        redisCacheService.clearAnalysisCache();
        return Result.success("分析数据缓存已清除");
    }
}
