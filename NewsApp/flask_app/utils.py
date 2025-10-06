import requests
import xml.etree.ElementTree as ET
from bson.objectid import ObjectId
from pymongo import MongoClient
from datetime import datetime
import openai
from urllib.parse import urlparse

# Kết nối MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["news_raw"]
dantri_collection = db["dantri"]

# API thời tiết
WEATHER_API_KEY = "58497cb5c6ba57ef2baef40c20d72b7b"
lat = 21
lon = 105
part = "minutely"
WEATHER_URL = f"https://api.openweathermap.org/data/3.0/onecall?lat={lat}&lon={lon}&exclude={part}&appid={WEATHER_API_KEY}"
VCB_EXCHANGE_RATE_URL = "https://portal.vietcombank.com.vn/Usercontrols/TVPortal.TyGia/pXML.aspx"

def get_weather():
    """Lấy dữ liệu thời tiết từ API OpenWeatherMap."""
    try:
        response = requests.get(WEATHER_URL)
        weather_data = response.json()

        temp_celsius = round(weather_data["current"]["temp"] - 273.15, 2)
        feels_like_celsius = round(weather_data["current"]["feels_like"] - 273.15, 2)

        return {
            "temp": temp_celsius,
            "feels_like": feels_like_celsius,
            "description": weather_data["current"]["weather"][0]["description"].capitalize(),
            "icon": f"http://openweathermap.org/img/wn/{weather_data['current']['weather'][0]['icon']}@2x.png"
        }
    except Exception as e:
        print(f"❌ Lỗi khi lấy dữ liệu thời tiết: {e}")
        return {
            "temp": "N/A",
            "feels_like": "N/A",
            "description": "Không có dữ liệu",
            "icon": ""
        }

def get_exchange_rates():
    """Lấy dữ liệu tỷ giá USD từ Vietcombank."""
    try:
        response = requests.get(VCB_EXCHANGE_RATE_URL)
        response.encoding = 'utf-8'
        xml_data = response.text

        root = ET.fromstring(xml_data)

        def parse_rate(value):
            if value in [None, '-', '']:
                return 0.0
            return float(value.replace(",", ""))

        rates = []
        for currency in root.findall("Exrate"):
            if currency.get("CurrencyCode") == "USD":
                buy = parse_rate(currency.get("Buy"))
                transfer = parse_rate(currency.get("Transfer"))
                sell = parse_rate(currency.get("Sell"))

                rates.append({
                    "code": "USD",
                    "buy": buy,
                    "transfer": transfer,
                    "sell": sell
                })

        return rates if rates else None
    except Exception as e:
        print(f"❌ Lỗi khi lấy dữ liệu tỷ giá: {e}")
        return None

def get_time_info():
    """Lấy thời gian hiện tại."""
    return datetime.now().strftime("%H:%M:%S - %d/%m/%Y")

def get_article_id_from_url(url):
    """Lấy ID bài báo từ URL."""
    try:
        path = urlparse(url).path
        article_id = path.split("/")[-1]
        ObjectId(article_id)
        return ObjectId(article_id)
    except Exception as e:
        print(f"❌ Lỗi khi lấy ID từ URL: {str(e)}")
        return None

def get_article_summary(article_id):
    """Tóm tắt nội dung bài báo."""
    article = dantri_collection.find_one({"_id": ObjectId(article_id)})
    if article:
        article_text = article.get("content", "")
        if article_text:
            return summarize_article_with_gpt(article_text)
    return "❌ Không tìm thấy bài viết để tóm tắt."

def summarize_article_with_gpt(article_text):
    """Sử dụng GPT-4 để tóm tắt bài báo."""
    prompt = f"Tóm tắt bài báo sau:\n\n{article_text}\n\nTóm tắt ngắn gọn:"
    try:
        response = openai.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"❌ Lỗi khi tóm tắt bài viết: {str(e)}"

def search_articles(query):
    # Giả lập tìm kiếm bài viết, bạn có thể thay bằng truy vấn DB
    all_articles = [
        {"title": "Bản tin sáng", "url": "/article1"},
        {"title": "Thời tiết hôm nay", "url": "/article2"},
        {"title": "Chứng khoán tăng mạnh", "url": "/article3"}
    ]
    return [article for article in all_articles if query.lower() in article["title"].lower()]