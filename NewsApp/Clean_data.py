from pymongo import MongoClient
from urllib.parse import urlparse
from bs4 import BeautifulSoup
import re
# Kết nối với MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["news_raw"]
collection = db["dantri"]

def extract_category(url):
    """Hàm lấy category từ URL"""
    if not url:  # Nếu URL không tồn tại, trả về giá trị mặc định
        return "Unknown"
    parsed_url = urlparse(url).path.strip("/")
    category = parsed_url.split("/")[0] if parsed_url else "Unknown"
    return category.replace("-", " ").capitalize()

def clean_content(html_content):
    """Làm sạch nội dung HTML, xử lý ảnh và loại bỏ thẻ không cần thiết"""
    if not html_content:  # Nếu nội dung là None hoặc rỗng
        return ""

    soup = BeautifulSoup(html_content, "html.parser")

    # Xử lý hình ảnh: thay thế src bằng data-src hoặc data-original nếu có
    for img in soup.find_all("img"):
        if img.has_attr("data-src"):
            img["src"] = img["data-src"]
        elif img.has_attr("data-original"):
            img["src"] = img["data-original"]

        # Xóa các thuộc tính không cần thiết
        img.attrs.pop("data-src", None)
        img.attrs.pop("data-original", None)
        img.attrs.pop("data-srcset", None)
    return str(soup)

def clean_html(html_content):
    """Loại bỏ HTML tags và giữ lại nội dung thuần văn bản"""
    if not html_content:
        return ""
    soup = BeautifulSoup(html_content, "html.parser").get_text(separator=" ").strip()
    cleaned_text = re.sub(r'[^a-záàảãạăắằẳẵặâấầẩẫậbcdđeéèẻẽẹêếềểễệfghiíìỉĩịjklmnoóòỏõọôốồổỗộơớờởỡợpqrstuúùủũụưứừửữựvwxyýỳỷỹỵz0-9/]', ' ', soup.lower())
    cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()
    return cleaned_text

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
    "phap luat": "Pháp Luật",
    "nhip song tre": "Nhịp sống trẻ",
    "ban doc": "Bạn đọc",
    "tinh yeu gioi tinh": "Tình yêu giới tính",
    "van hoa": "Văn hoá",
    "tam long nhan ai": "Tấm lòng nhân ái",
    "khoa hoc cong nghe": "Khoa học công nghệ",
    "nhip song tre": "Nhịp sống trẻ",
    "o to xe may": "Ô tô - xe máy",
    "tam diem": "Tâm điểm",
    "tet 2024": "Tết 2024",
    "lao dong viec lam": "Lao động việc lam",
    "doi song": "Đời sống",
    "du lich": "Du lịch"
}

def convert_category(category):
    """Hàm chuyển category không dấu sang có dấu"""
    category_lower = category.lower().strip()
    return category_mapping.get(category_lower, category)

# Duyệt tất cả tài liệu và cập nhật
for doc in collection.find():
    # Kiểm tra xem tài liệu có các trường cần thiết không
    url = doc.get("url", "")  # Trả về "" nếu không có
    author = doc.get("author", "Unknown")
    date_published = doc.get("date_published", "")
    title = doc.get("title", "No title")
    lead = doc.get("lead", "No lead")
    div_content = doc.get("div_content", "")

    # Làm sạch nội dung
    category = extract_category(url)
    cleaned_content = clean_content(div_content)

    # Cập nhật vào MongoDB
    collection.update_one(
        {"_id": doc["_id"]},
        {"$set": {
            "category": convert_category(category),  # Thêm category
            "div_content": cleaned_content,
            "content": clean_html(cleaned_content)# Cập nhật nội dung đã làm sạch
        }}
    )

