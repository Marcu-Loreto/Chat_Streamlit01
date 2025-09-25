import os
import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI

# Carrega variáveis do 
load_dotenv()

#Para rodar o sistema: streamlit run bot.py

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

# Função para incluir system message
def obter_mensagens_com_sistema():
    system_message = {
        "role": "system", 
        "content": "Você é um assistente de suporte de uma empresa de software. Responda de forma clara, objetiva e profissional. Seja prestativo e técnico quando necessário."
    }
    return [system_message] + st.session_state["lista_mensagens"]

# Exibe histórico
for msg in st.session_state["lista_mensagens"]:
    st.chat_message(msg["role"]).write(msg["content"])

# Entrada do usuário
mensagem_usuario = st.chat_input("Escreva sua mensagem aqui")

if mensagem_usuario:
    # Guarda e mostra a mensagem do usuário
    st.session_state["lista_mensagens"].append({"role": "user", "content": mensagem_usuario})
    st.chat_message("user").write(mensagem_usuario)

    # Chamada ao modelo COM system message
    resposta = client.chat.completions.create(
        model="gpt-4o",
        messages=obter_mensagens_com_sistema(),  # ← AQUI USA O SYSTEM MESSAGE
        temperature=0.2,
        max_tokens=300,
    )

    resposta_ia = resposta.choices[0].message.content

    # Guarda e mostra a resposta da IA
    st.chat_message("assistant").write(resposta_ia)
    st.session_state["lista_mensagens"].append({"role": "assistant", "content": resposta_ia})