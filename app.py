from flask import Flask, request, jsonify
from flask_cors import CORS
import chatbot_db  # chatbot_db 모듈에서 데이터베이스와 GPT 함수 사용
import os
from dotenv import load_dotenv

# .env 파일 로드 (API 키와 환경 변수 설정)
load_dotenv()

# Flask 애플리케이션 초기화
app = Flask(__name__)
CORS(app)  # CORS 활성화 (프론트엔드와 통신 가능)

# 데이터베이스 초기화
print("Initializing database...")
chatbot_db.initialize_database()
print("Database initialized successfully.")

@app.route("/chat", methods=["POST"])
def chat():
    """
    사용자 입력을 받아 GPT 응답을 생성하는 API 엔드포인트
    """
    try:
        # JSON 데이터 가져오기
        data = request.json
        if not data:
            return jsonify({"error": "No data provided"}), 400

        # 사용자 ID와 입력값 가져오기
        user_id = data.get("user_id", "default_user")  # 기본값 설정
        user_input = data.get("user_input")

        if not user_input:
            return jsonify({"error": "User input is required"}), 400

        # GPT 응답 생성 (chatbot_db 모듈 사용)
        response = chatbot_db.get_gpt_response(user_id, user_input)

        # 응답 반환
        return jsonify({"response": response})

    except Exception as e:
        # 오류 발생 시 JSON으로 반환
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    # Flask 서버 실행
    app.run(host="0.0.0.0", port=5000, debug=True)
