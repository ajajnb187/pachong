package com.tourism.tourismspringboot.vo;

import lombok.Data;
import java.io.Serializable;
import java.util.List;

/**
 * 数据概览VO
 */
@Data
public class AnalysisOverviewVO implements Serializable {
    
    private Long totalScenicSpots;
    
    private Long totalReviews;
    
    private Double avgRating;
    
    private String dataUpdateTime;
    
    private TodayStats todayStats;
    
    private List<HotSpot> hotSpots;
    
    @Data
    public static class TodayStats {
        private Long newReviews;
        private Long newVisitors;
    }
    
    @Data
    public static class HotSpot {
        private String spotName;
        private Long todayVisitors;
    }
}
