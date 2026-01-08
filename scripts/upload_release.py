import os
import requests
import json
from datetime import datetime

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO = os.getenv("GITHUB_REPOSITORY")
VIDEO_PATH = "output/video_final.mp4"

def create_release(tag):
    url = f"https://api.github.com/repos/{REPO}/releases"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json"
    }
    data = {
        "tag_name": tag,
        "name": f"PARALLAX Video {tag}",
        "body": "Vídeo generado automáticamente",
        "draft": False,
        "prerelease": False
    }
    r = requests.post(url, headers=headers, json=data)
    r.raise_for_status()
    return r.json()

def upload_asset(upload_url, file_path):
    upload_url = upload_url.split("{")[0]
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Content-Type": "video/mp4"
    }
    with open(file_path, "rb") as f:
        r = requests.post(
            f"{upload_url}?name=video_final.mp4",
            headers=headers,
            data=f
        )
    r.raise_for_status()
    return r.json()

if __name__ == "__main__":
    tag = datetime.utcnow().strftime("v%Y%m%d%H%M%S")
    release = create_release(tag)
    asset = upload_asset(release["upload_url"], VIDEO_PATH)

    metadata = {
        "release_tag": tag,
        "download_url": asset["browser_download_url"]
    }

    with open("output/metadata.json", "w") as f:
        json.dump(metadata, f, indent=4)

    print("✅ Vídeo subido a GitHub Release")
    print(metadata["download_url"])
