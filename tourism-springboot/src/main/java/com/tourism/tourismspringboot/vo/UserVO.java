package com.tourism.tourismspringboot.vo;

import java.io.Serializable;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

/**
 * 用户信息VO
 */
@Data
@Schema(description = "用户信息")
public class UserVO implements Serializable {
    
    @Schema(description = "用户ID")
    private Long id;
    
    @Schema(description = "用户名")
    private String username;
    
    @Schema(description = "昵称")
    private String nickname;
    
    @Schema(description = "邮箱")
    private String email;
    
    @Schema(description = "手机号")
    private String phone;
    
    @Schema(description = "头像")
    private String avatar;
    
    @Schema(description = "角色")
    private String role;
    
    @Schema(description = "创建时间")
    private String createTime;
    
    @Schema(description = "最后登录时间")
    private String lastLoginTime;
}
