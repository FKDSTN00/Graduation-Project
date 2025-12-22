from flask import Blueprint, request, jsonify
import requests
from flask import current_app

ai_bp = Blueprint('ai', __name__)

@ai_bp.route('/chat', methods=['POST'])
def chat():
    """
    AI 对话接口
    转发请求到本地 AI 服务
    """
    data = request.get_json()
    prompt = data.get('prompt')
    
    # 转发到本地 AI 服务 (Ollama)
    try:
        response = requests.post(
            f"{current_app.config['AI_API_URL']}/chat/completions",
            json={
                "model": current_app.config['AI_MODEL_NAME'],
                "messages": [{"role": "user", "content": prompt}]
            }
        )
        return jsonify(response.json()), response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"AI 服务连接失败: {str(e)}"}), 500
