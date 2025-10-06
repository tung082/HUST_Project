import numpy as np
import pandas as pd
from pymongo import MongoClient
from sklearn.pipeline import FeatureUnion, Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import TruncatedSVD
from sklearn.base import BaseEstimator, TransformerMixin
from bson.objectid import ObjectId

client = MongoClient("mongodb://localhost:27017/")
db = client.news_raw
collection = db.dantri
articles = list(collection.find({}, {"_id": 1, "title": 1, "content": 1, "author": 1}))  # Chỉ lấy cột cần thiết

if not articles:
    print("❌ Không tìm thấy dữ liệu trong MongoDB!")
    exit()

df = pd.DataFrame(articles)

# 🔹 Chuyển ObjectId thành string
df["_id"] = df["_id"].astype(str)

# 🔹 Xử lý giá trị None (nếu có)
df["title"] = df["title"].fillna("")
df["content"] = df["content"].fillna("")

# 🔹 ColumnSelector để chọn cột
class ColumnSelector(BaseEstimator, TransformerMixin):
    def __init__(self, column):
        self.column = column

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        return X[self.column].values.astype('U')

# 🔹 Tạo pipeline TF-IDF
title_pipe = Pipeline([
    ('select_title', ColumnSelector('title')),
    ('tfidf_title', TfidfVectorizer())
])

content_pipe = Pipeline([
    ('select_content', ColumnSelector('content')),
    ('tfidf_content', TfidfVectorizer())
])

# 🔹 Hợp nhất các feature
feature_union = FeatureUnion(
    transformer_list=[
        ('title_pipe', title_pipe),
        ('content_pipe', content_pipe),
    ],
    transformer_weights={
        'title_pipe': 3.0,  # Title có trọng số cao hơn
        'content_pipe': 1.0,
    }
)

# 🔹 Tạo ma trận TF-IDF (giữ dạng sparse)
X_sparse = feature_union.fit_transform(df)
print("✅ Đã tính xong TF-IDF")

# 🔹 Giảm số chiều bằng TruncatedSVD
pca_dim = 384
svd = TruncatedSVD(n_components=pca_dim)
X_reduced = svd.fit_transform(X_sparse)

print(f"✅ Đã giảm số chiều xuống còn {X_reduced.shape[1]}")

# 🔹 Lưu vào MongoDB với cập nhật nếu tồn tại
vector_collection = db.news_vector

for i, (_id, vec) in enumerate(zip(df["_id"], X_reduced)):
    try:
        object_id = ObjectId(_id)
        vector_collection.update_one(
            {"_id": object_id},  # Điều kiện tìm kiếm
            {"$set": {"vector_tfidf": vec.tolist()}},  # Nếu có thì cập nhật
            upsert=True  # Nếu không có thì chèn mới
        )
    except Exception as e:
        print(f"❌ Lỗi khi cập nhật ObjectId {_id}: {e}")

print("✅ TF-IDF vectors đã được cập nhật hoặc chèn mới vào MongoDB!")
