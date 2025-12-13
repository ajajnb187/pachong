package com.tourism.tourismspringboot.service;

import java.util.Map;

public interface IScenicManageService {
    
    Map<String, Object> getScenicList(Integer page, Integer pageSize, String keyword, String sightLevel);
    
    Map<String, Object> getScenicDetail(String spotName);
    
    Map<String, Object> getReviews(String spotName, Integer page, Integer pageSize);
}
