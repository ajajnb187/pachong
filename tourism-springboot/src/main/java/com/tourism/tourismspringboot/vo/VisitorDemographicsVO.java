package com.tourism.tourismspringboot.vo;

import lombok.Data;
import java.io.Serializable;
import java.util.List;
import java.util.Map;

/**
 * 游客画像VO
 */
@Data
public class VisitorDemographicsVO implements Serializable {
    
    private Integer averageAge;
    
    private Map<String, Double> genderDistribution;
    
    private List<AgeItem> ageDistribution;
    
    @Data
    public static class AgeItem {
        private String ageGroup;
        private Double percentage;
    }
}
