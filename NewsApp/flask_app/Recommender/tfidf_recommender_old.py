from pymongo import MongoClient
from bson.objectid import ObjectId
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import math
from datetime import datetime

class TFIDFRecommender:
    def __init__(self, mongo_uri="mongodb://localhost:27017/", db_name="news_raw"):
        self.client = MongoClient(mongo_uri)
        self.db = self.client[db_name]
        self.news_vector = self.db.news_vector
        self.dantri = self.db.dantri
        self.user_profiles = self.db.user_profiles

    def generate_random_vector(self, dim=256):
        """Tạo vector ngẫu nhiên cho user profile."""
        return np.random.rand(dim).tolist()

    def get_user_profile(self, user_id):
        """Lấy vector hồ sơ người dùng, nếu chưa có thì tạo mới."""
        user_profile = self.user_profiles.find_one({"_id": user_id})

        if not user_profile:
            random_vector = self.generate_random_vector()
            self.user_profiles.insert_one({"_id": user_id, "vector": random_vector})
            return np.array(random_vector)

        return np.array(user_profile["vector"])

    def update_user_profile(self, user_id, article_id):
        """Cập nhật vector hồ sơ người dùng khi họ nhấp vào bài viết."""
        article_vector_data = self.news_vector.find_one({"_id": article_id})
        if not article_vector_data:
            return

        article_vector = np.array(article_vector_data['vector_tfidf'])
        user_profile = self.get_user_profile(user_id)

        # Cập nhật hồ sơ người dùng với trọng số
        updated_profile = 0.55 * user_profile + 0.45 * article_vector

        self.user_profiles.update_one(
            {"_id": user_id},
            {"$set": {"vector": updated_profile.tolist()}},
            upsert=True
        )

    def calculate_time_scores(self):
        """Tính điểm thời gian dựa trên ngày xuất bản bài viết."""
        now = datetime.now()
        date_publisheds = list(self.dantri.find({}, {"_id": 1, "date_published": 1}))
        time_scores = []

        for doc in date_publisheds:
            past_time = doc["date_published"] if doc["date_published"] else now
            delta = now - past_time
            time_score = math.exp(-delta.days * 0.5)
            time_scores.append(time_score)

        return np.array(time_scores)

    def get_recommendations(self, user_id, top_k=5, test=False):
        """Lấy danh sách bài viết được đề xuất dựa trên user profile."""
        if test:
            return
        else:
            user_profile = self.get_user_profile(user_id).reshape(1, -1)

        all_vectors = list(self.news_vector.find({}, {"_id": 1, "vector_tfidf": 1}))
        if not all_vectors:
            return []

        ids, vectors = [], []
        for item in all_vectors:
            ids.append(str(item["_id"]))  # Lưu ID dưới dạng string để dễ sử dụng
            vectors.append(item["vector_tfidf"])

        vectors = np.array(vectors)
        time_scores = self.calculate_time_scores()

        # Tính cosine similarity và nhân với điểm thời gian
        similarities = time_scores * cosine_similarity(user_profile, vectors)[0]
        sorted_indices = np.argsort(similarities)[::-1]

        recommended_articles = []
        for i in sorted_indices[:top_k]:
            article = self.dantri.find_one({"_id": ObjectId(ids[i])}, {"_id": 1, "title": 1, "url": 1, "lead": 1, "date_published": 1})
            if article:
                recommended_articles.append({
                    "id": str(article["_id"]),  # Trả về _id dưới dạng string để dùng trong template
                    "title": article["title"],
                    "url": article["url"],
                    "similarity": float(similarities[i]),
                    "lead": article.get("lead", "không có mô tả."),
                    "date_published": article.get("date_published", "Không có ngày đăng.")
                })

        return recommended_articles
