import json
import pandas as pd

from sklearn.pipeline import FeatureUnion, Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.base import BaseEstimator, TransformerMixin

# 1. Đọc file JSON
json_file_path = "filtered_news.json"  # Đường dẫn tới file
df = pd.read_json(json_file_path, encoding='utf-8')

# 2. Định nghĩa ColumnSelector
class ColumnSelector(BaseEstimator, TransformerMixin):
    def __init__(self, column):
        self.column = column
    def fit(self, X, y=None):
        return self
    def transform(self, X):
        return X[self.column].values.astype('U')  # 'U' = Unicode string

# 3. Tạo Pipeline cho mỗi cột
title_pipe = Pipeline([
    ('select_title', ColumnSelector('title')),
    ('tfidf_title', TfidfVectorizer())
])

content_pipe = Pipeline([
    ('select_content', ColumnSelector('content')),
    ('tfidf_content', TfidfVectorizer())
])

author_pipe = Pipeline([
    ('select_author', ColumnSelector('author')),
    ('tfidf_author', TfidfVectorizer())
])

category_pipe = Pipeline([
    ('select_category', ColumnSelector('category')),
    ('tfidf_category', TfidfVectorizer())
])

# 4. Hợp nhất với FeatureUnion + trọng số
feature_union = FeatureUnion(
    transformer_list=[
        ('title_pipe', title_pipe),
        ('content_pipe', content_pipe),
        ('author_pipe', author_pipe),
        ('category_pipe', category_pipe),
    ],
    transformer_weights={
        'title_pipe': 3.0,
        'content_pipe': 1.0,
        'author_pipe': 5.0,
        'category_pipe': 3.0
    }
)

# 5. Fit_transform -> ma trận TF-IDF
X = feature_union.fit_transform(df)
print("Kích thước vector TF-IDF kết hợp:", X.shape)

# 6. Tính độ tương đồng
similarity_matrix = cosine_similarity(X, X)

# 7. Ví dụ gợi ý
i = 0
sim_scores = similarity_matrix[i]
sorted_indices = sim_scores.argsort()[::-1]

print(f"Bài {i}:", df['title'][i])
for idx in sorted_indices[1:]:
    print(f" - Gần với bài {idx} = {df['title'][idx]} (similarity={sim_scores[idx]:.3f})")
