import os
import random
import requests
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip, AudioFileClip
import json

# -----------------------------
# CONFIGURACIÓN DE BRAND / ASSETS
# -----------------------------
BG_TEMP = "output/bg_temp.mp4"            # Vídeo temporal descargado
SCRIPT_FILE = "output/script.txt"
OUTPUT_FILE = "output/video_final.mp4"
FONT_PATH = "assets/fonts/Inter.ttf"
MUSIC_FOLDER = "assets/music/"
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")  # Debes añadir esto a GitHub Secrets
CATEGORIES = ["city night neon", "abstract particles", "slow nature", "cinematic minimal", "space clouds"]

# -----------------------------
# FUNCIONES AUXILIARES
# -----------------------------

def download_video_from_pexels(category, min_duration=10, max_duration=30):
    """
    Descarga un vídeo aleatorio desde Pexels API según categoría y duración
    """
    headers = {"Authorization": PEXELS_API_KEY}
    params = {
        "query": category,
        "orientation": "portrait",
        "size": "medium",
        "per_page": 15
    }
    response = requests.get("https://api.pexels.com/videos/search", headers=headers, params=params)
    data = response.json()
    
    # Filtrar por duración
    filtered_videos = [v for v in data.get("videos", []) if min_duration <= v['duration'] <= max_duration]
    if not filtered_videos:
        raise Exception(f"No se encontraron vídeos para {category} con duración {min_duration}-{max_duration}s")
    
    video = random.choice(filtered_videos)
    video_url = video['video_files'][-1]['link']  # Elegir la mejor calidad
    r = requests.get(video_url)
    
    with open(BG_TEMP, "wb") as f:
        f.write(r.content)
    return BG_TEMP

def choose_music():
    """
    Selecciona aleatoriamente una pista de la carpeta de música local
    """
    music_files = [os.path.join(MUSIC_FOLDER, f) for f in os.listdir(MUSIC_FOLDER) if f.endswith((".mp3", ".wav"))]
    return random.choice(music_files)

def load_script():
    """
    Lee el guion generado previamente
    """
    with open(SCRIPT_FILE, "r", encoding="utf-8") as f:
        text = f.read().strip()
    # Dividir por líneas para animación progresiva
    lines = [line for line in text.split("\n") if line.strip()]
    return lines

# -----------------------------
# RENDER DEL VÍDEO
# -----------------------------
def render_video():
    # Elegir categoría de fondo aleatoria
    category = random.choice(CATEGORIES)
    print(f"[INFO] Descargando vídeo de Pexels categoría: {category}")
    bg_file = download_video_from_pexels(category)

    # Música
    music_file = choose_music()
    print(f"[INFO] Música elegida: {music_file}")

    # Script
    lines = load_script()
    duration_per_line = 4  # Duración de cada línea en segundos
    total_duration = max(len(lines) * duration_per_line, 10)  # mínimo 10s
    
    # Fondo
    bg_clip = VideoFileClip(bg_file)
    if bg_clip.duration < total_duration:
        # Repetir el clip si es más corto que el total del vídeo
        n_loops = int(total_duration // bg_clip.duration) + 1
        bg_clip = bg_clip.loop(n_loops=n_loops)
    bg_clip = bg_clip.subclip(0, total_duration)
    bg_clip = bg_clip.resize(height=1920).resize(width=1080)

    # Música
    audio_clip = AudioFileClip(music_file).subclip(0, total_duration)
    bg_clip = bg_clip.set_audio(audio_clip.volumex(0.5))  # volumen moderado

    # Texto animado
    clips = []
    for i, line in enumerate(lines):
        txt_clip = TextClip(
            line,
            fontsize=60,
            font=FONT_PATH,
            color="white",
            method="caption",
            size=(1000, None),  # margen lateral
        )
        txt_clip = txt_clip.set_start(i*duration_per_line)\
                           .set_duration(duration_per_line)\
                           .fadein(0.5).fadeout(0.5)\
                           .set_position(("center", "center"))
        clips.append(txt_clip)

    # Composición final
    final = CompositeVideoClip([bg_clip, *clips])
    final.write_videofile(
        OUTPUT_FILE,
        fps=30,
        codec="libx264",
        audio_codec="aac",
        preset="medium",
        threads=4,
        verbose=True
    )

    print(f"[INFO] Vídeo renderizado correctamente: {OUTPUT_FILE}")
    return OUTPUT_FILE

# -----------------------------
# METADATOS / TRAZABILIDAD
# -----------------------------
def save_metadata(video_file, category, music_file):
    metadata = {
        "video_file": os.path.basename(video_file),
        "category": category,
        "music_file": os.path.basename(music_file),
        "duration_lines": len(load_script()),
        "brand": "PARALLAX"
    }
    meta_file = "output/metadata.json"
    with open(meta_file, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=4)
    print(f"[INFO] Metadatos guardados en: {meta_file}")

# -----------------------------
# EJECUCIÓN PRINCIPAL
# -----------------------------
if __name__ == "__main__":
    final_video = render_video()
    save_metadata(final_video, category, music_file)
