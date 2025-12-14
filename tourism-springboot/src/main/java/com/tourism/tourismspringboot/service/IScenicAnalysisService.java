package com.tourism.tourismspringboot.service;

import com.tourism.tourismspringboot.vo.AnalysisOverviewVO;
import com.tourism.tourismspringboot.vo.ScenicVO;
import java.util.List;
import java.util.Map;

/**
 * 景区数据分析服务接口
 */
public interface IScenicAnalysisService {

    /**
     * 获取数据概览
     */
    AnalysisOverviewVO getOverview();

    /**
     * 获取景区列表
     */
    List<ScenicVO> getScenicList(Integer page, Integer pageSize);

    /**
     * 获取景区列表（带分页）
     */
    Map<String, Object> getScenicListWithPage(Integer page, Integer pageSize);

    /**
     * 获取景区详细信息
     */
    Map<String, Object> getScenicDetail(String spotId);

    /**
     * 获取客流量统计
     */
    List<Map<String, Object>> getVisitorCount(String spotId, String startDate, String endDate);

    /**
     * 获取客流量趋势对比
     */
    Map<String, Object> getVisitorTrendCompare(List<String> spotIds, String startDate, String endDate);

    /**
     * 获取评价统计
     */
    Map<String, Object> getReviewStats(String spotId);

    /**
     * 获取评价列表
     */
    Map<String, Object> getReviews(String spotId, Integer page, Integer pageSize, Integer rating, String sort);

    /**
     * 获取评价关键词分析
     */
    Map<String, Object> getReviewKeywords(String spotId, Integer limit);

    /**
     * 获取季节性分析
     */
    Map<String, Object> getSeasonPattern(String spotId, Integer year);

    /**
     * 获取节假日影响分析
     */
    Map<String, Object> getHolidayImpact(String spotId, Integer year);

    /**
     * 获取景区排行榜
     */
    List<Map<String, Object>> getScenicRanking(String rankType, Integer limit);

    /**
     * 获取景区排行榜（带周期）
     */
    Map<String, Object> getScenicRankingWithPeriod(String rankType, String rankPeriod, Integer limit);

    /**
     * 获取客源地分布
     */
    Map<String, Object> getVisitorSource(String spotId, String startDate, String endDate);

    /**
     * 获取游客年龄性别分布
     */
    Map<String, Object> getVisitorDemographics(String spotId, String startDate, String endDate);

    /**
     * 获取打分人数统计
     */
    Map<String, Object> getReviewUserCount(String spotId);

    /**
     * 获取建议游玩时间
     */
    Map<String, Object> getRecommendVisitTime(String spotId);
    
    /**
     * 获取人流量分析
     * 基于历史评论数据分析月度人流量趋势
     */
    Map<String, Object> getTrafficAnalysis(String spotId, Integer year);
    
    /**
     * 获取人流量预测
     * 基于ARIMA模型预测未来人流量
     */
    Map<String, Object> getTrafficForecast(String spotId, Integer monthsAhead);
    
    /**
     * 获取评分分布统计
     * 基于实际Hive数据统计各星级评分占比
     */
    Map<String, Object> getRatingDistribution(String spotId);
}
