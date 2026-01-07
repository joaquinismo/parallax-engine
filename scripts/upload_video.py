import os
import boto3
import json

# Configuración Cloudflare R2 (o S3 compatible)
R2_KEY = os.getenv("R2_ACCESS_KEY_ID")
R2_SECRET = os.getenv("R2_SECRET_ACCESS_KEY")
R2_BUCKET = os.getenv("R2_BUCKET_NAME")
R2_ENDPOINT = os.getenv("R2_ENDPOINT")

VIDEO_FILE = "output/video_final.mp4"

def upload_video_to_r2(video_path):
    s3 = boto3.client(
        's3',
        endpoint_url=R2_ENDPOINT,
        aws_access_key_id=R2_KEY,
        aws_secret_access_key=R2_SECRET
    )
    file_name = os.path.basename(video_path)
    s3.upload_file(video_path, R2_BUCKET, file_name)
    url = f"{R2_ENDPOINT}/{R2_BUCKET}/{file_name}"
    return url

def save_metadata(url):
    metadata_path = "output/metadata.json"
    if os.path.exists(metadata_path):
        with open(metadata_path, "r", encoding="utf-8") as f:
            metadata = json.load(f)
    else:
        metadata = {}

    metadata.update({
        "uploaded_url": url
    })

    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=4)
    print(f"[INFO] Metadatos actualizados con URL: {url}")

if __name__ == "__main__":
    if not os.path.exists(VIDEO_FILE):
        raise FileNotFoundError(f"No se encontró el vídeo en {VIDEO_FILE}")
    
    url = upload_video_to_r2(VIDEO_FILE)
    save_metadata(url)
    print(f"[INFO] Vídeo subido correctamente: {url}")
