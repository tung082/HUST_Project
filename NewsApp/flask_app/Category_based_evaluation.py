import numpy as np
import random
from typing import List
from pymongo import MongoClient
from bson.objectid import ObjectId

# Giả sử package gốc là 'Recommender'
from Recommender.tfidf_recommender import TFIDFRecommender
from Recommender.bert_recommender import BERTRecommender

def evaluate_by_category(
    recommender, 
    db, 
    category_field: str = "category", 
    top_k: int = 5, 
    n_samples: int = 20
) -> float:
    """
    Giả lập đánh giá dựa vào category (thể loại) 
    - Lấy ngẫu nhiên n_samples bài báo 
    - Mỗi bài, lấy category làm ground-truth 
    - Gọi get_recommendations() => so sánh tỉ lệ cùng category trong top_k
    - Trả về giá trị trung bình tỉ lệ bài cùng thể loại (avg_precision).
    """
    dantri_coll = db.dantri
    # Tắt time ranking khi test
    recommender.set_time_ranking(False)

    # Lấy tất cả bài báo có category
    articles_with_cat = list(dantri_coll.find(
        {category_field: {"$exists": True, "$ne": None}},
        {"_id": 1, category_field: 1}
    ))
    if not articles_with_cat:
        print("❌ Không có bài báo có trường category. Không thể đánh giá.")
        return 0.0
    # Chọn ngẫu nhiên n_samples bài
    random.shuffle(articles_with_cat)
    articles_sampled = articles_with_cat[:n_samples]
    
    sum_precision = 0.0
    
    for doc in articles_sampled:
        article_id = str(doc["_id"])
        true_cat = doc[category_field]
        
        # Gọi recommender
        top_recs = recommender.get_recommendations(article_id, top_k=top_k)
        
        # Đếm bao nhiêu bài chung category
        same_cat_count = 0
        for rec in top_recs:
            rec_article = dantri_coll.find_one(
                {"_id": ObjectId(rec["id"])}, 
                {category_field: 1}
            )
            if rec_article and rec_article.get(category_field) == true_cat:
                same_cat_count += 1
        
        precision_cat = same_cat_count / top_k
        sum_precision += precision_cat
    
    avg_precision = sum_precision / n_samples
    return avg_precision

if __name__ == "__main__":
    client = MongoClient("mongodb://localhost:27017/")
    db = client["news_raw"]

    # Tạo model (TF-IDF, BERT)
    tfidf_model = TFIDFRecommender("mongodb://localhost:27017/", "news_raw")
    bert_model = BERTRecommender("mongodb://localhost:27017/", "news_raw")

    # Danh sách n_samples: từ 10 rồi gấp đôi cho đến 10000
    # Bạn có thể thêm bớt tùy ý (VD: [10, 20, 40, 80, 160, 320, 640, 1280, 2560, 5120, 10000])
    n_samples_values = [20, 40, 80]

    # top_k_values: [5, 10, 20, 50, 100]
    top_k_values = [5, 10, 20, 50]

    print("========== ĐÁNH GIÁ THEO THỂ LOẠI ===========")
    print("Thử với TF-IDF...\n")

    for ns in n_samples_values:
        # In ra cho rõ
        print(f"---> n_samples = {ns}")
        # Duyệt qua các giá trị top_k
        if ns not in top_k_values:
            for tk in top_k_values + [ns]:  # Thêm trường hợp top_k = n_samples
                # Chỉ test khi tk <= ns (top_k không vượt quá n_samples)
                if tk <= ns:
                    precision_result = evaluate_by_category(tfidf_model, db, top_k=tk, n_samples=ns)
                    print(f"[TF-IDF] top_k={tk}, n_samples={ns} => Precision={precision_result:.4f}")
        else:
            for tk in top_k_values:  # Thêm trường hợp top_k = n_samples
                # Chỉ test khi tk <= ns (top_k không vượt quá n_samples)
                if tk <= ns:
                    precision_result = evaluate_by_category(tfidf_model, db, top_k=tk, n_samples=ns)
                    print(f"[TF-IDF] top_k={tk}, n_samples={ns} => Precision={precision_result:.4f}")

    print("\n============ BERT =================")
    for ns in n_samples_values:
        print(f"---> n_samples = {ns}")
        for tk in top_k_values + [ns]:
            if tk <= ns:
                precision_result = evaluate_by_category(bert_model, db, top_k=tk, n_samples=ns)
                print(f"[BERT ] top_k={tk}, n_samples={ns} => Precision={precision_result:.4f}")
        print()
