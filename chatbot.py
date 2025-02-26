from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import sqlite3
from dotenv import load_dotenv
import os
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from utils import initialize_retriever, fetch_data


# 환경 변수 로드
load_dotenv()

# FastAPI 앱 생성
app = FastAPI()

# OpenAI API 키
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# SQLite 데이터베이스 파일 경로
DB_FILE = os.path.join(os.getcwd(), "chat_memory.db")

# 데이터베이스 초기화 함수
def initialize_database():
    """데이터베이스 파일과 테이블을 초기화"""
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
def save_memory(user_id, user_input, bot_reply):
    """사용자 입력과 챗봇 응답을 같은 트랜잭션 내에서 저장"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO chat_memory (user_id, role, content)
        VALUES (?, ?, ?)
    ''', (user_id, "user", user_input))

    cursor.execute('''
        INSERT INTO chat_memory (user_id, role, content)
        VALUES (?, ?, ?)
    ''', (user_id, "assistant", bot_reply))

    conn.commit()
    conn.close()

# 최근 대화 불러오기 함수
def get_recent_memory(user_id, limit=50):
    """최근 대화 내용을 가져옴"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT role, content FROM chat_memory
        WHERE user_id = ?
        ORDER BY timestamp ASC
        LIMIT ?
    ''', (user_id, limit))
    rows = cursor.fetchall()
    conn.close()
    return [{"role": row[0], "content": row[1]} for row in rows]

# 챗봇 클래스
class ChatBot:
    def __init__(self, bot_name="포이"):
        self.bot_name = bot_name
        self.retriever = initialize_retriever()
        self.llm = ChatOpenAI(model_name="gpt-4o", temperature=0.7)

    def generate_response(self, user_id, user_name, user_input):
        """이전 대화 기록을 반영하여 응답 생성"""
        related_docs = fetch_data(self.retriever, user_input)
        chat_history = get_recent_memory(user_id)
        chat_summary = "\n".join([f"{msg['role']}: {msg['content']}" for msg in chat_history])

        # ✅ user_id 값을 템플릿에 적용
        prompt_template = ChatPromptTemplate.from_template("""
        [역할 설정]
        당신은 은둔형 외톨이의 사회화를 도와주는 친근한 AI 챗봇입니다.
        사용자가 은둔 생활에서 벗어나도록 정서적 지지와 실용적인 조언을 제공합니다.
        공감을 잘해야 하며, 용기와 격려를 해줘야 합니다.
        당신의 이름은 "포이"입니다. 꼭 기억하세요.

        [사용자 정보]
        사용자의 이름은 "{user_name}"입니다. 대화할 때 이 이름을 사용하세요.

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

        # ✅ user_id 적용
        input_data = {
            "user_id": user_id,
            "user_name" : user_name,
            "query": user_input,
            "context_docs": "\n".join(related_docs),
            "chat_history": chat_summary,
        }

        response_chain = prompt_template | self.llm | StrOutputParser()
        bot_reply = response_chain.invoke(input_data)

        # ✅ 대화 기록 저장
        save_memory(user_id, user_input, bot_reply)

        return bot_reply

# 챗봇 인스턴스 생성
chatbot = ChatBot()

# API 요청 데이터 모델
class ChatRequest(BaseModel):
    user_id: str
    user_input: str

# POST 요청: 챗봇 응답 생성
@app.post("/chat")
def chat(request: ChatRequest):
    """
    user_id와 user_input을 JSON 형식으로 보내면 챗봇이 응답을 생성하여 반환.
    """
    try:
        user_id = request.user_id
        user_input = request.user_input

        bot_reply = chatbot.generate_response(user_id, user_input)
        return {"user_id": user_id, "bot_reply": bot_reply}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"챗봇 처리 중 오류 발생: {str(e)}")

# GET 요청: 사용자 채팅 기록 조회
@app.get("/history")
def get_chat_history(user_id: str):
    """
    user_id를 기반으로 최근 대화 기록을 조회하는 API.
    `https://ai-iyjk.onrender.com/history?user_id=Dooor` 형태로 요청 가능.
    """
    try:
        chat_history = get_recent_memory(user_id)
        return {"user_id": user_id, "chat_history": chat_history}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"채팅 기록 조회 중 오류 발생: {str(e)}")

# 데이터베이스 초기화
initialize_database()









