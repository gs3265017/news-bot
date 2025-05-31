import base64
from cryptography.fernet import Fernet

class Crypto:
    def __init__(self, key: str):
        # Преобразуем ключ в 32-байтный формат
        self.key = base64.urlsafe_b64encode(key.encode()[:32].ljust(32, b'\0'))
        self.cipher = Fernet(self.key)

    def encrypt_file(self, file_path: str) -> bytes:
        with open(file_path, 'rb') as f:
            data = f.read()
        return self.cipher.encrypt(data)

    def decrypt_file(self, encrypted_data: bytes) -> str:
        return self.cipher.decrypt(encrypted_data).decode()
    