"""
隐私空间服务
管理隐私空间的访问令牌、密码验证等
"""
import secrets
from datetime import datetime, timedelta
from flask import current_app
from ..extensions import redis_client


class PrivacySpaceService:
    """隐私空间服务类"""
    
    TOKEN_PREFIX = "privacy_token:"
    TOKEN_EXPIRY = 180  # 3 分钟（秒）
    
    @staticmethod
    def generate_access_token(user_id: int) -> str:
        """
        生成隐私空间访问令牌
        有效期 3 分钟
        """
        token = secrets.token_urlsafe(32)
        key = f"{PrivacySpaceService.TOKEN_PREFIX}{user_id}"
        
        try:
            redis_client.setex(
                key,
                PrivacySpaceService.TOKEN_EXPIRY,
                token
            )
            return token
        except Exception as e:
            current_app.logger.error(f"生成隐私空间令牌失败: {e}")
            return None
    
    @staticmethod
    def verify_access_token(user_id: int, token: str) -> bool:
        """
        验证隐私空间访问令牌是否有效
        """
        if not token:
            return False
        
        key = f"{PrivacySpaceService.TOKEN_PREFIX}{user_id}"
        
        try:
            stored_token = redis_client.get(key)
            if stored_token:
                return stored_token.decode('utf-8') == token
            return False
        except Exception as e:
            current_app.logger.error(f"验证隐私空间令牌失败: {e}")
            return False
    
    @staticmethod
    def refresh_access_token(user_id: int, token: str) -> bool:
        """
        刷新隐私空间访问令牌的过期时间
        每次访问隐私空间 API 时调用
        """
        if not PrivacySpaceService.verify_access_token(user_id, token):
            return False
        
        key = f"{PrivacySpaceService.TOKEN_PREFIX}{user_id}"
        
        try:
            # 重新设置过期时间
            redis_client.expire(key, PrivacySpaceService.TOKEN_EXPIRY)
            return True
        except Exception as e:
            current_app.logger.error(f"刷新隐私空间令牌失败: {e}")
            return False
    
    @staticmethod
    def revoke_access_token(user_id: int) -> bool:
        """
        撤销隐私空间访问令牌
        用户主动退出隐私空间或修改密码时调用
        """
        key = f"{PrivacySpaceService.TOKEN_PREFIX}{user_id}"
        
        try:
            redis_client.delete(key)
            return True
        except Exception as e:
            current_app.logger.error(f"撤销隐私空间令牌失败: {e}")
            return False
