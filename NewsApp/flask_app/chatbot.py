import openai
from utils import get_time_info, get_weather, get_exchange_rates, get_article_summary
from bson.objectid import ObjectId
from pymongo import MongoClient

# Cấu hình API của OpenAI
openai.api_key = "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"

# Kết nối MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["news_raw"]
dantri_collection = db["dantri"]  # Sử dụng collection dantri để lấy dữ liệu bài báo

# Định nghĩa các hàm cho function calling
functions = [
    {
        "name": "get_weather",
        "description": "Lấy thông tin thời tiết hiện tại.",
        "parameters": {}
    },
    {
        "name": "get_exchange_rates",
        "description": "Lấy tỷ giá USD từ Vietcombank.",
        "parameters": {}
    },
    {
        "name": "get_time_info",
        "description": "Lấy thời gian hiện tại.",
        "parameters": {}
    },
    {
        "name": "get_article_summary",
        "description": "Tóm tắt nội dung bài báo hiện tại.",
        "parameters": {
            "type": "object",
            "properties": {
                "article_id": {"type": "string"}
            },
            "required": ["url"]
        }
    }
]

# Hàm xử lý tin nhắn từ người dùng với function calling
def process_chat_message(message, article_id=None):
    """Xử lý yêu cầu từ người dùng và gọi hàm tương ứng nếu cần."""
    messages = [{"role": "user", "content": message}]

    try:
        response = openai.chat.completions.create(
            model="gpt-4",
            messages=messages,
            functions=functions,
            function_call="auto"  # Tự động gọi hàm phù hợp
        )

        response_message = response.choices[0].message

        if response_message.function_call:
            function_name = response_message.function_call.name
            arguments = response_message.function_call.arguments or {}

            # Gọi các hàm tương ứng
            if function_name == "get_weather":
                weather_data = get_weather()
                return f"Thời tiết hiện tại: {weather_data['temp']}°C, {weather_data['description']}."

            elif function_name == "get_exchange_rates":
                rates = get_exchange_rates()
                if rates:
                    usd_rate = rates[0]
                    return (
                        f"Tỷ giá USD:\n"
                        f"• Mua vào: {usd_rate['buy']} VND\n"
                        f"• Chuyển khoản: {usd_rate['transfer']} VND\n"
                        f"• Bán ra: {usd_rate['sell']} VND"
                    )
                return "Không có dữ liệu tỷ giá."

            elif function_name == "get_time_info":
                return f"Thời gian hiện tại: {get_time_info()}"

            elif function_name == "get_article_summary":
                if article_id:
                    article = dantri_collection.find_one({"_id": ObjectId(article_id)})
                    if article:
                        return get_article_summary(article_id)
                    return "Không tìm thấy bài báo để tóm tắt."
                return "Bạn chưa chọn bài viết nào để tóm tắt."

        # Trả lời trực tiếp nếu không cần gọi hàm
        return response_message.content

    except Exception as e:
        return f"❌ Đã xảy ra lỗi khi xử lý yêu cầu: {str(e)}"

    except Exception as e:
        return f"❌ Đã xảy ra lỗi khi xử lý yêu cầu: {str(e)}"
