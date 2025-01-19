import requests
import isodate

API_KEY = "YOUR_API_KEY"

def search_youtube_videos(keywords):
    query = "+".join(keywords)
    url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&q={query}&type=video&maxResults=10&key={API_KEY}"
    response = requests.get(url).json()
    return response.get("items", [])

def get_video_details(video_id):
    url = f"https://www.googleapis.com/youtube/v3/videos?part=snippet,contentDetails,statistics&id={video_id}&key={API_KEY}"
    response = requests.get(url).json()
    video = response.get("items", [])[0]
    if not video:
        return None
    duration = isodate.parse_duration(video["contentDetails"]["duration"]).total_seconds()
    return {
        "videoId": video_id,
        "title": video["snippet"]["title"],
        "thumbnail": video["snippet"]["thumbnails"]["high"]["url"],
        "duration": duration,
        "totalTime": 0  # Replace with actual value if tracked
    }

def record_watch_time(video_id, watched_time, duration, watch_records):
    if video_id not in watch_records:
        watch_records[video_id] = {"total_time": 0, "duration": duration, "percentage": 0}
    watch_records[video_id]["total_time"] += watched_time
    watch_records[video_id]["percentage"] = (watch_records[video_id]["total_time"] / duration) * 100
    return watch_records[video_id]
