"""
AES 加密解密服务
用于隐私空间文档内容的加密存储
"""
import os
import base64
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


def derive_key(password: str, salt: bytes) -> bytes:
    """
    从用户密码派生加密密钥
    使用 PBKDF2 算法，100000 次迭代
    """
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,  # AES-256 需要 32 字节密钥
        salt=salt,
        iterations=100000,
        backend=default_backend()
    )
    return kdf.derive(password.encode('utf-8'))


def encrypt_content(content: str, password: str) -> str:
    """
    使用 AES-256-GCM 加密内容
    返回格式: base64(salt + nonce + tag + ciphertext)
    """
    if not content:
        return content
    
    # 生成随机盐值和 nonce
    salt = os.urandom(16)
    nonce = os.urandom(12)  # GCM 模式推荐 12 字节
    
    # 从密码派生密钥
    key = derive_key(password, salt)
    
    # 创建加密器
    cipher = Cipher(
        algorithms.AES(key),
        modes.GCM(nonce),
        backend=default_backend()
    )
    encryptor = cipher.encryptor()
    
    # 加密内容
    ciphertext = encryptor.update(content.encode('utf-8')) + encryptor.finalize()
    
    # 获取认证标签
    tag = encryptor.tag
    
    # 组合: salt(16) + nonce(12) + tag(16) + ciphertext
    encrypted_data = salt + nonce + tag + ciphertext
    
    # Base64 编码以便存储
    return base64.b64encode(encrypted_data).decode('utf-8')


def decrypt_content(encrypted_content: str, password: str) -> str:
    """
    解密 AES-256-GCM 加密的内容
    """
    if not encrypted_content:
        return encrypted_content
    
    try:
        # Base64 解码
        encrypted_data = base64.b64decode(encrypted_content.encode('utf-8'))
        
        # 分离各部分
        salt = encrypted_data[:16]
        nonce = encrypted_data[16:28]
        tag = encrypted_data[28:44]
        ciphertext = encrypted_data[44:]
        
        # 从密码派生密钥
        key = derive_key(password, salt)
        
        # 创建解密器
        cipher = Cipher(
            algorithms.AES(key),
            modes.GCM(nonce, tag),
            backend=default_backend()
        )
        decryptor = cipher.decryptor()
        
        # 解密内容
        plaintext = decryptor.update(ciphertext) + decryptor.finalize()
        
        return plaintext.decode('utf-8')
    except Exception as e:
        # 解密失败（密码错误或数据损坏）
        raise ValueError(f"解密失败: {str(e)}")


def encrypt_title(title: str, password: str) -> str:
    """
    加密文档标题（简化版，仅用于搜索场景）
    """
    return encrypt_content(title, password)


def decrypt_title(encrypted_title: str, password: str) -> str:
    """
    解密文档标题
    """
    return decrypt_content(encrypted_title, password)
