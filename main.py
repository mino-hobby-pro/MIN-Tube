from flask import Flask, request, jsonify, send_file, redirect, make_response
import requests
from bs4 import BeautifulSoup
import os
import random
import urllib.parse
import ast
import json
import datetime
import time

app = Flask(__name__)

class InvidiousAPI:
    def __init__(self):
        self.all = ast.literal_eval(requests.get('https://raw.githubusercontent.com/LunaKamituki/yukiyoutube-inv-instances/main/main.txt').text)
        self.video = self.all['video']

invidious_api = InvidiousAPI()

def getRandomUserAgent():
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
        "Mozilla/5.0 (Linux; Android 10; Pixel 3 XL) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Mobile Safari/537.36"
    ]
    return random.choice(user_agents)

def is_authenticated():
    return 'authenticated' in request.cookies and request.cookies['authenticated'] == 'true'

@app.route('/api/fetch', methods=['GET'])
def fetch_html():
    if not is_authenticated():
        return redirect('/nocookie')
    
    video_id = request.args.get('video_id')
    if not video_id:
        return jsonify({'error': 'ビデオIDパラメータが必要です'}), 400

    url = f'https://inv.zzls.xyz/watch?v={video_id}'
    try:
        response = requests.get(url, headers={'User-Agent': getRandomUserAgent()})
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        title = soup.find('meta', property='og:title')['content']
        description = soup.find('meta', property='og:description')['content']
        thumbnail = soup.find('meta', property='og:image')['content']
        view_count = soup.find('p', id='views').text.strip()
        stream_url = soup.find('meta', property='og:video')['content']
        
        if stream_url.startswith('/videoplayback'):
            host = stream_url.split('&host=')[-1]
            stream_url = f'https://{host}{stream_url.split("&host=")[0]}'

        video_data = {
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'view_count': view_count,
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
                if 'application/json' in res.headers.get('Content-Type'):
                    data = res.json()
                    return jsonify({
                        'title': data['title'],
                        'description': data['descriptionHtml'],
                        'thumbnail': data['thumbnail'],
                        'view_count': data['viewCount'],
                        'stream_url': data['formatStreams'][0]['url']
                    })
                else:
                    continue  # JSON以外のレスポンスの場合、次のAPIに進む
        except Exception as e:
            continue
    return jsonify({'error': '代替APIからの情報取得に失敗しました。'}), 500

@app.route('/api/get_stream', methods=['GET'])
def get_stream():
    if not is_authenticated():
        return redirect('/nocookie')

    video_id = request.args.get('video_id')
    if not video_id:
        return jsonify({'error': 'ビデオIDパラメータが必要です'}), 400

    url = f'https://inv.zzls.xyz/watch?v={video_id}'
    try:
        response = requests.get(url, headers={'User-Agent': getRandomUserAgent()})
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        stream_url = soup.find('meta', property='og:video')['content']
        
        if stream_url.startswith('/videoplayback'):
            host = stream_url.split('&host=')[-1]
            stream_url = f'https://{host}{stream_url.split("&host=")[0]}'

        return jsonify({'stream_url': stream_url})
    except Exception as e:
        return jsonify({'error': 'ストリームURLの取得に失敗しました。'}), 500

@app.route('/api/search', methods=['GET'])
def search():
    if not is_authenticated():
        return redirect('/nocookie')

    query = request.args.get('q')
    if not query:
        return jsonify({'error': '検索クエリが必要です'}), 400

    results = get_search(query, 1)  # 1ページ目を取得
    return jsonify({'results': results})

def get_search(q, page):
    results = []

    api_urls = [
        "https://invidious.jing.rocks/",
        "https://invidious.nerdvpn.de/",
        "https://inv.nadeko.net/",
        "https://inv.zzls.xyz/"
    ]

    for api_url in api_urls:
        try:
            response = requests.get(f"{api_url}api/v1/search?q={urllib.parse.quote(q)}&page={page}&hl=jp", headers={'User-Agent': getRandomUserAgent()})
            response.raise_for_status()
            try:
                t = response.json()
            except json.JSONDecodeError:
                continue  # JSONデコードエラーが発生した場合、次のAPIに進む
            
            for i in t:
                if i["type"] == "video":
                    results.append({
                        "title": i["title"],
                        "id": i["videoId"],
                        "authorId": i["authorId"],
                        "author": i["author"],
                        "length": str(datetime.timedelta(seconds=i["lengthSeconds"])),
                        "published": i["publishedText"],
                        "type": "video"
                    })
                elif i["type"] == "playlist":
                    results.append({
                        "title": i["title"],
                        "id": i["playlistId"],
                        "thumbnail": i["videos"][0]["videoId"],
                        "count": i["videoCount"],
                        "type": "playlist"
                    })
                else:
                    thumbnail_url = i["authorThumbnails"][-1]["url"]
                    if not thumbnail_url.startswith("https"):
                        thumbnail_url = "https://" + thumbnail_url
                    results.append({
                        "author": i["author"],
                        "id": i["authorId"],
                        "thumbnail": thumbnail_url,
                        "type": "channel"
                    })
            return results
        except requests.exceptions.RequestException:
            continue

    return []

@app.route('/nocookie')
def nocookie():
    return send_file('nocookie.html')

@app.route('/set_cookie')
def set_cookie():
    resp = make_response(redirect('/'))
    resp.set_cookie('authenticated', 'true')
    return resp

@app.route('/')
def index():
    if not is_authenticated():
        return redirect('/nocookie')
    return send_file('index.html')

@app.route('/player/<video_id>')
def player(video_id):
    if not is_authenticated():
        return redirect('/nocookie')
    return send_file('player.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
