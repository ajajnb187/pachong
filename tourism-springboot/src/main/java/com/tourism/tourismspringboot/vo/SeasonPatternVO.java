package com.tourism.tourismspringboot.vo;

import lombok.Data;
import java.io.Serializable;
import java.util.List;

/**
 * 季节模式分析VO
 */
@Data
public class SeasonPatternVO implements Serializable {
    
    private String spotName;
    
    private Integer year;
    
    private List<MonthlyStats> monthlyStats;
    
    @Data
    public static class MonthlyStats {
        private Integer month;
        private Long visitorCount;
        private Double avgRating;
        private String seasonType;
    }
}
