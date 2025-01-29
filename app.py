from flask import Flask, request, jsonify
import base64
from ocr_utils import detect_text_with_api_key, detect_handwritten_text, is_receipt, is_movie_ticket, is_writing_motivation
from sky_utils import sky_image
from mountain_utils import mountain_image

app = Flask(__name__)

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

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)