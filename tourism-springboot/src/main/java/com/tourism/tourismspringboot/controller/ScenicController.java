package com.tourism.tourismspringboot.controller;

import java.util.List;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.CrossOrigin;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import com.tourism.tourismspringboot.common.Result;
import com.tourism.tourismspringboot.service.IScenicAnalysisService;
import com.tourism.tourismspringboot.vo.ScenicVO;

import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;

/**
 * 景区查询控制器
 */
@Tag(name = "景区查询接口")
@RestController
@RequestMapping("/api/scenic")
@CrossOrigin
public class ScenicController {

    @Autowired
    private IScenicAnalysisService scenicAnalysisService;

    @Operation(summary = "获取景区列表")
    @GetMapping("/list")
    public Result<List<ScenicVO>> getScenicList() {
        List<ScenicVO> list = scenicAnalysisService.getScenicList(1, 100);
        return Result.success(list);
    }
}
