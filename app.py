import os
import requests
import hashlib
import time
from flask import Flask

app = Flask(__name__)

# Конфигурация из переменных окружения
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')
SITE_URL = "https://apextraderfunding.com/coupon-code"
CHECK_INTERVAL = 300  # 5 минут

def send_telegram_message(message):
    """Отправляет сообщение в Telegram"""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    try:
        response = requests.post(url, data=data, timeout=10)
        print(f"✅ Сообщение отправлено: {message}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Ошибка отправки: {e}")
        return False

def get_website_hash():
    """Получает хеш содержимого сайта"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(SITE_URL, headers=headers, timeout=10)
        response.raise_for_status()
        return hashlib.md5(response.text.encode()).hexdigest()
    except Exception as e:
        print(f"❌ Ошибка получения сайта: {e}")
        return None

def monitor_website():
    """Основная функция мониторинга"""
    print("🔍 Проверяем сайт...")
    
    current_hash = get_website_hash()
    if not current_hash:
        return
    
    # Получаем предыдущий хеш из переменной окружения
    last_hash = os.getenv('LAST_HASH')
    
    if last_hash and current_hash != last_hash:
        print("🚨 Обнаружены изменения!")
        message = f"""🚨 <b>ВНИМАНИЕ! Сайт изменился!</b>

📄 Страница: {SITE_URL}
⏰ Время: {time.strftime('%Y-%m-%d %H:%M:%S')}

🔗 <a href="{SITE_URL}">Перейти на сайт</a>"""
        
        if send_telegram_message(message):
            # Обновляем хеш в переменных окружения (через Railway dashboard)
            print("✅ Уведомление отправлено, обновите LAST_HASH в настройках Railway")
    
    elif not last_hash:
        # Первый запуск
        print("⭐ Первый запуск, сохраняем хеш")
        message = f"""🔍 <b>Мониторинг запущен!</b>

📄 Сайт: {SITE_URL}
⏰ Проверка каждые 5 минут
✅ Бот работает на Railway

Текущий хеш: {current_hash[:10]}..."""
        send_telegram_message(message)
    
    else:
        print("✅ Изменений нет")
    
    return current_hash

@app.route('/')
def home():
    return "🤖 Apex Monitor Bot работает!"

@app.route('/check')
def check():
    """Ручная проверка"""
    current_hash = monitor_website()
    return f"Проверка завершена! Хеш: {current_hash}"

@app.route('/health')
def health():
    """Для проверки работоспособности"""
    return "OK"

if __name__ == '__main__':
    # При старте отправляем уведомление
    monitor_website()
    
    # Запускаем Flask
    port = int(os.getenv('PORT', 8000))
    app.run(host='0.0.0.0', port=port)
