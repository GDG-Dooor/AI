import openai
import sqlite3
import os

# 환경 변수에서 API 키 가져오기
openai.api_key = os.getenv("OPENAI_API_KEY")

# SQLite 데이터베이스 파일 경로
DB_FILE = "chat_memory.db"

# 데이터베이스 초기화 함수
def initialize_database():
    """
    데이터베이스 파일과 테이블을 초기화합니다.
    파일이 없으면 생성하고, 테이블이 없으면 생성합니다.
    """
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

# 대화 저장 함수
def save_memory(user_id, role, content):
    """
    대화를 데이터베이스에 저장합니다.
    """
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO chat_memory (user_id, role, content)
        VALUES (?, ?, ?)
    ''', (user_id, role, content))
    conn.commit()
    conn.close()

# 최근 대화 가져오기 함수
def get_recent_memory(user_id, limit=10):
    """
    지정된 사용자 ID의 최근 대화를 가져옵니다.
    """
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT role, content FROM chat_memory
        WHERE user_id = ?
        ORDER BY timestamp DESC
        LIMIT ?
    ''', (user_id, limit))
    rows = cursor.fetchall()
    conn.close()
    # 가장 최근 대화가 맨 마지막에 오도록 순서 변경
    return [{"role": row[0], "content": row[1]} for row in reversed(rows)]

# GPT 응답 생성 함수
def get_gpt_response(user_id, user_input):
    """
    GPT-3.5 모델을 사용하여 응답을 생성합니다.
    """
    recent_memory = get_recent_memory(user_id)

    messages = [
        {
            "role": "system",
            "content": (
                "You are a kind and understanding chatbot. Always provide helpful and "
                "clear responses with a friendly and respectful tone. Focus on solving "
                "the user's problem or providing information, and avoid phrases like "
                "'I’m sorry' unless absolutely necessary. Be positive, encouraging, and concise."
            )
        }
    ]
    messages.extend(recent_memory)
    messages.append({"role": "user", "content": user_input})

    # OpenAI API 호출
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages,
        max_tokens=150,
        temperature=0.7
    )

    # GPT 응답 추출
    bot_response = response.choices[0].message["content"]

    # 대화 저장
    save_memory(user_id, "user", user_input)
    save_memory(user_id, "assistant", bot_response)

    # 응답 반환
    return bot_response


# 데이터베이스 초기화 (테스트 목적으로 호출)
if __name__ == "__main__":
    initialize_database()
    print("Database initialized and ready to use.")
