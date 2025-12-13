package com.tourism.tourismspringboot.controller;

import com.tourism.tourismspringboot.common.Result;
import com.tourism.tourismspringboot.service.IScenicManageService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@Slf4j
@Tag(name = "景区管理接口")
@RestController
@RequestMapping("/api/scenic-manage")
@CrossOrigin
public class ScenicManageController {

    @Autowired
    private IScenicManageService scenicManageService;

    @Operation(summary = "获取景区列表（分页）")
    @GetMapping("/list")
    public Result getScenicList(
            @RequestParam(defaultValue = "1") Integer page,
            @RequestParam(defaultValue = "10") Integer pageSize,
            @RequestParam(required = false) String keyword,
            @RequestParam(required = false) String sightLevel) {
        log.info("获取景区列表: page={}, pageSize={}, keyword={}, sightLevel={}", page, pageSize, keyword, sightLevel);
        Map<String, Object> result = scenicManageService.getScenicList(page, pageSize, keyword, sightLevel);
        return Result.success(result);
    }

    @Operation(summary = "获取景区详情")
    @GetMapping("/detail/{spotName}")
    public Result getScenicDetail(@PathVariable String spotName) {
        log.info("获取景区详情: spotName={}", spotName);
        Map<String, Object> result = scenicManageService.getScenicDetail(spotName);
        return Result.success(result);
    }

    @Operation(summary = "获取景区评论列表")
    @GetMapping("/reviews/{spotName}")
    public Result getReviews(
            @PathVariable String spotName,
            @RequestParam(defaultValue = "1") Integer page,
            @RequestParam(defaultValue = "10") Integer pageSize) {
        log.info("获取景区评论: spotName={}, page={}, pageSize={}", spotName, page, pageSize);
        Map<String, Object> result = scenicManageService.getReviews(spotName, page, pageSize);
        return Result.success(result);
    }
}
