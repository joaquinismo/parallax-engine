import os
from openai import OpenAI

# API Key desde GitHub Secrets
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Prompt maestro: profesional, detallado y preciso
PROMPT = """
Eres un escritor experto en psicología cognitiva, percepción humana y comportamiento.

Tu tarea es generar guiones para vídeos de TikTok diseñados para:
- Alta retención
- Relecturas
- Watch time superior a 70 segundos
- Monetización por Creator Rewards

REGLAS ESTRICTAS:
- Duración del texto: 120–160 palabras
- Frases cortas (máx 2 líneas en móvil)
- Lenguaje simple pero profundo
- Nada de frases motivacionales genéricas
- Nada de emojis
- Nada de llamadas a la acción
- Nada de vender nada
- Tono reflexivo, serio, casi documental
- Final abierto que invite a pensar

ESTRUCTURA:
1. Frase inicial que genere tensión mental
2. Desarrollo progresivo (no revelar todo de golpe)
3. Idea psicológica real (sesgos, percepción, mente)
4. Cierre en forma de pregunta o reflexión abierta

TEMÁTICAS VÁLIDAS:
- Sesgos cognitivos
- Cómo el cerebro distorsiona la realidad
- Percepción del tiempo
- Identidad y mente
- Pensamiento inconsciente
- Paradojas reales

ENTREGA:
- Solo el texto del guion
- Sin títulos
- Sin explicaciones
"""

def generate_script():
    response = client.responses.create(
        model="gpt-5",
        input=PROMPT
    )
    return response.output_text

if __name__ == "__main__":
    script_text = generate_script()
    os.makedirs("output", exist_ok=True)
    script_path = "output/script.txt"
    with open(script_path, "w", encoding="utf-8") as f:
        f.write(script_text)
    print(f"[INFO] Script generado y guardado en {script_path}")
