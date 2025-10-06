from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from bson.objectid import ObjectId
from Recommender.tfidf_recommender import TFIDFRecommender
from Recommender.bert_recommender import BERTRecommender
from utils import get_weather, search_articles, get_exchange_rates  # Import các hàm từ utils
from models import User, bcrypt
from auth import auth_bp
from flask_login import LoginManager, login_required, current_user
from chatbot import process_chat_message
from urllib.parse import quote

app = Flask(__name__)
app.secret_key = "supersecretkey"

# Khởi tạo hệ thống gợi ý
tfidf_recommender = TFIDFRecommender()
bert_recommender = BERTRecommender()

def get_user_id():
    if "user_id" not in session:
        session["user_id"] = str(ObjectId())  
    return session["user_id"]

# Cấu hình Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "auth.login"

@login_manager.user_loader
def load_user(user_id):
    """Tải user từ database khi đăng nhập"""
    return User.find_by_username(user_id)

# Đăng ký Blueprint từ auth.py
app.register_blueprint(auth_bp)

@app.route('/search')
def search():
    query = request.args.get('query', '').strip()
    if not query:
        return render_template("search_results.html", query=query, results=[])
    recommender = tfidf_recommender
    results = recommender.search_articles(query, top_k=10)

    return render_template("search_results.html", query=query, results=results)

@app.route("/chatbot", methods=["POST"])
def global_chat():
    message = request.form.get("message")
    current_url = request.form.get("current_url")

    article_id = None
    if current_url:
        article_id = current_url.split("/")[-1]
        print(article_id)
    response_text = process_chat_message(message, article_id)

    # Lưu lịch sử trò chuyện vào session
    if 'chat_history' not in session:
        session['chat_history'] = []

    session['chat_history'].append({"role": "user", "content": message})
    session['chat_history'].append({"role": "bot", "content": response_text})

    # Trả về JSON để xử lý giao diện bằng JavaScript
    return jsonify({
        "user_message": message,
        "bot_response": response_text
    })


@app.after_request
def clear_chat_history(response):
    session.pop('chat_history', None)
    return response


@app.route("/set_algorithm", methods=["POST"])
def set_algorithm():
    algorithm = request.form.get("algorithm", "tfidf")  # Lấy thuật toán từ form
    use_time_ranking = request.form.get("use_time_ranking") == "yes"  # Lấy tùy chọn thời gian
    session["selected_algorithm"] = algorithm  # Lưu thuật toán vào session
    session["use_time_ranking"] = use_time_ranking  # Lưu tùy chọn thời gian vào session
    return redirect(url_for("index"))  # Quay lại trang chủ sau khi chọn

def get_recommender():
    """Trả về hệ thống gợi ý dựa trên thuật toán đã chọn"""
    selected_algorithm = session.get("selected_algorithm", "tfidf")  # Mặc định dùng TF-IDF
    use_time_ranking = session.get("use_time_ranking", True)  # Mặc định bật xếp hạng thời gian
    recommender = bert_recommender if selected_algorithm == "bert" else tfidf_recommender
    recommender.set_time_ranking(use_time_ranking)  # Truyền tùy chọn thời gian vào recommender
    return recommender

@app.route("/")
def index():
    user_id = get_user_id()
    recommender = get_recommender()  # Chọn thuật toán phù hợp
    recommended_articles = recommender.get_recommendations(user_id, top_k=40, test=True)
    algorithm_name = "BERT" if isinstance(recommender, BERTRecommender) else "TF-IDF"
    
    # Xử lý dữ liệu bài viết để tránh lỗi hiển thị
    for article in recommended_articles:
        article.setdefault("title", "Không có tiêu đề")
        article.setdefault("description", "Không có mô tả")
        article.setdefault("url", "#")
        article.setdefault("image_url", "/static/images/default.jpg")

    # Lấy thông tin thời tiết từ utils.py
    weather = get_weather()

    return render_template(
        "index.html", 
        articles=recommended_articles, 
        weather=weather,
        algorithm_name=algorithm_name)

@app.route("/article/<article_id>")
def article_detail(article_id):
    article_id = ObjectId(article_id)
    recommender = get_recommender()
    article = recommender.dantri.find_one({"_id": article_id})

    if not article:
        return "Bài viết không tồn tại", 404

    user_id = get_user_id()
    tfidf_recommender.update_user_profile(user_id, article_id)
    bert_recommender.update_user_profile(user_id, article_id)
    similar_articles = recommender.get_recommendations(user_id, top_k=5)

    return render_template("article.html", article=article, similar_articles=similar_articles)

@app.context_processor
def inject_global_data():
    """Truyền dữ liệu tỷ giá và thời tiết vào mọi template."""
    weather = get_weather()
    exchange_rates = get_exchange_rates()
    return dict(weather=weather, exchange_rates=exchange_rates)

if __name__ == "__main__":
    app.run(debug=True)
