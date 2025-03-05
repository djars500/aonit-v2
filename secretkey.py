from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from base64 import b64encode, b64decode
import hashlib
from datetime import datetime


def verify_activation_key(encrypted_data: str):
    try:
        secret_key = b64decode("hEZXeXhva2mHWc1AoPDL1e4cGry7odlCYq1WjpQTPFE=")
        encrypted_bytes = b64decode(encrypted_data)
        nonce = encrypted_bytes[:16]
        tag = encrypted_bytes[16:32]
        ciphertext = encrypted_bytes[32:]
        cipher = AES.new(secret_key, AES.MODE_EAX, nonce=nonce)
        data = cipher.decrypt_and_verify(ciphertext, tag).decode()

        # Проверка даты активации
        current_date = datetime.now()
        activation_date = datetime.strptime(data, "%Y%m%d")

        if activation_date >= current_date:
            return True, f'"Ключ действителен. Срок активации:", {activation_date.strftime("%Y-%m-%d")}'
        else:
            return False, f'Ключ истёк. Срок активации был:" {activation_date.strftime("%Y-%m-%d")}'
    except Exception as e:
        print(f"Ошибка расшифровки или проверки ключа: {e}")