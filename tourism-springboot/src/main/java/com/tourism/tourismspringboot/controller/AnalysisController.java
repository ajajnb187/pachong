package com.tourism.tourismspringboot.controller;

import java.util.List;
import java.util.Map;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.CrossOrigin;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import com.tourism.tourismspringboot.common.Result;
import com.tourism.tourismspringboot.service.IScenicAnalysisService;
import com.tourism.tourismspringboot.vo.AnalysisOverviewVO;
import com.tourism.tourismspringboot.vo.ScenicVO;

import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;

/**
 * 数据分析控制器
 * 提供福州旅游景区数据分析API接口
 */
@Tag(name = "数据分析接口")
@RestController
@RequestMapping("/api/analysis")
@CrossOrigin
public class AnalysisController {

    @Autowired
    private IScenicAnalysisService scenicAnalysisService;

    @Operation(summary = "数据概览")
    @GetMapping("/overview")
    public Result<AnalysisOverviewVO> getOverview() {
        AnalysisOverviewVO overview = scenicAnalysisService.getOverview();
        return Result.success(overview);
    }

    @Operation(summary = "景区列表")
    @GetMapping("/scenic/list")
    public Result<List<ScenicVO>> getScenicList(
            @Parameter(description = "页码") @RequestParam(defaultValue = "1") Integer page,
            @Parameter(description = "每页数量") @RequestParam(defaultValue = "10") Integer pageSize) {
        List<ScenicVO> list = scenicAnalysisService.getScenicList(page, pageSize);
        return Result.success(list);
    }

    @Operation(summary = "客流量统计")
    @GetMapping("/visitor-count")
    public Result<List<Map<String, Object>>> getVisitorCount(
            @Parameter(description = "景区ID") @RequestParam String spotId,
            @Parameter(description = "开始日期") @RequestParam String startDate,
            @Parameter(description = "结束日期") @RequestParam String endDate) {
        List<Map<String, Object>> data = scenicAnalysisService.getVisitorCount(spotId, startDate, endDate);
        return Result.success(data);
    }

    @Operation(summary = "评价统计")
    @GetMapping("/review-stats")
    public Result<Map<String, Object>> getReviewStats(
            @Parameter(description = "景区ID") @RequestParam String spotId) {
        Map<String, Object> stats = scenicAnalysisService.getReviewStats(spotId);
        return Result.success(stats);
    }

    @Operation(summary = "季节性分析")
    @GetMapping("/season-pattern")
    public Result<Map<String, Object>> getSeasonPattern(
            @Parameter(description = "景区ID") @RequestParam String spotId,
            @Parameter(description = "年份") @RequestParam Integer year) {
        Map<String, Object> pattern = scenicAnalysisService.getSeasonPattern(spotId, year);
        return Result.success(pattern);
    }

    @Operation(summary = "景区排行榜")
    @GetMapping("/scenic/ranking")
    public Result<List<Map<String, Object>>> getScenicRanking(
            @Parameter(description = "排行类型:visitor-游客量,rating-评分") @RequestParam(defaultValue = "visitor") String rankType,
            @Parameter(description = "返回数量") @RequestParam(defaultValue = "10") Integer limit) {
        List<Map<String, Object>> ranking = scenicAnalysisService.getScenicRanking(rankType, limit);
        return Result.success(ranking);
    }

    @Operation(summary = "客源地分布")
    @GetMapping("/visitor-source")
    public Result<Map<String, Object>> getVisitorSource(
            @Parameter(description = "景区ID") @RequestParam(required = false) String spotId) {
        Map<String, Object> source = scenicAnalysisService.getVisitorSource(spotId, null, null);
        return Result.success(source);
    }

    @Operation(summary = "游客年龄性别分布")
    @GetMapping("/visitor-demographics")
    public Result<Map<String, Object>> getVisitorDemographics(
            @Parameter(description = "景区ID") @RequestParam(required = false) String spotId) {
        Map<String, Object> demographics = scenicAnalysisService.getVisitorDemographics(spotId, null, null);
        return Result.success(demographics);
    }

    @Operation(summary = "打分人数统计")
    @GetMapping("/review-user-count")
    public Result<Map<String, Object>> getReviewUserCount(
            @Parameter(description = "景区ID") @RequestParam(required = false) String spotId) {
        Map<String, Object> userCount = scenicAnalysisService.getReviewUserCount(spotId);
        return Result.success(userCount);
    }

    @Operation(summary = "建议游玩时间")
    @GetMapping("/recommend-visit-time")
    public Result<Map<String, Object>> getRecommendVisitTime(
            @Parameter(description = "景区ID") @RequestParam String spotId) {
        Map<String, Object> recommend = scenicAnalysisService.getRecommendVisitTime(spotId);
        return Result.success(recommend);
    }
}
