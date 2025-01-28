import openai
import json
import os

# 환경 변수에서 API 키 가져오기
openai.api_key = os.getenv("OPENAI_API_KEY")

# 메모리 저장소
MEMORY_FILE = "memory.json"

# 메모리 초기화 및 파일 로드
if os.path.exists(MEMORY_FILE):
    with open(MEMORY_FILE, "r", encoding="utf-8") as f:
        memory = json.load(f)
else:
    memory = {}

# 대화 저장 함수
def save_memory(user_id, role, content):
    if user_id not in memory:
        memory[user_id] = []
    memory[user_id].append({"role": role, "content": content})

    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(memory, f, indent=4, ensure_ascii=False)

# 최근 대화 가져오기
def get_recent_memory(user_id):
    return memory.get(user_id, [])

# GPT 응답 생성 함수
def get_gpt_response(user_id, user_input):
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

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages,
        max_tokens=150,
        temperature=0.7
    )

    bot_response = response.choices[0].message["content"]

    # 대화 저장
    save_memory(user_id, "user", user_input)
    save_memory(user_id, "assistant", bot_response)

    return bot_response
