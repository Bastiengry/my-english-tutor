import streamlit as st
from streamlit_mic_recorder import mic_recorder
from groq import Groq

# Configuration de la page
st.set_page_config(page_title="AI English Tutor", page_icon="🇬🇧")
st.title("My English tutor")

# Initialisation de Groq
client = Groq(api_key="TON_API_KEY_ICI")

# Historique de la conversation
if "messages" not in st.session_state:
    st.session_state.messages = []

# Affichage des messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

st.write("---")
st.write("Click on the microphone to start to speak:")

# Bouton d'enregistrement
audio = mic_recorder(start_prompt="🎤 Start to speak", stop_prompt="🛑 Stop", key='recorder')

if audio:
    # Le texte transcrit apparaît ici (Streamlit-mic-recorder utilise le STT du navigateur)
    user_text = audio['transcript'] 
    
    if user_text:
        # 1. Afficher le message utilisateur
        st.session_state.messages.append({"role": "user", "content": user_text})
        with st.chat_message("user"):
            st.markdown(user_text)

        # 2. Envoyer à Llama 3 via Groq
        response = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are a helpful English tutor. Correct grammar mistakes in bold."},
                {"role": "user", "content": user_text}
            ],
            model="llama-3.1-8b-instant",
        )
        answer = response.choices[0].message.content

        # 3. Afficher la réponse du tuteur
        st.session_state.messages.append({"role": "assistant", "content": answer})
        with st.chat_message("assistant"):
            st.markdown(answer)