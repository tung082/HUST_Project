from pymongo import MongoClient
from bson.objectid import ObjectId
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import math
from datetime import datetime

class BaseRecommender:
    def __init__(self, mongo_uri="mongodb://localhost:27017/", db_name="news_raw", algorithm_name="tfidf"):
        self.client = MongoClient(mongo_uri)
        self.db = self.client[db_name]
        self.news_vector = self.db.news_vector
        self.dantri = self.db.dantri
        self.user_profiles = self.db.user_profiles
        self.algorithm_name = algorithm_name  # Tên thuật toán hiện tại (tfidf hoặc bert)
        self.vector_field = f"vector_{self.algorithm_name}"  # Tạo trường vector theo thuật toán
        self.vector_dim = 384  # Kích thước vector theo thuật toán
        self.use_time_ranking = True
        
    def generate_random_vector(self, dim=384):
        """Tạo vector ngẫu nhiên cho user profile."""
        return np.random.rand(dim).tolist()

    def get_user_profile(self, user_id):
        """Lấy vector hồ sơ người dùng, nếu chưa có thì tạo mới riêng cho từng thuật toán."""
        user_profile = self.user_profiles.find_one({"_id": user_id})

        if not user_profile or self.vector_field not in user_profile:
            random_vector = self.generate_random_vector(dim=self.vector_dim)
            self.user_profiles.update_one(
                {"_id": user_id},
                {"$set": {self.vector_field: random_vector}},
                upsert=True
            )
            return np.array(random_vector)

        return np.array(user_profile[self.vector_field])

    def get_article_vector_for_test(self, article_id):
        """
        Khi chạy kiểm thử "theo category", ta coi article_id là bài gốc.
        Thay vì user_profiles, hàm này lấy vector từ 'news_vector'.
        """       
        doc = self.news_vector.find_one({"_id": ObjectId(article_id)})
        if doc and self.vector_field in doc:
            return np.array(doc[self.vector_field])
        
        # Nếu bài không có vector => trả về None (hoặc tạo vector ngẫu nhiên)
        return None

    def update_user_profile(self, user_id, article_id):
        """Cập nhật vector hồ sơ người dùng cho thuật toán tương ứng khi họ nhấp vào bài viết."""
        article_vector_data = self.news_vector.find_one({"_id": ObjectId(article_id)})
        if not article_vector_data or self.vector_field not in article_vector_data:
            return

        article_vector = np.array(article_vector_data[self.vector_field])
        user_profile = self.get_user_profile(user_id)

        # Cập nhật hồ sơ người dùng với trọng số
        updated_profile = 0.55 * user_profile + 0.45 * article_vector

        self.user_profiles.update_one(
            {"_id": user_id},
            {"$set": {self.vector_field: updated_profile.tolist()}},
            upsert=True
        )

    def set_time_ranking(self, use_time_ranking):
        """Cài đặt tùy chọn xếp hạng theo thời gian"""
        self.use_time_ranking = use_time_ranking
    
    def calculate_time_scores(self):
        """Tính điểm thời gian dựa trên ngày xuất bản bài viết."""
        now = datetime.now()
        date_publisheds = list(self.dantri.find({}, {"_id": 1, "date_published": 1}))
        time_scores = []

        for doc in date_publisheds:
            past_time = doc.get("date_published", now)
            delta = now - past_time if isinstance(past_time, datetime) else now
            time_score = math.exp(-delta.days * 0.04)  # Giảm trọng số theo thời gian
            time_scores.append(time_score)

        return np.array(time_scores)

    def get_recommendations(self, user_id, top_k=5):
        """Phương thức trừu tượng - sẽ được override bởi class con."""
        raise NotImplementedError("Phương thức này phải được triển khai trong lớp con")
