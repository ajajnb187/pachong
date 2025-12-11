package com.tourism.tourismspringboot.vo;

import lombok.Data;
import java.io.Serializable;

/**
 * 景区数据VO
 */
@Data
public class ScenicVO implements Serializable {
    
    private String spotId;
    
    private String spotName;
    
    private Long totalReviews;
    
    private Double avgRating;
    
    private Long totalVisitors;
}
