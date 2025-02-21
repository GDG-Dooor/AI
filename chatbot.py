import os
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

# 대화 저장 함수 (순서 보장)
def save_memory(user_id, user_input, bot_reply):
    """사용자 입력과 챗봇 응답을 같은 트랜잭션 내에서 저장하여 순서를 보장"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # 트랜잭션 시작 (BEGIN)
        cursor.execute('''
            INSERT INTO chat_memory (user_id, role, content)
            VALUES (?, ?, ?)
        ''', (user_id, "user", user_input))

        cursor.execute('''
            INSERT INTO chat_memory (user_id, role, content)
            VALUES (?, ?, ?)
        ''', (user_id, "assistant", bot_reply))

        # 트랜잭션 완료 (COMMIT)
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"❌ Error saving data: {e}")

# 최근 대화 불러오기 함수
def get_recent_memory(user_id, limit=50):
    """최근 대화 내용을 가져옴"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT role, content FROM chat_memory
            WHERE user_id = ?
            ORDER BY timestamp ASC  -- 올바른 순서 보장
            LIMIT ?
        ''', (user_id, limit))
        rows = cursor.fetchall()
        conn.close()
        return [{"role": row[0], "content": row[1]} for row in rows]
    except Exception as e:
        print(f"❌ Error retrieving data: {e}")
        return []

class ChatBot:
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
        당신은 은둔형 외톨이의 사회화를 도와주는 친근한 친구같은 ai채팅봇입니다.
        사용자가 은둔 생활에서 벗어나도록 정서적 지지와 실용적인 조언을 제공합니다.
        공감을 잘해야 하며 용기와 격려를 해줘야 합니다.
        당신의 이름은 "포이" 입니다. 꼭 기억하세요. 

        [사용자 질문]
        {query}

        [관련 정보]
        {context_docs}

        [이전 대화 기록]
        {chat_history}

        [응답 지침]
        1. 부드럽고 **긍정적인 어조를 유지**하며, 친구처럼 **친근하게 반말로 대답하세요**.
        2. 사용자가 부담을 느끼지 않도록 강요하지 않고, 용기를 주세요.
        3. 현실적인 조언을 하되, 강요하지 마세요.
        4. 답변은 되도록 50자 이내로 해주세요.

        [최종 답변]
        """)

        input_data = {
            "query": user_input,
            "context_docs": "\n".join(related_docs),
            "chat_history": chat_summary,
        }

        response_chain = prompt_template | self.llm | StrOutputParser()
        bot_reply = response_chain.invoke(input_data)

        # ✅ 사용자의 입력과 챗봇의 응답을 한 번에 저장하여 순서 유지
        save_memory(user_id, user_input, bot_reply)

        return bot_reply

# 실행 예제
if __name__ == "__main__":
    initialize_database()  # 데이터베이스 초기화
    chatbot = ChatBot()

    user_id = "user_1234"
    while True:
        user_input = input("👤 사용자: ")
        if user_input.lower() in ["exit", "quit"]:
            print("👋 챗봇 종료!")
            break
        bot_reply = chatbot.generate_response(user_id, user_input)
        print(f"🤖 포이: {bot_reply}")



