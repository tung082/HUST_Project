import random
from typing import List, Dict

def simulate_user_preferences():
    """
    Tạo danh sách user ảo, mỗi user có list 'preferred_tags'.
    """
    return [
        {"user_id": "sim1", "preferred_tags": ["Thể thao"]},
        {"user_id": "sim2", "preferred_tags": ["Công nghệ", "Khoa học"]},
        {"user_id": "sim3", "preferred_tags": ["Chính trị"]},
        # Thêm tuỳ ý
    ]

def evaluate_simulation(recommender, db, users_sim, top_k=5):
    dantri_coll = db.dantri
    sum_precision = 0.0
    n_users = len(users_sim)
    
    for sim_user in users_sim:
        user_id = sim_user["user_id"]
        preferred_tags = sim_user["preferred_tags"]  # list
        
        # Giả định get_recommendations(user_id, top_k)
        # Hoặc bạn tự tạo vector user ảo => get_recommendations()
        top_recs = recommender.get_recommendations(user_id, top_k=top_k)
        
        # Đếm số bài gợi ý có category ∈ preferred_tags
        same_cat_count = 0
        for rec in top_recs:
            article = dantri_coll.find_one({"_id": rec["id"]}, {"category": 1})
            if article and article.get("category") in preferred_tags:
                same_cat_count += 1
        
        prec = same_cat_count / top_k
        sum_precision += prec
    
    avg_precision = sum_precision / n_users if n_users else 0.0
    print(f"Precision trung bình (Simulation-based) = {avg_precision:.4f}")

# Sử dụng:
# 1) Tạo users_sim = simulate_user_preferences()
# 2) evaluate_simulation(bert_model, db, users_sim, top_k=5)
