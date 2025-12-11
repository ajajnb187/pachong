package com.tourism.tourismspringboot.service;

import com.tourism.tourismspringboot.dto.LoginDTO;
import com.tourism.tourismspringboot.dto.UpdateUserDTO;
import com.tourism.tourismspringboot.vo.LoginVO;
import com.tourism.tourismspringboot.vo.UserVO;

/**
 * 认证服务接口
 */
public interface IAuthService {
    
    /**
     * 用户登录
     */
    LoginVO login(LoginDTO loginDTO);
    
    /**
     * 获取当前用户信息
     */
    UserVO getUserInfo();
    
    /**
     * 更新用户信息
     */
    UserVO updateUserInfo(UpdateUserDTO updateUserDTO);
    
    /**
     * 退出登录
     */
    void logout();
}
