package com.ecom.aics.auth;

/**
 * 已认证用户（userId 来自 token 解析，是唯一可信身份来源）。
 */
public record AuthUser(long userId) {
}
