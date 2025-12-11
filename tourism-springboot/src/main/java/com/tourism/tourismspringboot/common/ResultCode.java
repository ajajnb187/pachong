package com.tourism.tourismspringboot.common;

/**
 * 响应状态码
 *
 * @author Tourism System
 */
public class ResultCode {

    /**
     * 成功
     */
    public static final Integer SUCCESS = 200;

    /**
     * 失败
     */
    public static final Integer ERROR = 500;

    /**
     * 未授权
     */
    public static final Integer UNAUTHORIZED = 401;

    /**
     * 无权限
     */
    public static final Integer FORBIDDEN = 403;

    /**
     * 参数错误
     */
    public static final Integer BAD_REQUEST = 400;

    /**
     * 资源不存在
     */
    public static final Integer NOT_FOUND = 404;
}
