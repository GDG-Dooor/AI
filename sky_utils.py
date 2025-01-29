import requests
import base64
import os

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
            if label['description'].lower() in ["sky", "cloud", "blue sky"] and label['score'] >= confidence_threshold:
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
