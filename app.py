from flask import Flask, request, jsonify
from flask_cors import CORS
import chatbot_db  # chatbot.py의 GPT 기능 사용
import os
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

app = Flask(__name__)
CORS(app)  # CORS 활성화 (프론트엔드와 연결 가능)

# API 엔드포인트: 사용자 입력을 GPT로 보내고 응답 반환
@app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.json
        user_id = data.get("user_id", "default_user")
        user_input = data.get("user_input")

        if not user_input:
            return jsonify({"error": "User input is required"}), 400

        # chatbot.py의 GPT 응답 생성 함수 호출
        response = chatbot_db.get_gpt_response(user_id, user_input)

        return jsonify({"response": response})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 서버 실행
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
