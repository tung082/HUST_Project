import numpy as np
import pandas as pd
from pymongo import MongoClient
from sklearn.pipeline import Pipeline
from sklearn.base import BaseEstimator, TransformerMixin
from sentence_transformers import SentenceTransformer
from bson.objectid import ObjectId

# 🔹 Kết nối MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client.news_raw
collection = db.dantri
articles = list(collection.find())

if not articles:
    print("❌ Không tìm thấy dữ liệu trong MongoDB!")
    exit()

df = pd.DataFrame(articles)

# 🔹 Chuyển ObjectId thành string
df["_id"] = df["_id"].astype(str)

# 🔹 Xử lý giá trị None (nếu có)
df["title"] = df["title"].fillna("")
df["content"] = df["content"].fillna("")
df["author"] = df["author"].fillna("")

# 🔹 Định nghĩa token đặc biệt
TITLE_TOKEN = "<|title|>"
TITLE_END_TOKEN = "<|/title|>"
CONTENT_TOKEN = "<|content|>"
CONTENT_END_TOKEN = "<|/content|>"
AUTHOR_TOKEN = "<|author|>"
AUTHOR_END_TOKEN = "<|/author|>"

# 🔹 Kết hợp các trường dữ liệu với token đặc biệt
df["combined_text"] = (
    TITLE_TOKEN + df["title"] + TITLE_END_TOKEN + " " +
    CONTENT_TOKEN + df["content"] + CONTENT_END_TOKEN + " " +
    AUTHOR_TOKEN + df["author"] + AUTHOR_END_TOKEN
)

# 🔹 Load mô hình BERT (SBERT)
bert_model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

# 🔹 Transformer để chuyển văn bản thành vector bằng BERT
class BERTEmbedding(BaseEstimator, TransformerMixin):
    def fit(self, X, y=None):
        return self

    def transform(self, X):
        return np.array([bert_model.encode(text) for text in X])  # Chuyển thành vector

# 🔹 Pipeline xử lý dữ liệu kết hợp với token đặc biệt
bert_pipeline = Pipeline([
    ('bert_embedding', BERTEmbedding())
])

# 🔹 Tạo vector BERT từ dữ liệu đã chuẩn hóa
X = bert_pipeline.fit_transform(df["combined_text"])
print("✅ Đã tính xong BERT Embeddings")

# 🔹 Lưu vector BERT vào MongoDB
vector_collection = db.news_vector
vector_collection.delete_many({})  # Xóa dữ liệu cũ nếu có

# 🔹 Chuyển dữ liệu sang dictionary
bert_dict = {df["_id"][i]: X[i].tolist() for i in range(len(df))}

vector_data = []
for _id, vec in bert_dict.items():
    try:
        object_id = ObjectId(_id)
        vector_data.append({"_id": object_id, "vector_bert": vec})
    except Exception as e:
        print(f"❌ Lỗi khi chuyển ObjectId {_id}: {e}")

if vector_data:
    vector_collection.insert_many(vector_data)
    print("✅ BERT vectors đã được lưu vào MongoDB!")
else:
    print("❌ Không có dữ liệu hợp lệ để lưu!")
