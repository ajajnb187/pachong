package com.tourism.tourismspringboot.service.impl;

import cn.dev33.satoken.stp.StpUtil;
import cn.hutool.crypto.digest.BCrypt;
import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.tourism.tourismspringboot.dto.LoginDTO;
import com.tourism.tourismspringboot.dto.UpdateUserDTO;
import com.tourism.tourismspringboot.entity.User;
import com.tourism.tourismspringboot.mapper.UserMapper;
import com.tourism.tourismspringboot.service.IAuthService;
import com.tourism.tourismspringboot.vo.LoginVO;
import com.tourism.tourismspringboot.vo.UserVO;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.BeanUtils;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;

/**
 * 认证服务实现
 */
@Slf4j
@Service
public class AuthServiceImpl implements IAuthService {

    @Autowired
    private UserMapper userMapper;

    @Override
    public LoginVO login(LoginDTO loginDTO) {
        log.info("用户登录: {}", loginDTO.getUsername());

        // 查询用户
        LambdaQueryWrapper<User> queryWrapper = new LambdaQueryWrapper<>();
        queryWrapper.eq(User::getUsername, loginDTO.getUsername());
        User user = userMapper.selectOne(queryWrapper);

        if (user == null) {
            throw new IllegalArgumentException("用户名或密码错误");
        }

        // 验证密码
        if (!BCrypt.checkpw(loginDTO.getPassword(), user.getPassword())) {
            throw new IllegalArgumentException("用户名或密码错误");
        }

        // 检查用户状态
        if (user.getStatus() == 0) {
            throw new IllegalArgumentException("账号已被禁用");
        }

        // 使用SaToken登录
        StpUtil.login(user.getId());
        
        // 更新最后登录时间
        user.setLastLoginTime(LocalDateTime.now());
        userMapper.updateById(user);

        // 构造返回对象
        LoginVO loginVO = new LoginVO();
        loginVO.setToken(StpUtil.getTokenValue());

        UserVO userVO = new UserVO();
        BeanUtils.copyProperties(user, userVO);
        if (user.getCreateTime() != null) {
            userVO.setCreateTime(user.getCreateTime().format(DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss")));
        }
        if (user.getLastLoginTime() != null) {
            userVO.setLastLoginTime(user.getLastLoginTime().format(DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss")));
        }
        loginVO.setUserInfo(userVO);

        log.info("用户登录成功: {}, token: {}", user.getUsername(), loginVO.getToken());
        return loginVO;
    }

    @Override
    public UserVO getUserInfo() {
        // 获取当前登录用户ID
        long userId = StpUtil.getLoginIdAsLong();
        
        User user = userMapper.selectById(userId);
        if (user == null) {
            throw new IllegalArgumentException("用户不存在");
        }

        UserVO userVO = new UserVO();
        BeanUtils.copyProperties(user, userVO);
        if (user.getCreateTime() != null) {
            userVO.setCreateTime(user.getCreateTime().format(DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss")));
        }
        if (user.getLastLoginTime() != null) {
            userVO.setLastLoginTime(user.getLastLoginTime().format(DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss")));
        }
        
        return userVO;
    }

    @Override
    public UserVO updateUserInfo(UpdateUserDTO updateUserDTO) {
        // 获取当前登录用户ID
        long userId = StpUtil.getLoginIdAsLong();
        
        User user = userMapper.selectById(userId);
        if (user == null) {
            throw new IllegalArgumentException("用户不存在");
        }

        // 更新用户信息
        if (updateUserDTO.getNickname() != null) {
            user.setNickname(updateUserDTO.getNickname());
        }
        if (updateUserDTO.getEmail() != null) {
            user.setEmail(updateUserDTO.getEmail());
        }
        if (updateUserDTO.getPhone() != null) {
            user.setPhone(updateUserDTO.getPhone());
        }
        if (updateUserDTO.getAvatar() != null) {
            user.setAvatar(updateUserDTO.getAvatar());
        }

        userMapper.updateById(user);
        log.info("用户信息更新成功: userId={}", userId);

        // 返回更新后的用户信息
        return getUserInfo();
    }

    @Override
    public void logout() {
        StpUtil.logout();
        log.info("用户退出登录");
    }
}
