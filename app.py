from flask import Flask, request, jsonify
from flask_cors import CORS
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound
from urllib.parse import urlparse, parse_qs
from bs4 import BeautifulSoup
import requests
import datetime

app = Flask(__name__)
CORS(app)

def extract_video_id(url):
    if 'youtu.be' in url:
        return urlparse(url).path[1:]
    if 'youtube.com' in url:
        query = parse_qs(urlparse(url).query)
        return query.get('v', [None])[0]
    return None

def format_timestamp(seconds):
    return str(datetime.timedelta(seconds=int(seconds)))

def get_video_title(url):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        res = requests.get(url, headers=headers)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, 'html.parser')
        title_tag = soup.find('meta', property='og:title')
        return title_tag['content'] if title_tag else "제목 없음"
    except:
        return "제목 불러오기 실패"


@app.route('/get_subtitle', methods=['GET'])
def get_subtitle():
    url = request.args.get('url')
    if not url:
        return jsonify({"error": "URL이 필요합니다"}), 400

    video_id = extract_video_id(url)
    if not video_id:
        return jsonify({"error": "유효하지 않은 유튜브 링크입니다"}), 400

    title = get_video_title(url)

    try:
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        try:
            transcript = transcript_list.find_transcript(['ko'])
        except NoTranscriptFound:
            transcript = transcript_list.find_transcript(['en'])

        entries = transcript.fetch()
        result = [
            {"time": format_timestamp(entry.start), "text": entry.text}
            for entry in entries
        ]

        return jsonify({
            "title": title,
            "video_id": video_id,
            "url": url,
            "subtitles": result
        })

    except TranscriptsDisabled:
        return jsonify({"error": "이 영상은 자막이 비활성화되어 있습니다"}), 403
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

