from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_community.document_loaders import TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from dotenv import load_dotenv
import os

# 환경 변수 로드
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
 
# 심리 지원 관련 데이터 리스트
data_list = ['심리지원']

def load_and_split_txt(txt_path, chunk_size=200, chunk_overlap=50):
    """
    텍스트 데이터를 로드하고, 적절한 크기로 분할하는 함수
    """
    loader = TextLoader(txt_path, encoding="utf-8")
    data = loader.load()

    text_splitter = RecursiveCharacterTextSplitter(
        separators=["\n\n"],
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len
    )
    
    return text_splitter.split_documents(data)

# OpenAI 임베딩 초기화
embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)

for data in data_list:
    file_path = f'data/{data}.txt'
    
    if os.path.exists(file_path):
        texts = load_and_split_txt(file_path)
        db = Chroma.from_documents(texts, embeddings, persist_directory=f"./data/embedding/{data}_chroma_db")
