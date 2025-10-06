from pymongo import MongoClient

# Kết nối đến MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["news_raw"]
collection = db["dantri"]

# Lấy danh sách các giá trị duy nhất
categories = collection.distinct("category")

# In ra kết quả
print(categories)
