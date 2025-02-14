import os
import json
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from utils import initialize_retriever, fetch_data

# 환경 변수 로드
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# 대화 기록 저장 경로
CHAT_HISTORY_PATH = "chat_history.json"

class ReintegrationChatBot:
    def __init__(self, bot_name="소셜 가이드"):
        self.bot_name = bot_name
        self.retriever = initialize_retriever()
        self.llm = ChatOpenAI(model_name="gpt-4o", temperature=0.7)
        self.chat_history = self.load_chat_history()

    def load_chat_history(self):
        """대화 기록을 JSON에서 불러오기"""
        if os.path.exists(CHAT_HISTORY_PATH):
            with open(CHAT_HISTORY_PATH, "r", encoding="utf-8") as file:
                return json.load(file)
        return {}

    def save_chat_history(self):
        """현재 대화 기록을 JSON 파일에 저장"""
        with open(CHAT_HISTORY_PATH, "w", encoding="utf-8") as file:
            json.dump(self.chat_history, file, ensure_ascii=False, indent=4)

    def get_chat_summary(self, session_id):
        """이전 대화 내용을 요약하여 반환"""
        history = self.chat_history.get(session_id, [])
        if not history:
            return "이전 대화 기록 없음"
        summary = "\n".join([f"사용자: {msg['user']}\n챗봇: {msg['bot']}" for msg in history[-5:]])
        return summary

    def store_conversation(self, session_id, user_msg, bot_reply):
        """대화 기록 저장"""
        if session_id not in self.chat_history:
            self.chat_history[session_id] = []
        self.chat_history[session_id].append({"user": user_msg, "bot": bot_reply})
        self.save_chat_history()

    def generate_response(self, session_id, user_input):
        """유사한 문서 검색 후 LLM을 통해 답변 생성"""
        related_docs = fetch_data(self.retriever, user_input)
        chat_summary = self.get_chat_summary(session_id)

        prompt_template = ChatPromptTemplate.from_template("""
        [역할 설정]
        당신은 은둔형 외톨이의 사회화를 도와주는 친근한 친구같은 ai채팅봇입니다.
        사용자가 은둔 생활에서 벗어나도록 정서적 지지와 실용적인 조언을 제공합니다.
        공감을 잘해야 하며 용기와 격려를 해줘야 합니다.
        

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
        
        self.store_conversation(session_id, user_input, bot_reply)
        return bot_reply

# 실행
if __name__ == "__main__":
    chatbot = ReintegrationChatBot()
    session_id = "user_1"

    while True:
        user_input = input("\n💬 사용자: ")
        if user_input.lower() in ["exit", "quit"]:
            print("🔚 챗봇 종료")
            break
        response = chatbot.generate_response(session_id, user_input)
        print(f"🤖 챗봇: {response}")
