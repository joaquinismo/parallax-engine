import os
import random
import requests
import json
from pathlib import Path
from moviepy import VideoFileClip, TextClip, CompositeVideoClip, AudioFileClip
import openai

# -----------------------------
# PATHS
# -----------------------------
BASE_DIR = Path(__file__).resolve().parent.parent
ASSETS = BASE_DIR / "assets"
OUTPUT = BASE_DIR / "output"
OUTPUT.mkdir(exist_ok=True)

BG_TEMP = OUTPUT / "bg_temp.mp4"
SCRIPT_FILE = OUTPUT / "script.txt"
OUTPUT_FILE = OUTPUT / "video_final.mp4"
FONT_PATH = ASSETS / "fonts" / "Inter-SemiBold.ttf"
MUSIC_FOLDER = ASSETS / "music"

# -----------------------------
# KEYS
# -----------------------------
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY

# -----------------------------
# CATEGORIAS
# -----------------------------
CATEGORIES = [
    "city",
    "nature",
    "technology",
    "abstract",
    "space"
]

# -----------------------------
# FUNCIONES
# -----------------------------

def download_video(category=None, min_dur=5, max_dur=40):
    """Descarga un vídeo aleatorio de Pexels con fallback seguro"""
    if category is None:
        category = random.choice(CATEGORIES)

    headers = {"Authorization": PEXELS_API_KEY}
    params = {
        "query": category,
        "orientation": "portrait",
        "size": "medium",
        "per_page": 15
    }

    r = requests.get("https://api.pexels.com/videos/search", headers=headers, params=params)
    data = r.json()
    videos = [v for v in data.get("videos", []) if min_dur <= v["duration"] <= max_dur]

    # Fallback si no hay vídeos que cumplan duración
    if not videos:
        print(f"[WARN] No se encontraron vídeos para {category} con duración {min_dur}-{max_dur}s, buscando cualquier vídeo disponible...")
        videos = data.get("videos", [])

    if not videos:
        raise RuntimeError(f"No se encontraron vídeos para ninguna categoría")

    video = random.choice(videos)
    url = video["video_files"][-1]["link"]

    with open(BG_TEMP, "wb") as f:
        f.write(requests.get(url).content)

    print(f"[INFO] Vídeo descargado: categoría={category}, duración={video['duration']}s")
    return category

def choose_music():
    tracks = list(MUSIC_FOLDER.glob("*.mp3"))
    if not tracks:
        raise RuntimeError("No se encontraron pistas de música en assets/music")
    music_file = random.choice(tracks)
    print(f"[INFO] Música seleccionada: {music_file.name}")
    return music_file

def load_script():
    with open(SCRIPT_FILE, encoding="utf-8") as f:
        return [l.strip() for l in f.readlines() if l.strip()]

def render_video():
    category = download_video(random.choice(CATEGORIES))
    music_file = choose_music()
    lines = load_script()

    duration_per_line = 3.5
    total_duration = max(len(lines) * duration_per_line, 10)

    bg = VideoFileClip(str(BG_TEMP))
    if bg.duration < total_duration:
        bg = bg.loop(duration=total_duration)

    bg = bg.subclip(0, total_duration)
    bg = bg.resize(height=1920)
    bg = bg.crop(
        x_center=bg.w / 2,
        y_center=bg.h / 2,
        width=1080,
        height=1920
    )

    audio = AudioFileClip(str(music_file)).subclip(0, total_duration)
    bg = bg.set_audio(audio.volumex(0.45))

    text_clips = []
    for i, line in enumerate(lines):
        txt = TextClip(
            line,
            font=str(FONT_PATH),
            fontsize=72,
            color="white",
            method="caption",
            size=(900, None),
            align="center"
        ).set_start(i * duration_per_line)\
         .set_duration(duration_per_line)\
         .fadein(0.4)\
         .fadeout(0.4)\
         .set_position("center")

        text_clips.append(txt)

    final = CompositeVideoClip([bg, *text_clips])
    final.write_videofile(
        str(OUTPUT_FILE),
        fps=30,
        codec="libx264",
        audio_codec="aac",
        preset="medium",
        threads=4
    )

    metadata = {
        "video": OUTPUT_FILE.name,
        "category": category,
        "music": music_file.name,
        "lines": len(lines)
    }

    return metadata, lines

def save_metadata(meta):
    with open(OUTPUT / "metadata.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=4)
    print(f"[INFO] Metadatos guardados en {OUTPUT / 'metadata.json'}")

def generate_description(script_lines):
    prompt = f"""
    Eres un experto en marketing digital para TikTok.
    Basándote en el siguiente guion, escribe una descripción llamativa y profesional para TikTok:
    Guion:
    {script_lines}

    La descripción debe:
    - Ser corta, directa y atrapar la atención
    - Tener un máximo de 150 caracteres
    - Ser profesional pero atractiva
    - Incluir hashtags universales (máx. 5)
    """

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=60
    )

    description = response.choices[0].message.content.strip()

    with open(OUTPUT / "description.txt", "w", encoding="utf-8") as f:
        f.write(description)

    print(f"[INFO] Descripción generada: {description}")
    return description

# -----------------------------
# MAIN
# -----------------------------
if __name__ == "__main__":
    metadata, lines = render_video()
    description = generate_description(lines)
    metadata["description"] = description
    save_metadata(metadata)
