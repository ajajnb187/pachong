package com.tourism.tourismspringboot.vo;

import lombok.Data;
import java.io.Serializable;
import java.util.List;
import java.util.Map;

/**
 * 评论统计详情VO
 */
@Data
public class ReviewStatsVO implements Serializable {
    
    private String spotName;
    
    private Long totalReviews;
    
    private Double avgRating;
    
    private Long uniqueReviewers;
    
    private Double positiveRate;
    
    private Map<String, Long> ratingDistribution;
    
    private List<ReviewItem> recentReviews;
    
    private List<MonthlyRating> monthlyRating;
    
    @Data
    public static class ReviewItem {
        private String visitorName;
        private Double rating;
        private String reviewContent;
        private String travelDate;
        private String reviewDate;
    }
    
    @Data
    public static class MonthlyRating {
        private Integer month;
        private Double avgRating;
        private Long reviewCount;
    }
}
