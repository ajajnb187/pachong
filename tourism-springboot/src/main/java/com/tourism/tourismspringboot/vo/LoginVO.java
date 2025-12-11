package com.tourism.tourismspringboot.vo;

import java.io.Serializable;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

/**
 * 登录响应VO
 */
@Data
@Schema(description = "登录响应")
public class LoginVO implements Serializable {
    
    @Schema(description = "JWT Token")
    private String token;
    
    @Schema(description = "用户信息")
    private UserVO userInfo;
}
