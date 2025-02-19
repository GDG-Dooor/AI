import requests
import base64
import os
from dotenv import load_dotenv

# .env 파일에서 환경 변수 로드
load_dotenv()

# Google Vision API 키 설정
API_KEY = os.getenv("GOOGLE_API_KEY")
VISION_API_URL = f"https://vision.googleapis.com/v1/images:annotate?key={API_KEY}"

def sky_image(image_content, confidence_threshold=0.8):
    """
    Google Vision API를 사용하여 하늘 사진인지 분석
    - image_content: Base64로 인코딩된 이미지 데이터
    - confidence_threshold: 신뢰도 기준 (기본값: 0.8)
    """
    payload = {
        "requests": [
            {
                "image": {
                    "content": image_content
                },
                "features": [
                    {
                        "type": "LABEL_DETECTION",  # 라벨 감지
                        "maxResults": 10
                    }
                ]
            }
        ]
    }

    response = requests.post(VISION_API_URL, json=payload)

    if response.status_code == 200:
        labels = response.json().get("responses", [])[0].get("labelAnnotations", [])
        is_sky = False
        detected_labels = []

        for label in labels:
            detected_labels.append({
                "label": label['description'],
                "confidence": label['score']
            })
            if label['description'].lower() in ["sky", "cloud", "blue sky", "galaxy", "star"] and label['score'] >= confidence_threshold:
                is_sky = True

        return {
            "is_sky": is_sky,
            "labels": detected_labels
        }
    else:
        return {
            "error": f"Vision API 오류: {response.status_code}",
            "details": response.text
        }
    
def mountain_image(image_content, confidence_threshold=0.8):
    """
    Google Vision API를 사용하여 산 사진인지 분석
    - image_content: Base64로 인코딩된 이미지 데이터
    - confidence_threshold: 신뢰도 기준 (기본값: 0.8)
    """
    payload = {
        "requests": [
            {
                "image": {
                    "content": image_content
                },
                "features": [
                    {
                        "type": "LABEL_DETECTION",  # 라벨 감지
                        "maxResults": 10
                    }
                ]
            }
        ]
    }

    response = requests.post(VISION_API_URL, json=payload)

    if response.status_code == 200:
        labels = response.json().get("responses", [])[0].get("labelAnnotations", [])
        is_mountain = False
        detected_labels = []

        for label in labels:
            detected_labels.append({
                "label": label['description'],
                "confidence": label['score']
            })
            if label['description'].lower() in ["mountain", "hill", "rock", "peak", "ridge","nature reserve"] and label['score'] >= confidence_threshold:
                is_mountain = True

        return {
            "is_mountain": is_mountain,
            "labels": detected_labels
        }
    else:
        return {
            "error": f"Vision API 오류: {response.status_code}",
            "details": response.text
        }
    
def fried_egg_image(image_content, confidence_threshold=0.8):
    """
    Google Vision API를 사용하여 계란 후라이 사진인지 분석
    - image_content: Base64로 인코딩된 이미지 데이터
    - confidence_threshold: 신뢰도 기준 (기본값: 0.8)
    """
    payload = {
        "requests": [
            {
                "image": {
                    "content": image_content
                },
                "features": [
                    {
                        "type": "LABEL_DETECTION",  # 라벨 감지
                        "maxResults": 10
                    }
                ]
            }
        ]
    }

    response = requests.post(VISION_API_URL, json=payload)

    if response.status_code == 200:
        labels = response.json().get("responses", [])[0].get("labelAnnotations", [])
        is_fried_egg = False
        detected_labels = []

        for label in labels:
            detected_labels.append({
                "label": label['description'],
                "confidence": label['score']
            })
            if label['description'].lower() in ["fried egg", "yolk",] and label['score'] >= confidence_threshold:
                is_fried_egg = True

        return {
            "is_fried_egg": is_fried_egg,
            "labels": detected_labels
        }
    else:
        return {
            "error": f"Vision API 오류: {response.status_code}",
            "details": response.text
        }

