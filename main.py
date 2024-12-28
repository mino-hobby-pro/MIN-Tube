from flask import Flask, request, render_template, jsonify
import requests
from bs4 import BeautifulSoup
import os
import urllib.parse
import random

app = Flask(__name__)

class InvidiousAPI:
    def __init__(self):
        self.all = requests.get('https://raw.githubusercontent.com/LunaKamituki/yukiyoutube-inv-instances/refs/heads/main/main.txt').json()
        self.video = self.all['video']

invidious_api = InvidiousAPI()

def getRandomUserAgent():
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
        "Mozilla/5.0 (Linux; Android 10; Pixel 3 XL) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Mobile Safari/537.36"
    ]
    return random.choice(user_agents)

@app.route('/')
def index():
    return render_template('player.html')

@app.route('/fetch_video', methods=['GET'])
def fetch_video():
    video_id = request.args.get('video_id')
    if not video_id:
        return jsonify({'error': 'ビデオIDパラメータが必要です'}), 400

    url = f'https://inv.zzls.xyz/watch?v={video_id}'
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # 必要な情報を抽出
        title = soup.find('meta', property='og:title')['content']
        thumbnail = soup.find('meta', property='og:image')['content']
        stream_url = soup.find('meta', property='og:video')['content']

        # ストリームURLが指定の形式の場合は修正
        if stream_url.startswith('/videoplayback'):
            host = stream_url.split('&host=')[-1]
            stream_url = f'https://{host}{stream_url.split("&host=")[0]}'

        video_data = {
            'title': title,
            'thumbnail': thumbnail,
            'stream_url': stream_url
        }
        return jsonify(video_data)
    
    except requests.exceptions.RequestException:
        return fetch_from_invidious(video_id)
    except Exception as e:
        return jsonify({'error': '情報の取得に失敗しました。'}), 500

def fetch_from_invidious(video_id):
    api_urls = invidious_api.video
    path = f"/videos/{urllib.parse.quote(video_id)}"
    
    for api in api_urls:
        try:
            res = requests.get(api + path, headers={'User-Agent': getRandomUserAgent()})
            if res.status_code == 200:
                data = res.json()
                return jsonify({
                    'title': data['title'],
                    'thumbnail': data['thumbnail'],
                    'stream_url': data['formatStreams'][0]['url']
                })
        except Exception as e:
            continue

    return jsonify({'error': '代替APIからの情報取得に失敗しました。'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
