import os
import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI

# Carrega variáveis do .env
load_dotenv()

# Valida a API key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    st.error("OPENAI_API_KEY não encontrada. Crie um arquivo .env com OPENAI_API_KEY=suachave")
    st.stop()

# Instancia o cliente usando a chave do ambiente (sem expor no código)
client = OpenAI(api_key=OPENAI_API_KEY)

st.write("## ChatBot com IA - Suporte")

# Memória de conversa
if "lista_mensagens" not in st.session_state:
    st.session_state["lista_mensagens"] = []

# Exibe histórico
for msg in st.session_state["lista_mensagens"]:
    st.chat_message(msg["role"]).write(msg["content"])

# Entrada do usuário
mensagem_usuario = st.chat_input("Escreva sua mensagem aqui")

if mensagem_usuario:
    # Guarda e mostra a mensagem do usuário
    st.session_state["lista_mensagens"].append({"role": "user", "content": mensagem_usuario})
    st.chat_message("user").write(mensagem_usuario)

    # Chamada ao modelo
    resposta = client.chat.completions.create(
        model="gpt-4o",
        messages=st.session_state["lista_mensagens"]
    )

    resposta_ia = resposta.choices[0].message.content

    # Guarda e mostra a resposta da IA
    st.chat_message("assistant").write(resposta_ia)
    st.session_state["lista_mensagens"].append({"role": "assistant", "content": resposta_ia})
