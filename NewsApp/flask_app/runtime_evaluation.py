import time
import random
from typing import List
from pymongo import MongoClient
from bson.objectid import ObjectId

# Thay bằng import phù hợp với dự án của bạn
from Recommender.tfidf_recommender import TFIDFRecommender
from Recommender.bert_recommender import BERTRecommender

def measure_runtime(recommender, article_ids: List[str], n_times: int = 50, top_k: int = 5):
    """
    Đánh giá thời gian trung bình (tính bằng giây) để gọi get_recommendations().
    - recommender: Mô hình gợi ý (TFIDFRecommender hoặc BERTRecommender).
    - article_ids: Danh sách _id (string) của bài báo trong DB.
    - n_times: Số lần gọi get_recommendations() để lấy trung bình.
    - top_k: Số lượng bài gợi ý.
    """

    start_time = time.time()

    # Lặp n_times, mỗi lần chọn ngẫu nhiên một article_id
    for _ in range(n_times):
        test_id = random.choice(article_ids)
        # Gọi hàm get_recommendations
        _ = recommender.get_recommendations(test_id, top_k=top_k)

    total_time = time.time() - start_time
    avg_time = total_time / n_times

    print(f"Model: {recommender.algorithm_name}")
    print(f"  - Gọi {n_times} lần get_recommendations(top_k={top_k})")
    print(f"  - Tổng thời gian: {total_time:.4f} giây")
    print(f"  - Trung bình: {avg_time:.4f} giây/lần\n")

def main():
    # 1) Kết nối DB
    client = MongoClient("mongodb://localhost:27017/")
    db = client["news_raw"]

    # 2) Lấy danh sách _id bài báo
    articles = list(db.dantri.find({}, {"_id": 1}))
    article_ids = [str(a["_id"]) for a in articles]
    if not article_ids:
        print("❌ Không có bài báo nào trong DB!")
        return

    # 3) Tạo instance cho hai mô hình
    tfidf_model = TFIDFRecommender(mongo_uri="mongodb://localhost:27017/", db_name="news_raw")
    bert_model = BERTRecommender(mongo_uri="mongodb://localhost:27017/", db_name="news_raw")

    # 4) Đánh giá thời gian TF-IDF
    measure_runtime(tfidf_model, article_ids, n_times=100, top_k=5)

    # 5) Đánh giá thời gian BERT
    measure_runtime(bert_model, article_ids, n_times=100, top_k=5)

if __name__ == "__main__":
    main()
