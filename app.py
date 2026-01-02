import streamlit as st
from streamlit_mic_recorder import mic_recorder
from groq import Groq
import tempfile
import hashlib
import os

# Configuration
st.set_page_config(page_title="AI English Tutor", page_icon="🇬🇧")
st.title("My English Tutor")

# Connexion sécurisée à Groq
# Note : Tu devras ajouter ta clé dans les "Secrets" de Streamlit Cloud
if "GROQ_API_KEY" in st.secrets:
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
else:
    st.error("No GROQ_API_KEY set in secrets.")
    st.stop()

# Historique
if "messages" not in st.session_state:
    st.session_state.messages = []
if "last_processed_audio" not in st.session_state:
    st.session_state.last_processed_audio = None
if "last_spoken" not in st.session_state:
    st.session_state.last_spoken = None

# Fonction pour traiter le texte (commune au micro et au clavier)
def process_interaction(text):
    if text and text.strip():
        # Ajouter et afficher message utilisateur
        st.session_state.messages.append({"role": "user", "content": text})
        
        # Appel à Llama 3 avec tout l'historique pour le contexte
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": "You are a helpful English tutor. Correct mistakes in bold and keep the conversation natural."},
                *st.session_state.messages
            ]
        )
        answer = response.choices[0].message.content
        st.session_state.messages.append({"role": "assistant", "content": answer})
        st.rerun()

# Affichage du chat
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Zone d'enregistrement
st.write("---")
col1, col2 = st.columns([1, 4])
with col1:
    # Zone texte audio
    audio = mic_recorder(
        start_prompt="🎤 Press to speak",
        stop_prompt="🛑 Stop listening",
        key='recorder'
    )
with col2:
    # Zone texte écrit
    recording = audio is not None and len(audio.get("bytes", b"")) == 0
    user_input = st.chat_input(
        "Or type your message here...",
        disabled=recording)

# --- LOGIQUE DE TRAITEMENT ---
# A. Si saisie clavier
if user_input:
    process_interaction(user_input)

# B. Si saisie micro
if (audio and isinstance(audio, dict) and "bytes" in audio and len(audio["bytes"]) > 1000):
    # On évite de retraiter le même audio au rechargement
    audio_hash = hashlib.md5(audio["bytes"]).hexdigest()

    if st.session_state.last_processed_audio != audio_hash:
        st.session_state.last_processed_audio = audio_hash
        
        audio_path = None

        try:
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                f.write(audio["bytes"])
                audio_path = f.name

            with open(audio_path, "rb") as file:
                transcription = client.audio.transcriptions.create(
                    file=file,
                    model="whisper-large-v3"
                )
            text = transcription.text.strip()
            if text:
                process_interaction(text)
        finally:
            if os.path.exists(audio_path):
                os.remove(audio_path)

# --- SYNTHÈSE VOCALE (Dernier message de l'IA) ---
if (
    st.session_state.messages
    and st.session_state.messages[-1]["role"] == "assistant"
):
    last_answer = st.session_state.messages[-1]["content"]

    if st.session_state.last_spoken != last_answer:
        st.session_state.last_spoken = last_answer
        
        # NETTOYAGE POUR LA VOIX :
        # 1. On remplace les guillemets pour ne pas casser le JS
        # 2. On supprime les astérisques (*) utilisés pour l'italique/gras
        # 3. On aplatit les retours à la ligne
        clean_answer = last_answer.replace('"', "'").replace("*", "").replace("\n", " ")

        st.components.v1.html(f"""
            <script>
                var msg = new SpeechSynthesisUtterance("{clean_answer}");
                msg.lang = 'en-US';
                window.speechSynthesis.speak(msg);
            </script>
        """, height=0)
