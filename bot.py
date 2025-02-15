import os
import asyncio
import logging
import requests
from bs4 import BeautifulSoup
from aiogram import Bot, Dispatcher
from aiogram.types import Message

# Загружаем переменные окружения
TOKEN = os.environ["TOKEN"]
CHANNEL_ID = os.environ["CHANNEL_ID"]
SBERGPT_URL = os.environ["SBERGPT_URL"]

# Сайты для парсинга
TECH_NEWS_SITES = {
    "games": "https://www.ixbt.com/games/news/",
    "processors": "https://www.ixbt.com/news/hard/index.shtml",
    "gpus": "https://www.ixbt.com/news/video/index.shtml",
    "xiaomi": "https://www.ixbt.com/news/company/xiaomi/"
}

# Ключевые слова
KEYWORDS = ["релиз", "анонс", "Xiaomi", "процессор", "видеокарта", "игра", "AMD", "Intel", "NVIDIA", "Snapdragon"]

# Настройка логирования
logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
dp = Dispatcher()

# Функция парсинга новостей
def get_filtered_news():
    news_list = []
    headers = {"User-Agent": "Mozilla/5.0"}

    for category, url in TECH_NEWS_SITES.items():
        try:
            response = requests.get(url, headers=headers)
            soup = BeautifulSoup(response.text, "html.parser")

            articles = soup.find_all("a", class_="caption")[:10]
            for article in articles:
                title = article.text.strip()
                link = article["href"]

                if any(word.lower() in title.lower() for word in KEYWORDS):
                    news_list.append({"title": title, "link": link})

        except Exception as e:
            logging.error(f"Ошибка парсинга {url}: {e}")

    return news_list[:2]

# Функция анализа текста через SberGPT
def analyze_news_sber(text):
    headers = {"Content-Type": "application/json"}
    data = {"prompt": f"Выдели главное в новости: {text}", "max_tokens": 80, "temperature": 0.7}

    response = requests.post(SBERGPT_URL, json=data, headers=headers)
    if response.status_code == 200:
        return response.json().get("result", "Ошибка обработки")
    return "Ошибка подключения к SberGPT"

# Отправка новостей в Telegram
async def send_news():
    news = get_filtered_news()
    for article in news:
        summary = analyze_news_sber(article["title"])
        message = f"📢 {article['title']}\n\n📰 {summary}\n🔗 {article['link']}"
        await bot.send_message(CHANNEL_ID, message)
    await bot.session.close()

# Запуск бота в цикле (2 новости в час)
async def main():
    while True:
        await send_news()
        await asyncio.sleep(1800)

if name == "main":
    asyncio.run(main())