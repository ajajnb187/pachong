package com.tourism.tourismspringboot.vo;

import lombok.Data;
import java.io.Serializable;
import java.util.List;

/**
 * 数据概览VO
 * 对应前端Dashboard页面的overview数据需求
 */
@Data
public class AnalysisOverviewVO implements Serializable {
    
    // 前端字段: totalSpots
    private Long totalSpots;
    
    // 前端字段: totalReviews  
    private Long totalReviews;
    
    // 前端字段: averageRating
    private Double averageRating;
    
    // 前端字段: totalReviewers (唯一游客数)
    private Long totalReviewers;
    
    private String dataUpdateTime;
    
    // 热门景区数据（Dashboard右侧榜单）
    private List<HotSpot> hotSpots;
    
    @Data
    public static class HotSpot {
        private String name;      // 景区名称
        private Double rating;    // 评分
    }
}
