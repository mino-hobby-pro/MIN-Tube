from flask import Flask, render_template, request, jsonify
import requests
from bs4 import BeautifulSoup
import urllib.parse
import random

app = Flask(__name__)

class InvidiousAPI:
    def __init__(self):
        self.all = requests.get('https://raw.githubusercontent.com/LunaKamituki/yukiyoutube-inv-instances/refs/heads/main/main.txt').json()
        self.video = self.all['video']

    def get_video_data(self, video_id):
        api_urls = self.video
        path = f"/videos/{urllib.parse.quote(video_id)}"
        
        for api in api_urls:
            try:
                res = requests.get(api + path)
                if res.status_code == 200:
                    return res.json()
            except Exception:
                continue
        return None

invidious_api = InvidiousAPI()

@app.route('/')
def index():
    return render_template('player.html')

@app.route('/api/fetch', methods=['GET'])
def fetch_video():
    video_id = request.args.get('video_id')
    if not video_id:
        return jsonify({'error': 'ビデオIDパラメータが必要です'}), 400

    video_data = invidious_api.get_video_data(video_id)
    if video_data is None:
        return jsonify({'error': '情報の取得に失敗しました。'}), 500

    return jsonify({
        'title': video_data['title'],
        'description': video_data['descriptionHtml'],
        'thumbnail': video_data['thumbnail'],
        'view_count': video_data['viewCount'],
        'stream_url': video_data['formatStreams'][0]['url']
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
