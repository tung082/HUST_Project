from flask_login import UserMixin
from pymongo import MongoClient
from bson.objectid import ObjectId
from flask_bcrypt import Bcrypt

bcrypt = Bcrypt()

# Kết nối MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["news_raw"]
users_collection = db["users"]

class User(UserMixin):
    def __init__(self, user_id, username, password_hash):
        self.id = str(user_id)
        self.username = username
        self.password_hash = password_hash

    @staticmethod
    def find_by_username(username):
        """Tìm user theo username"""
        user_data = users_collection.find_one({"username": username})
        if user_data:
            return User(user_data["_id"], user_data["username"], user_data["password"])
        return None

    @staticmethod
    def register(username, password):
        """Đăng ký người dùng mới"""
        if users_collection.find_one({"username": username}):
            return None  # Người dùng đã tồn tại
        
        password_hash = bcrypt.generate_password_hash(password).decode("utf-8")
        user_id = users_collection.insert_one({"username": username, "password": password_hash}).inserted_id
        return User(user_id, username, password_hash)

    @staticmethod
    def find_by_email(email):
        """Tìm user theo email"""
        user_data = users_collection.find_one({"email": email})
        if user_data:
            return User(user_data["_id"], user_data["username"], user_data["password"])
        return None


    def check_password(self, password):
        """Kiểm tra mật khẩu"""
        return bcrypt.check_password_hash(self.password_hash, password)
