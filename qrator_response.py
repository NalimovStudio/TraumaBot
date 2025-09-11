import hashlib
import time

def generate_qrator_token(url: str) -> tuple[str, str]:
    """
    Генерирует Qrator-Token и временную метку для заданного URL.

    """
    timestamp = str(int(time.time()))

    url_without_params = url.split('?')[0]

    # Секретный ключ (salt) из исходного кода
    salt = "5f3672395460c5dae9d91466a06915d9"

    string_to_hash = salt + url_without_params + timestamp

    # Хешируем строку с помощью MD5
    md5_hash = hashlib.md5(string_to_hash.encode('utf-8'))

    # Форматируем результат в шестнадцатеричную строку в нижнем регистре
    qrator_token = md5_hash.hexdigest()

    return qrator_token, timestamp


# Подставьте сюда URL, который вы хотите использовать
target_url = "https://api.lenta.com/v1/auth/session/guest/token"

token, ts = generate_qrator_token(target_url)

print("\n--- Результат ---")
print(f"Timestamp: {ts}")
print(f"Qrator-Token: {token}")