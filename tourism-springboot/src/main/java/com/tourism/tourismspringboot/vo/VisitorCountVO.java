package com.tourism.tourismspringboot.vo;

import lombok.Data;
import java.io.Serializable;
import java.util.List;

/**
 * 游客流量统计VO
 */
@Data
public class VisitorCountVO implements Serializable {
    
    private Long totalVisitors;
    
    private List<MonthlyData> monthlyData;
    
    @Data
    public static class MonthlyData {
        private Integer month;
        private String date;
        private Long visitors;
        private Double avgRating;
    }
}
