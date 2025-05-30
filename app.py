import streamlit as st
from pytube import YouTube
from youtube_transcript_api import YouTubeTranscriptApi
from urllib.parse import urlparse, parse_qs
import requests
import re
import os

st.set_page_config(page_title="YouTube Milionário", page_icon="📈", layout="wide")

st.markdown("""
<style>
    body { background-color: #f5faff; }
    .main { background-color: #ffffff; padding: 2rem; border-radius: 12px; box-shadow: 0px 2px 10px rgba(0,0,0,0.05); }
    h1, h2, h3, h4 { color: #004aad; }
    .stButton>button { background-color: #004aad; color: white; border-radius: 8px; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

st.title("📈 YouTube Milionário")
st.markdown("Descubra como criar vídeos que viralizam no YouTube com ajuda da inteligência artificial.")

def extract_video_id(url):
    parsed_url = urlparse(url)
    if parsed_url.hostname == "youtu.be":
        return parsed_url.path[1:]
    if parsed_url.hostname in ["www.youtube.com", "youtube.com"]:
        query = parse_qs(parsed_url.query)
        return query.get("v", [""])[0]
    return ""

def limpar_texto(texto):
    texto_limpo = re.sub(r'[^ -]+', ' ', texto)
    return texto_limpo.strip().replace("\n", " ").replace("\", " ")

def chamar_groq(titulo, transcricao):
    api_key = os.environ.get("GROQ_API_KEY")
    if not transcricao.strip():
        return "⚠️ Este vídeo não possui transcrição."

    prompt = f"""Você é um especialista em vídeos virais para YouTube.

Com base no título: "{titulo}" e na transcrição resumida abaixo:

{transcricao[:1500]}

1. Explique por que esse vídeo pode ter viralizado.
2. Sugira 10 títulos alternativos.
3. Crie um roteiro completo de até 20 minutos com técnicas de retenção.
4. Escreva uma descrição otimizada com CTA.
5. Liste até 20 hashtags relevantes.
6. Crie 20 prompts de imagem para thumbnails (Midjourney/DALL·E).
7. Crie 10 prompts de vídeo (Runway, Kaiber, Pika Labs).
"""

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    data = {
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "user", "content": prompt}]
    }
    response = requests.post(url, headers=headers, json=data)
    try:
        return response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return f"❌ Erro da IA: {response.text}"

def analisar_video(url):
    video_id = extract_video_id(url)
    yt = YouTube(url)
    try:
        transcript_data = YouTubeTranscriptApi.get_transcript(video_id)
        transcript = " ".join([seg['text'] for seg in transcript_data])
        transcript = limpar_texto(transcript)
        transcricao = transcript[:2000] + "..." if len(transcript) > 2000 else transcript
    except:
        transcricao = "Transcrição não disponível."
        transcript = ""

    resposta_ia = chamar_groq(yt.title, transcript)
    return {
        "Título": yt.title,
        "Canal": yt.author,
        "Publicado em": yt.publish_date.strftime('%d/%m/%Y'),
        "Duração (segundos)": yt.length,
        "Visualizações": yt.views,
        "Descrição (início)": yt.description[:300] + "...",
        "Transcrição": transcricao,
        "Resultado da IA": resposta_ia
    }

url = st.text_input("🔗 Link do vídeo do YouTube:")

if url:
    with st.spinner("🔍 Analisando vídeo com IA..."):
        try:
            resultado = analisar_video(url)
            st.subheader("📋 Informações do Vídeo")
            for chave in ["Título", "Canal", "Publicado em", "Duração (segundos)", "Visualizações"]:
                st.write(f"**{chave}:** {resultado[chave]}")
            st.subheader("📄 Transcrição (resumida)")
            st.write(resultado["Transcrição"])
            st.subheader("🤖 Resultado Completo da IA")
            st.markdown(f"<div class='main'>{resultado['Resultado da IA']}</div>", unsafe_allow_html=True)
        except Exception as e:
            st.error(f"❌ Erro: {e}")
