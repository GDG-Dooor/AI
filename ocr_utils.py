import requests
import base64
import re
import os
from dotenv import load_dotenv


# .env 파일에서 환경 변수 로드
load_dotenv()

# Google Vision API 키 설정
API_KEY = os.getenv("GOOGLE_API_KEY") 
VISION_API_URL = f"https://vision.googleapis.com/v1/images:annotate?key={API_KEY}"

def detect_text_with_api_key(image_content):
    """
    Google Vision API를 사용하여 이미지에서 텍스트 추출
    - image_content: Base64로 인코딩된 이미지 데이터
    """
    payload = {
        "requests": [
            {
                "image": {
                    "content": image_content
                },
                "features": [
                    {
                        "type": "TEXT_DETECTION"  # 텍스트 감지
                    }
                ]
            }
        ]
    }

    response = requests.post(VISION_API_URL, json=payload)

    if response.status_code == 200:
        result = response.json()
        texts = result.get("responses", [])[0].get("textAnnotations", [])
        if texts:
            return texts[0]["description"]  # 감지된 텍스트 반환
        else:
            return ""
    else:
        raise Exception(f"Vision API 호출 실패: {response.status_code}, {response.text}")
    

def detect_handwritten_text(image_content):
    """
    Google Vision API를 사용하여 손글씨 텍스트 추출
    - image_content: Base64로 인코딩된 이미지 데이터
    """
    payload = {
        "requests": [
            {
                "image": {
                    "content": image_content
                },
                "features": [
                    {
                        "type": "DOCUMENT_TEXT_DETECTION"  # 손글씨 인식 최적화
                    }
                ]
            }
        ]
    }

    response = requests.post(VISION_API_URL, json=payload)

    if response.status_code == 200:
        result = response.json()
        responses = result.get("responses", [])
        if not responses or "textAnnotations" not in responses[0]:
            return ""

        texts = responses[0]["textAnnotations"]
        return texts[0]["description"] if texts else ""
    else:
        raise Exception(f"Vision API 호출 실패: {response.status_code}, {response.text}")


def is_receipt(text):
    """
    추출된 텍스트가 영수증인지 판단
    """
    keywords = ["합계", "금액", "현금", "카드", "총액", "부가세", "영수증"]

    for keyword in keywords:
        if keyword in text:
            return True

    if re.search(r"\d{1,3}(,\d{3})*원", text):
        return True

    if re.search(r"\d{4}[/-]\d{2}[/-]\d{2}", text) or re.search(r"\d{2}[/-]\d{2}[/-]\d{4}", text):
        return True

    return False

def is_movie_ticket(text):
    """
    추출된 텍스트가 영화표인지 판단
    """
    keywords = ["영화", "티켓", "좌석", "상영", "관람", "시간", "극장", "예매", "입장","CGV", "메가박스", "롯데시네마"]

    # 키워드 검사
    for keyword in keywords:
        if keyword in text:
            return True

    return False

def is_library_receipt(text):
    """
    추출된 텍스트가 도서관 대출증인지 판단
    """
    keywords = ["도서관", "대출", "반납", "도서","대출확인증"]

    # 키워드 검사
    for keyword in keywords:
        if keyword in text:
            return True

    return False

def is_writing_motivation(text):
    """
    추출된 텍스트가 "나는 잘하고 있어"인지 판단
    """
    target_text = "나는 잘하고 있어"

    return target_text in text

