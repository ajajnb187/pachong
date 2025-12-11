package com.tourism.tourismspringboot.controller;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.CrossOrigin;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import com.tourism.tourismspringboot.common.Result;
import com.tourism.tourismspringboot.dto.LoginDTO;
import com.tourism.tourismspringboot.dto.UpdateUserDTO;
import com.tourism.tourismspringboot.service.IAuthService;
import com.tourism.tourismspringboot.vo.LoginVO;
import com.tourism.tourismspringboot.vo.UserVO;

import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;

/**
 * 认证控制器
 */
@Tag(name = "用户认证接口")
@RestController
@RequestMapping("/api/auth")
@CrossOrigin
public class AuthController {

    @Autowired
    private IAuthService authService;

    @Operation(summary = "用户登录")
    @PostMapping("/login")
    public Result<LoginVO> login(@RequestBody LoginDTO loginDTO) {
        LoginVO loginVO = authService.login(loginDTO);
        return Result.success("登录成功", loginVO);
    }

    @Operation(summary = "获取当前用户信息")
    @GetMapping("/userinfo")
    public Result<UserVO> getUserInfo() {
        UserVO userVO = authService.getUserInfo();
        return Result.success(userVO);
    }

    @Operation(summary = "更新用户信息")
    @PutMapping("/update")
    public Result<UserVO> updateUserInfo(@RequestBody UpdateUserDTO updateUserDTO) {
        UserVO userVO = authService.updateUserInfo(updateUserDTO);
        return Result.success("更新成功", userVO);
    }

    @Operation(summary = "退出登录")
    @PostMapping("/logout")
    public Result<Void> logout() {
        authService.logout();
        return Result.success("退出成功", null);
    }
}
