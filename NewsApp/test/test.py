from pymongo import MongoClient
from bs4 import BeautifulSoup
import json

# Kết nối với MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["news_raw"]
collection = db["dantri"]

# Từ điển ánh xạ category không dấu sang có dấu
category_mapping = {
    "kinh doanh": "Kinh Doanh",
    "xa hoi": "Xã Hội",
    "the gioi": "Thế Giới",
    "giai tri": "Giải Trí",
    "bat dong san": "Bất Động Sản",
    "the thao": "Thể Thao",
    "viec lam": "Việc Làm",
    "nhan ai": "Nhân Ái",
    "suc khoe": "Sức Khỏe",
    "xe": "Xe",
    "suc manh so": "Sức Mạnh Số",
    "giao duc": "Giáo Dục",
    "an sinh": "An Sinh",
    "phap luat": "Pháp Luật"
}

def clean_html(html_content):
    """Hàm loại bỏ HTML, giữ lại nội dung thuần văn bản"""
    if not html_content:
        return ""
    soup = BeautifulSoup(html_content, "html.parser")
    return soup.get_text(separator="\n").strip()  # Xuống dòng giữa các đoạn văn bản

def convert_category(category):
    """Hàm chuyển category không dấu sang có dấu"""
    category_lower = category.lower().strip()
    return category_mapping.get(category_lower, category)  # Trả về category có dấu hoặc giữ nguyên nếu không có trong danh sách

# Danh sách để lưu dữ liệu đã lọc
filtered_data = []

# Lặp qua các tài liệu trong MongoDB
for doc in collection.find({}, {"title": 1, "div_content": 1, "author": 1, "category": 1}):
    cleaned_content = clean_html(doc.get("div_content", ""))  # Loại bỏ HTML

    # Chuyển category thành tiếng Việt có dấu từ từ điển
    category_no_diacritics = doc.get("category", "Unknown")
    category_with_diacritics = convert_category(category_no_diacritics)

    # Tạo dictionary với cấu trúc mong muốn
    filtered_doc = {
        "title": doc.get("title", "No Title"),
        "content": cleaned_content,
        "author": doc.get("author", "Unknown"),
        "category": category_with_diacritics 
    }

    # Thêm vào danh sách kết quả
    filtered_data.append(filtered_doc)

# Xuất dữ liệu ra file JSON
output_file = "filtered_news.json"
with open(output_file, "w", encoding="utf-8") as f:
    json.dump(filtered_data, f, indent=4, ensure_ascii=False)

print(f"✅ Dữ liệu đã được xuất ra file {output_file}")
