import os
import json
import sqlite3
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from utils import initialize_retriever, fetch_data

# 환경 변수 로드
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# SQLite 데이터베이스 파일 경로
DB_FILE = os.path.join(os.getcwd(), "chat_memory.db")

# 데이터베이스 초기화 함수
def initialize_database():
    """데이터베이스 파일과 테이블을 초기화"""
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

# 대화 저장 함수
def save_memory(user_id, role, content):
    """대화를 SQLite 데이터베이스에 저장"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO chat_memory (user_id, role, content)
            VALUES (?, ?, ?)
        ''', (user_id, role, content))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"❌ Error saving data: {e}")

# 최근 대화 불러오기 함수
def get_recent_memory(user_id, limit=5):
    """최근 대화 내용을 가져옴"""
    try:
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
        return [{"role": row[0], "content": row[1]} for row in reversed(rows)]
    except Exception as e:
        print(f"❌ Error retrieving data: {e}")
        return []

class ReintegrationChatBot:
    def __init__(self, bot_name="소셜 가이드"):
        self.bot_name = bot_name
        self.retriever = initialize_retriever()
        self.llm = ChatOpenAI(model_name="gpt-4o", temperature=0.7)

    def generate_response(self, user_id, user_input):
        """이전 대화 기록을 반영하여 응답 생성"""
        related_docs = fetch_data(self.retriever, user_input)
        chat_history = get_recent_memory(user_id)
        chat_summary = "\n".join([f"{msg['role']}: {msg['content']}" for msg in chat_history])

        prompt_template = ChatPromptTemplate.from_template("""
        [역할 설정]
        당신은 은둔형 외톨이의 사회화를 도와주는 친근한 친구 같은 AI 챗봇입니다.
        공감하고 용기를 주며, 친근한 말투로 반말로 답변합니다.
        
        [사용자 질문]
        {query}
        
        [관련 정보]
        {context_docs}
        
        [이전 대화 기록]
        {chat_history}
        
        [응답 지침]
        1. 긍정적이고 따뜻한 말투 유지
        2. 강요 없이 조언 제공
        3. 답변은 50자 이내
        
        [최종 답변]
        """)

        input_data = {
            "query": user_input,
            "context_docs": "\n".join(related_docs),
            "chat_history": chat_summary,
        }

        response_chain = prompt_template | self.llm | StrOutputParser()
        bot_reply = response_chain.invoke(input_data)
        
        save_memory(user_id, "user", user_input)
        save_memory(user_id, "assistant", bot_reply)
        return bot_reply



