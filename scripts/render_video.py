import os
import random
import requests
import json
from pathlib import Path
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip, AudioFileClip
import openai

# -----------------------------
# PATHS Y CONFIG
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

PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")       # Añadir a GitHub Secrets
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")       # Añadir a GitHub Secrets
openai.api_key = OPENAI_API_KEY

CATEGORIES = [
    "city night neon",
    "abstract particles",
    "cinematic minimal",
    "space clouds",
    "slow motion nature"
]

# -----------------------------
# FUNCIONES
# -----------------------------
def download_video(category, min_dur=10, max_dur=30):
    """
    Descarga un vídeo aleatorio de Pexels según categoría y duración
    """
    headers = {"Authorization": PEXELS_API_KEY}
    params = {
        "query": category,
        "orientation": "portrait",
        "size": "medium",
        "per_page": 15
    }

    r = requests.get(
        "https://api.pexels.com/videos/search",
        headers=headers,
        params=params
    ).json()

    videos = [
        v for v in r.get("videos", [])
        if min_dur <= v["duration"] <= max_dur
    ]

    if not videos:
        raise RuntimeError(f"No se encontraron vídeos para la categoría {category}")

    video = random.choice(videos)
    url = video["video_files"][-1]["link"]

    with open(BG_TEMP, "wb") as f:
        f.write(requests.get(url).content)

    return category

def choose_music():
    """
    Selecciona aleatoriamente un audio de la carpeta de música
    """
    tracks = list(MUSIC_FOLDER.glob("*.mp3"))
    if not tracks:
        raise RuntimeError("No hay archivos de música en la carpeta assets/music/")
    return random.choice(tracks)

def load_script():
    """
    Lee el guion desde script.txt
    """
    with open(SCRIPT_FILE, encoding="utf-8") as f:
        return [l.strip() for l in f.readlines() if l.strip()]

def render_video():
    """
    Renderiza el vídeo completo con fondo, música y textos animados
    """
    category = download_video(random.choice(CATEGORIES))
    music_file = choose_music()
    lines = load_script()

    duration_per_line = 3.5
    total_duration = max(len(lines) * duration_per_line, 10)

    # --- Fondo ---
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

    # --- Música ---
    audio = AudioFileClip(str(music_file)).subclip(0, total_duration)
    bg = bg.set_audio(audio.volumex(0.45))

    # --- Texto animado ---
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

    return {
        "video": OUTPUT_FILE.name,
        "category": category,
        "music": music_file.name,
        "lines": len(lines),
        "script_lines": lines
    }

# -----------------------------
# METADATA
# -----------------------------
def save_metadata(meta):
    with open(OUTPUT / "metadata.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=4)
    print(f"[INFO] Metadata guardada en {OUTPUT / 'metadata.json'}")

# -----------------------------
# DESCRIPCION
# -----------------------------
def generate_description(script_lines):
    """
    Genera una descripción profesional para TikTok basada en el guion
    """
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
        max_tokens=80
    )

    description = response.choices[0].message.content.strip()

    # Guardar en archivo
    with open(OUTPUT / "description.txt", "w", encoding="utf-8") as f:
        f.write(description)

    print(f"[INFO] Descripción generada: {description}")
    return description

# -----------------------------
# MAIN
# -----------------------------
if __name__ == "__main__":
    metadata = render_video()
    save_metadata(metadata)

    description = generate_description(metadata["script_lines"])
    metadata["description"] = description
    save_metadata(metadata)
