package com.tourism.tourismspringboot.vo;

import lombok.Data;
import java.io.Serializable;
import java.util.List;

/**
 * 推荐游玩时间VO
 */
@Data
public class RecommendVisitTimeVO implements Serializable {
    
    private String spotName;
    
    private String bestVisitTime;
    
    private List<RecommendMonth> recommendedMonths;
    
    private List<String> peakMonths;
    
    private List<String> offPeakMonths;
    
    @Data
    public static class RecommendMonth {
        private Integer month;
        private String monthName;
        private Long visitorCount;
        private Double avgRating;
        private String crowdLevel;
        private String seasonType;
    }
}
