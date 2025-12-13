package com.tourism.tourismspringboot.vo;

import lombok.Data;
import java.io.Serializable;

/**
 * 景区数据VO
 */
@Data
public class ScenicVO implements Serializable {
    
    private Integer businessId;
    
    private String scenicSpot;
    
    private String city;
    
    private String zoneName;
    
    private Double commentScore;
    
    private Double heatScore;
    
    private String sightLevel;
    
    private String marketPrice;
    
    private String isFree;
    
    private String coverImageUrl;
    
    private String detailUrl;
    
    private Double latitude;
    
    private Double longitude;
}
