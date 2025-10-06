from Recommender.Base_recommender import BaseRecommender
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from bson.objectid import ObjectId
from sentence_transformers import SentenceTransformer


class BERTRecommender(BaseRecommender):
    def __init__(self, mongo_uri="mongodb://localhost:27017/", db_name="news_raw"):
        super().__init__(mongo_uri, db_name, algorithm_name="bert")
        self.vector_dim = 384  # Kích thước vector của BERT MiniLM
        self.vector_field = "vector_bert"  # Trường lưu vector BERT trong MongoDB
        # self.model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

    def get_article_vector(self, article_id, text):
        """Lấy vector bài viết từ MongoDB hoặc tạo mới bằng BERT."""
        article = self.news_vector.find_one({"_id": ObjectId(article_id)})
        if article and self.vector_field in article:
            return np.array(article[self.vector_field])  # Lấy vector đã lưu

        # vector = self.model.encode(text, convert_to_numpy=True)
        # self.news_vector.update_one(
        #     {"_id": ObjectId(article_id)},
        #     {"$set": {self.vector_field: vector.tolist()}},
        #     upsert=True
        # )
        # return vector

    def get_recommendations(self, user_id, top_k=5, test=False):
        """Lấy danh sách bài viết được đề xuất dựa trên BERT."""

        user_profile = self.get_user_profile(user_id).reshape(1, -1)


        # Lấy tất cả vector bài viết từ MongoDB
        all_vectors = list(self.news_vector.find({}, {"_id": 1, self.vector_field: 1}))
        if not all_vectors:
            return []

        # Tách ID và vector
        ids, vectors = [], []
        for item in all_vectors:
            if self.vector_field in item:
                ids.append(str(item["_id"]))
                vectors.append(item[self.vector_field])

        vectors = np.array(vectors)
        original_similarities = cosine_similarity(user_profile, vectors)[0]

        # Áp dụng time_scores nếu use_time_ranking được bật
        if self.use_time_ranking:
            time_scores = self.calculate_time_scores()
            final_similarities = time_scores * original_similarities
        else:
            final_similarities = original_similarities  # Không dùng time_scores

        # Sắp xếp theo điểm cuối
        sorted_indices = np.argsort(final_similarities)[::-1]

        # Tạo danh sách bài viết được đề xuất
        recommended_articles = []
        for i in sorted_indices[:top_k]:
            article = self.dantri.find_one(
                {"_id": ObjectId(ids[i])},
                {"_id": 1, "title": 1, "url": 1, "lead": 1, "date_published": 1}
            )
            if article:
                recommended_articles.append({
                    "id": str(article["_id"]),
                    "title": article["title"],
                    "url": article["url"],
                    "original_score": float(original_similarities[i]),
                    "final_score": float(final_similarities[i]),
                    "lead": article.get("lead", "Không có mô tả."),
                    "date_published": article.get("date_published", "Không có ngày đăng.")
                })

        return recommended_articles

    def search_articles(self, query, top_k=10):
        """Tìm kiếm bài viết dựa trên truy vấn sử dụng BERT."""
        query_vector = self.model.encode(query, convert_to_numpy=True).reshape(1, -1)

        all_vectors = list(self.news_vector.find({}, {"_id": 1, self.vector_field: 1}))
        if not all_vectors:
            return []

        ids, vectors = [], []
        for item in all_vectors:
            if self.vector_field in item:
                ids.append(str(item["_id"]))
                vectors.append(item[self.vector_field])

        vectors = np.array(vectors)
        similarities = cosine_similarity(query_vector, vectors)[0]
        sorted_indices = np.argsort(similarities)[::-1]

        results = []
        for i in sorted_indices[:top_k]:
            article = self.dantri.find_one(
                {"_id": ObjectId(ids[i])},
                {"_id": 1, "title": 1, "url": 1, "lead": 1, "date_published": 1}
            )
            if article:
                results.append({
                    "id": str(article["_id"]),
                    "title": article["title"],
                    "url": article["url"],
                    "score": float(similarities[i]),
                    "lead": article.get("lead", "Không có mô tả."),
                    "date_published": article.get("date_published", "Không có ngày đăng.")
                })

        return results

    def update_user_profile(self, user_id, article_id):
        """Cập nhật hồ sơ người dùng dựa trên bài viết đã xem."""
        article = self.dantri.find_one({"_id": ObjectId(article_id)})
        if article:
            # Giả sử BaseRecommender có phương thức update_user_profile
            super().update_user_profile(user_id, article_id)