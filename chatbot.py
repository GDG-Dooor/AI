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

# ✅ 데이터베이스 초기화 (요약 저장 테이블 추가)
def initialize_database():
    """데이터베이스 파일과 테이블을 초기화"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        # 기존 대화 기록 테이블
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chat_memory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        # 요약본 저장 테이블
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS summary_memory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                summary TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        conn.close()
        print("✅ Database initialized successfully.")
    except Exception as e:
        print(f"❌ Database initialization error: {e}")

# ✅ 요약본을 별도로 저장하는 방식
def summarize_old_chats(user_id):
    """대화가 20개 초과하면 오래된 대화를 요약하고 요약본을 별도 저장"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        # 1️⃣ 대화 개수 확인
        cursor.execute("SELECT COUNT(*) FROM chat_memory WHERE user_id = ?", (user_id,))
        count = cursor.fetchone()[0]

        if count <= 20:
            conn.close()
            return "✅ 아직 요약할 필요 없음"

        # 2️⃣ 최신 20개를 제외한 나머지 오래된 대화 가져오기
        cursor.execute('''
            SELECT content FROM chat_memory
            WHERE user_id = ?
            ORDER BY timestamp ASC
            LIMIT ?
        ''', (user_id, count - 20))
        old_messages = "\n".join([row[0] for row in cursor.fetchall()])

        # 3️⃣ GPT로 요약 생성
        summary_prompt = ChatPromptTemplate.from_template("""
        [대화 기록]
        {chat_history}

        [요약]
        - 중요한 내용을 간결하게 정리하세요.
        - 질문과 답변의 핵심 내용만 남기고, 반복된 대화는 제거하세요.
        - 길이는 500자 이내로 유지하세요.
        """)

        input_data = {"chat_history": old_messages}
        llm = ChatOpenAI(model_name="gpt-4o", temperature=0.7)
        response_chain = summary_prompt | llm | StrOutputParser()
        summarized_past = response_chain.invoke(input_data)

        # 4️⃣ 요약된 대화를 summary_memory 테이블에 저장
        cursor.execute("INSERT INTO summary_memory (user_id, summary) VALUES (?, ?)", 
                       (user_id, summarized_past))

        # 5️⃣ 기존의 오래된 대화 삭제 (최신 20개만 유지)
        cursor.execute('''
            DELETE FROM chat_memory 
            WHERE user_id = ? AND id NOT IN (
                SELECT id FROM chat_memory
                WHERE user_id = ?
                ORDER BY timestamp DESC
                LIMIT 20
            )
        ''', (user_id, user_id))

        conn.commit()
        conn.close()
        return "✅ 대화 요약 완료"
    except Exception as e:
        print(f"❌ 요약 오류: {e}")
        return "❌ 요약 실패"

# ✅ 기존 save_memory()에 자동 요약 기능 추가
def save_memory(user_id, role, content):
    """대화를 SQLite 데이터베이스에 저장하고, 20개 초과 시 자동 요약"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO chat_memory (user_id, role, content)
            VALUES (?, ?, ?)
        ''', (user_id, role, content))
        conn.commit()
        conn.close()

        # 🟢 대화가 20개 이상이면 자동으로 요약 실행
        summarize_old_chats(user_id)

    except Exception as e:
        print(f"❌ Error saving data: {e}")


# ✅ 기존 대화 불러오기 (최신 20개 + 요약본 추가)
def get_recent_memory(user_id, limit=20):
    """최근 대화 내용을 가져오며, 요약본이 있으면 추가"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # 1️⃣ 최신 20개 대화 가져오기
        cursor.execute('''
            SELECT role, content FROM chat_memory
            WHERE user_id = ?
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (user_id, limit))
        recent_chats = [{"role": row[0], "content": row[1]} for row in reversed(cursor.fetchall())]

        # 2️⃣ 요약본 가져오기
        cursor.execute('''
            SELECT summary FROM summary_memory
            WHERE user_id = ?
            ORDER BY timestamp DESC
            LIMIT 1
        ''', (user_id,))
        summary = cursor.fetchone()
        conn.close()

        if summary:
            recent_chats.insert(0, {"role": "assistant", "content": f"[이전 대화 요약]\n{summary[0]}"})

        return recent_chats
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
        
        save_memory(user_id, "user", user_input)
        save_memory(user_id, "assistant", bot_reply)
        return bot_reply
