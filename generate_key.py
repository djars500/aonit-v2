from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from base64 import b64encode, b64decode
import hashlib

# Генерация секретного ключа (выполняется один раз)
def generate_secret_key():
    return b64decode("hEZXeXhva2mHWc1AoPDL1e4cGry7odlCYq1WjpQTPFE=")

# Шифрование данных
def encrypt_data(secret_key, data):
    cipher = AES.new(secret_key, AES.MODE_EAX)
    ciphertext, tag = cipher.encrypt_and_digest(data.encode())
    return b64encode(cipher.nonce + tag + ciphertext).decode()

# Расшифровка данных
def decrypt_data(secret_key, encrypted_data):
    try:
        encrypted_bytes = b64decode(encrypted_data)
        nonce = encrypted_bytes[:16]
        tag = encrypted_bytes[16:32]
        ciphertext = encrypted_bytes[32:]
        cipher = AES.new(secret_key, AES.MODE_EAX, nonce=nonce)
        data = cipher.decrypt_and_verify(ciphertext, tag)
        return data.decode()
    except Exception as e:
        print(f"Ошибка расшифровки: {e}")
        return None

if __name__ == "__main__":
    # Генерация или использование существующего секретного ключа
    SECRET_KEY = generate_secret_key()

    # Ввод даты окончания действия ключа
    valid_until = input("Введите дату окончания действия ключа (в формате YYYYMMDD): ")

    # Генерация ключа активации
    encrypted_key = encrypt_data(SECRET_KEY, valid_until)
    print(f"Сгенерированный ключ активации: {encrypted_key}")

    # Проверка ключа активации
    decrypted_data = decrypt_data(SECRET_KEY, encrypted_key)
    print(f"Расшифрованные данные: {decrypted_data}")

    # Сравнение введённых и расшифрованных данных
    if decrypted_data == valid_until:
        print("Ключ успешно проверен!")
    else:
        print("Ошибка проверки ключа!")
