from pathlib import Path
from cryptography.fernet import Fernet
import base64


class Crypto:
    def __init__(self, key: str):
        try:
            key = key.strip()
            
            padding = len(key) % 4
            if padding:
                key += "=" * (4 - padding)
            
            key_bytes = base64.urlsafe_b64decode(key)
            if len(key_bytes) != 32:
                raise ValueError(f"Некорректная длина ключа: {len(key_bytes)} байт (требуется 32)")
                
            self.cipher = Fernet(base64.urlsafe_b64encode(key_bytes))
        except Exception as e:
            raise ValueError(f"Ошибка инициализации шифрования. Проверьте ENCRYPTION_KEY: {str(e)}")
        
    def encrypt_file(self, file_path: Path) -> bytes:
        """Шифрование файла"""
        if not file_path.exists():
            raise FileNotFoundError(f"File {file_path} not found")
        return self.cipher.encrypt(file_path.read_bytes())

    def decrypt_file(self, encrypted_data: bytes) -> str:
        """Дешифрование данных"""
        return self.cipher.decrypt(encrypted_data).decode('utf-8')
    