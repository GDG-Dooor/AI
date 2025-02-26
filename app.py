from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import sqlite3
from dotenv import load_dotenv
from chatbot import ChatBot, get_recent_memory, save_memory  # chatbot.py의 기능 활용

# .env 파일 로드
load_dotenv()

# Flask 앱 설정
app = Flask(__name__)
CORS(app)  # CORS 활성화 (프론트엔드와 연결 가능)

# 챗봇 인스턴스 생성
chatbot = ChatBot()

# SQLite 데이터베이스 파일 경로
DB_FILE = os.path.join(os.getcwd(), "chat_memory.db")

# 데이터베이스 초기화 함수
def initialize_database():
    """대화 기록을 저장하는 SQLite 데이터베이스 초기화"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chat_memory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        conn.close()
        print("✅ Database initialized successfully.")
    except Exception as e:
        print(f"❌ Database initialization error: {e}")

# 🔹 API 엔드포인트: 챗봇과 대화 (POST)
@app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.json
        user_id = data.get("user_id", "default_user")
        user_name = data.get("user_name")
        user_input = data.get("message")

        if not user_input:
            return jsonify({"error": "User input is required"}), 400

        # 챗봇 응답 생성 (이전 대화 기록 포함)
        bot_response = chatbot.generate_response(user_id, user_name, user_input)

        return jsonify({
            "poi": bot_response
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 🔹 API 엔드포인트: 특정 사용자의 대화 기록 조회 (GET)
@app.route("/history/<user_id>", methods=["GET"])
def get_history(user_id):
    try:
        history = get_recent_memory(user_id, limit=50)  # 최근 20개 대화 불러오기
        return jsonify({"user_id": user_id, "history": history})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 🔹 API 엔드포인트: 특정 사용자의 대화 기록 삭제 (DELETE)
@app.route("/history/<user_id>", methods=["DELETE"])
def delete_history(user_id):
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM chat_memory WHERE user_id = ?", (user_id,))
        conn.commit()
        conn.close()
        return jsonify({"message": f"Deleted chat history for user: {user_id}"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 서버 실행
if __name__ == "__main__":
    initialize_database()
    app.run(host="0.0.0.0", port=5000, debug=True)
