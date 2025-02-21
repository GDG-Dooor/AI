import os
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# OpenAI 임베딩 모델 초기화
embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)

# ChromaDB 연결
vector_db = Chroma(persist_directory="./data/embedding/심리지원_chroma_db", embedding_function=embeddings)

def initialize_retriever():
    """
    유사도 점수 기반 검색을 위한 retriever 초기화
    """
    return vector_db.as_retriever(
        search_type="similarity_score_threshold",
        search_kwargs={"score_threshold": 0.7}  # 기존 0.8 → 0.5로 변경 (검색 범위 확장)
    )

def fetch_data(retriever, query, max_docs=2):
    """
    Retriever를 사용해 query와 유사한 문서를 검색하고, 검색된 문서의 내용을 출력하는 함수
    """
    docs = retriever.invoke(query)  

    if not docs:  # 검색된 문서가 없을 경우
        #print("\n⚠ 검색된 문서가 없습니다. ChromaDB에 데이터가 제대로 저장되었는지 확인하세요.")
        return []

    #print(f"\n🔎 검색된 문서 개수: {len(docs)}")
    
    results = []
    for i, doc in enumerate(docs[:max_docs]):
       # print(f"\n📄 [{i+1}] 문서 내용:\n{doc.page_content}")
        results.append(doc.page_content)
    
    return results
"""
if __name__ == "__main__":
    # 사용자 입력 받기
    query = input("\n💬 검색할 질문을 입력하세요: ")

    # Retriever 초기화
    retriever = initialize_retriever()

    # 검색 후 결과 출력
    fetch_data(retriever, query)
"""