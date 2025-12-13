package com.tourism.tourismspringboot.vo;

import lombok.Data;
import java.io.Serializable;
import java.util.List;

/**
 * 客源地分布VO
 */
@Data
public class VisitorSourceVO implements Serializable {
    
    private Long totalVisitors;
    
    private List<ProvinceItem> provinceDistribution;
    
    private List<CityItem> cityDistribution;
    
    @Data
    public static class ProvinceItem {
        private String province;
        private Long visitorCount;
        private Double percentage;
    }
    
    @Data
    public static class CityItem {
        private String city;
        private Long visitorCount;
        private Double percentage;
    }
}
