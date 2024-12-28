from flask import Flask, request, render_template, jsonify
import requests
import urllib.parse
import random

app = Flask(__name__)

API_URL = "https://sure-helsa-mino-hobby-1e3b2fbf.koyeb.app/api/fetch"

def getRandomUserAgent():
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
        "Mozilla/5.0 (Linux; Android 10; Pixel 3 XL) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Mobile Safari/537.36"
    ]
    return random.choice(user_agents)

@app.route('/')
def index():
    video_id = request.args.get('video_id')
    return render_template('player.html', video_id=video_id) if video_id else render_template('player.html')

@app.route('/api/get_video_info', methods=['GET'])
def get_video_info():
    video_id = request.args.get('video_id')
    if not video_id:
        return jsonify({'error': 'ビデオIDパラメータが必要です'}), 400

    try:
        response = requests.get(f"{API_URL}?video_id={video_id}", headers={'User-Agent': getRandomUserAgent()})
        response.raise_for_status()
        return jsonify(response.json())
    except requests.exceptions.RequestException:
        return jsonify({'error': '情報の取得に失敗しました。'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
