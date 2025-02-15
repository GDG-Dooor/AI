from flask import Flask, request, jsonify
import torch
import base64
import io
import os
import gdown
import pathlib
from PIL import Image
from ocr_utils import detect_text_with_api_key, detect_handwritten_text, is_receipt, is_movie_ticket, is_writing_motivation, is_library_receipt
from vision_utils import sky_image, mountain_image, fried_egg_image

# Windows 환경에서 PosixPath 오류 방지 (WindowsPath로 강제 변경)
if os.name == "nt":  
    temp = pathlib.PosixPath
    pathlib.PosixPath = pathlib.WindowsPath


# Flask 인스턴스 생성
app = Flask(__name__)

# Google Drive에서 YOLO 모델 파일 ID
best_pt_id = "17tuBF-Rktb6f8PSAEq98swyaxO--dl9J" # `best.pt`의 파일 ID
best2_pt_id = "1bQnF8hSOHZDNl0FVkRr4epLGKOCXTm6H"    # `best2.pt`의 파일 ID

# 다운로드할 경로 설정
model_path = os.path.join(os.getcwd(), "best.pt")
mic_model_path = os.path.join(os.getcwd(), "best2.pt")

# Google Drive에서 파일 다운로드 함수
def download_from_gdrive(file_id, save_path):
    if not os.path.exists(save_path):  # 파일이 없을 때만 다운로드
        print(f"📥 {save_path} 다운로드 중...")
        url = f"https://drive.google.com/uc?id={file_id}"
        gdown.download(url, save_path, quiet=False)
        print(f"✅ 다운로드 완료: {save_path}")
    else:
        print(f"✅ 이미 존재함: {save_path}")

# 모델 다운로드 실행
download_from_gdrive(best_pt_id, model_path)
download_from_gdrive(best2_pt_id, mic_model_path)

# ✅ YOLOv5 모델 로드 (torch.hub.load 사용)
model = torch.hub.load("ultralytics/yolov5", "custom", path=model_path, force_reload=True)
mic_model = torch.hub.load("ultralytics/yolov5", "custom", path=mic_model_path, force_reload=True)

print("✅ 모델 로드 성공!")


@app.route('/ocr', methods=['POST'])
def ocr_endpoint():
    """
    이미지에서 텍스트 추출 및 영수증 여부 판단
    """
    if 'image' not in request.files:
        return jsonify({"error": "이미지 파일이 제공되지 않았습니다."}), 400

    image_file = request.files['image']
    image_content = base64.b64encode(image_file.read()).decode("utf-8")

    try:
        extracted_text = detect_text_with_api_key(image_content)
        if extracted_text:
            is_receipt_flag = is_receipt(extracted_text)
            return jsonify({
                "is_receipt": is_receipt_flag,
                "extracted_text": extracted_text
            })
        else:
            return jsonify({"is_receipt": False, "message": "텍스트를 감지하지 못했습니다."})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route('/movie', methods=['POST'])
def movie_endpoint():
    """
    이미지에서 텍스트 추출 및 영화입장권 여부 판단
    """
    if 'image' not in request.files:
        return jsonify({"error": "이미지 파일이 제공되지 않았습니다."}), 400

    image_file = request.files['image']
    image_content = base64.b64encode(image_file.read()).decode("utf-8")

    try:
        extracted_text = detect_text_with_api_key(image_content)
        if extracted_text:
            is_movie_ticket_flag = is_movie_ticket(extracted_text)
            return jsonify({
                "is_movie_ticket": is_movie_ticket_flag,
                "extracted_text": extracted_text
            })
        else:
            return jsonify({"is_movie_ticket": False, "message": "텍스트를 감지하지 못했습니다."})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route('/library', methods=['POST'])
def library_endpoint():
    """
    이미지에서 텍스트 추출 및 도서관 대출확인증 여부 판단
    """
    if 'image' not in request.files:
        return jsonify({"error": "이미지 파일이 제공되지 않았습니다."}), 400

    image_file = request.files['image']
    image_content = base64.b64encode(image_file.read()).decode("utf-8")

    try:
        extracted_text = detect_text_with_api_key(image_content)
        if extracted_text:
            is_library_receipt_flag = is_library_receipt(extracted_text)
            return jsonify({
                "is_library_receipt": is_library_receipt_flag,
                "extracted_text": extracted_text
            })
        else:
            return jsonify({"is_library_receipt": False, "message": "텍스트를 감지하지 못했습니다."})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route('/positive', methods=['POST'])
def positive_endpoint():
    """
    이미지에서 텍스트 추출 및 "나는 잘하고 있어" 여부 판단
    """
    if 'image' not in request.files:
        return jsonify({"error": "이미지 파일이 제공되지 않았습니다."}), 400

    image_file = request.files['image']
    image_content = base64.b64encode(image_file.read()).decode("utf-8")

    try:
        extracted_text = detect_handwritten_text(image_content)
        if extracted_text:
            is_writing_motivation_flag = is_writing_motivation(extracted_text)
            return jsonify({
                "is_writing_motivation": is_writing_motivation_flag,
                "extracted_text": extracted_text
            })
        else:
            return jsonify({"is_writing_motivation": False, "message": "텍스트를 감지하지 못했습니다."})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/sky', methods=['POST'])
def sky_endpoint():
    """
    하늘 사진 여부 판단
    """
    if 'image' not in request.files:
        return jsonify({"error": "이미지 파일이 제공되지 않았습니다."}), 400

    image_file = request.files['image']
    image_content = base64.b64encode(image_file.read()).decode("utf-8")

    result = sky_image(image_content)

    if "error" in result:
        return jsonify(result), 500
    else:
        return jsonify(result)
    
@app.route('/mountain', methods=['POST'])
def mountain_endpoint():
    """
    산 사진 여부 판단
    """
    if 'image' not in request.files:
        return jsonify({"error": "이미지 파일이 제공되지 않았습니다."}), 400

    image_file = request.files['image']
    image_content = base64.b64encode(image_file.read()).decode("utf-8")

    result = mountain_image(image_content)

    if "error" in result:
        return jsonify(result), 500
    else:
        return jsonify(result)
    
@app.route('/egg', methods=['POST'])
def egg_endpoint():
    """
    계란프라이이 사진 여부 판단
    """
    if 'image' not in request.files:
        return jsonify({"error": "이미지 파일이 제공되지 않았습니다."}), 400

    image_file = request.files['image']
    image_content = base64.b64encode(image_file.read()).decode("utf-8")

    result = fried_egg_image(image_content)

    if "error" in result:
        return jsonify(result), 500
    else:
        return jsonify(result)

@app.route('/paper', methods=['POST'])
def detect_paper():
    """
    업로드된 이미지에서 'paper' 라벨이 감지되었는지 여부를 반환 (True/False)
    """
    if 'image' not in request.files:
        return jsonify({"error": "이미지 파일이 제공되지 않았습니다."}), 400

    image_file = request.files['image']
    image = Image.open(io.BytesIO(image_file.read()))  # PIL 이미지 변환

    # YOLO 모델 실행
    results = model(image)

    # YOLO 결과 변환
    detections = results.pandas().xyxy[0].to_dict(orient="records")

    # 신뢰도(유사도) 기준 설정
    confidence_threshold = 0.8
    filtered_detections = [d for d in detections if d.get("confidence", 0) >= confidence_threshold]

    # 'paper' 라벨이 감지되었는지 확인 (신뢰도 조건을 만족하는 것만 확인)
    paper_detected = any(d.get("name") == "paper" for d in filtered_detections)

    # True/False만 반환
    return jsonify({"paper_detected": paper_detected})

@app.route('/microphone', methods=['POST'])
def detect_microphone():
    """
    업로드된 이미지에서 'microphone' 라벨이 감지되었는지 여부를 반환 (True/False)
    """
    if 'image' not in request.files:
        return jsonify({"error": "이미지 파일이 제공되지 않았습니다."}), 400

    image_file = request.files['image']
    image = Image.open(io.BytesIO(image_file.read()))  # PIL 이미지 변환

    # YOLO 모델 실행
    results = mic_model(image)

    # YOLO 결과 변환
    detections = results.pandas().xyxy[0].to_dict(orient="records")

    # 신뢰도(유사도) 기준 설정
    confidence_threshold = 0.6
    filtered_detections = [d for d in detections if d.get("confidence", 0) >= confidence_threshold]

    # 'paper' 라벨이 감지되었는지 확인 (신뢰도 조건을 만족하는 것만 확인)
    microphone_detected = any(d.get("name") == "microphone" for d in filtered_detections)

    # True/False만 반환
    return jsonify({"microphone_detected": microphone_detected})

    

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)