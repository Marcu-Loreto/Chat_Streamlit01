import os
import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI
import json
from pathlib import Path

# Carrega variáveis do .env
load_dotenv()

# Para rodar o sistema: streamlit run bot.py

# ═══════════════════════════════════════════════════════
# FUNÇÃO PARA CARREGAR PROMPTS DE ARQUIVOS EXTERNOS
# ═══════════════════════════════════════════════════════

@st.cache_data
def carregar_prompt_do_arquivo(caminho_arquivo="prompt.txt"):
    """
    Carrega o prompt do sistema de um arquivo externo
    Cria o arquivo com prompt padrão se não existir
    """
    try:
        # Cria diretório se não existir
        Path(caminho_arquivo).parent.mkdir(parents=True, exist_ok=True)
        
        # Se arquivo não existir, cria com prompt padrão
        if not os.path.exists(caminho_arquivo):
            prompt_padrao = """Você é um assistente de suporte técnico especializado em desenvolvimento de software, Python e Streamlit.

Características:
- Responda de forma clara, objetiva e profissional
- Forneça soluções práticas e código quando apropriado  
- Seja prestativo e paciente
- Use exemplos quando necessário
- Mantenha um tom amigável mas técnico

Instruções específicas:
- Sempre teste suas sugestões de código
- Explique o "porquê" das suas recomendações
- Se não souber algo, admita e sugira onde buscar
- Priorize boas práticas de desenvolvimento"""
            
            with open(caminho_arquivo, 'w', encoding='utf-8') as f:
                f.write(prompt_padrao)
            st.info(f"📄 Arquivo de prompt criado em: {caminho_arquivo}")
        
        # Lê o conteúdo do arquivo
        with open(caminho_arquivo, 'r', encoding='utf-8') as f:
            prompt = f.read().strip()
            
        return prompt
        
    except Exception as e:
        st.error(f"❌ Erro ao carregar prompt: {str(e)}")
        # Retorna prompt básico como fallback
        return "Você é um assistente de suporte técnico. Responda de forma clara e objetiva."

@st.cache_data
def carregar_configuracao_json(caminho_arquivo="config/bot_config.json"):
    """
    Carrega configurações do bot de um arquivo JSON
    """
    try:
        Path(caminho_arquivo).parent.mkdir(parents=True, exist_ok=True)
        
        if not os.path.exists(caminho_arquivo):
            config_padrao = {
                "temperatura_padrao": 0.2,
                "max_tokens_padrao": 400,
                "modelo_padrao": "gpt-5-nano",
                "prompts_disponiveis": {
                    "suporte_tecnico": "prompts/prompt_suporte.txt",
                    "assistente_comercial": "prompts/prompt_comercial.txt",
                    "mentor_codigo": "prompts/prompt_mentor.txt"
                }
            }
            
            with open(caminho_arquivo, 'w', encoding='utf-8') as f:
                json.dump(config_padrao, f, indent=2, ensure_ascii=False)
            st.info(f"⚙️ Arquivo de configuração criado em: {caminho_arquivo}")
        
        with open(caminho_arquivo, 'r', encoding='utf-8') as f:
            config = json.load(f)
            
        return config
        
    except Exception as e:
        st.error(f"❌ Erro ao carregar configuração: {str(e)}")
        return {"temperatura_padrao": 0.2, "max_tokens_padrao": 400, "modelo_padrao": "gpt-4o"}

# ═══════════════════════════════════════════════════════
# VALIDAÇÃO E CONFIGURAÇÃO INICIAL
# ═══════════════════════════════════════════════════════

# Valida a API key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    st.error("OPENAI_API_KEY não encontrada. Crie um arquivo .env com OPENAI_API_KEY=suachave")
    st.stop()

# Instancia o cliente
client = OpenAI(api_key=OPENAI_API_KEY)

# Configuração da página
st.set_page_config(
    page_title="ChatBot IA - Suporte",
    page_icon="🤖",
    layout="wide"
)

# Carrega configurações e prompts
config = carregar_configuracao_json()
prompt_sistema_arquivo = carregar_prompt_do_arquivo()

# Título principal
st.write("## 🤖 ChatBot com IA - Suporte Técnico")

# ═══════════════════════════════════════════════════════
# SIDEBAR - CONFIGURAÇÕES
# ═══════════════════════════════════════════════════════

st.sidebar.write("### ⚙️ Configurações do Bot")

# Seletor de tipo de prompt
tipo_prompt = st.sidebar.selectbox(
    "🎭 Tipo de Assistente:",
    ["Arquivo Personalizado", "Suporte Técnico", "Comercial", "Mentor de Código"],
    help="Escolha o comportamento do assistente"
)

# Carrega prompt baseado na seleção
if tipo_prompt == "Arquivo Personalizado":
    prompt_sistema = prompt_sistema_arquivo
    st.sidebar.info("📄 Usando prompt de: prompts/prompt_sistema.txt")
elif tipo_prompt == "Suporte Técnico":
    prompt_sistema = carregar_prompt_do_arquivo("prompts/prompt_suporte.txt")
elif tipo_prompt == "Comercial":
    prompt_sistema = carregar_prompt_do_arquivo("prompts/prompt_comercial.txt")
elif tipo_prompt == "Mentor de Código":
    prompt_sistema = carregar_prompt_do_arquivo("prompts/prompt_mentor.txt")

# Opção para editar prompt inline (sobrescreve arquivo)
editar_prompt = st.sidebar.checkbox("✏️ Editar Prompt", help="Permite editar o prompt atual")

if editar_prompt:
    prompt_editado = st.sidebar.text_area(
        "📝 Prompt do Sistema (editável):",
        value=prompt_sistema,
        height=200,
        help="Suas alterações serão salvas no arquivo"
    )
    
    if st.sidebar.button("💾 Salvar no Arquivo"):
        try:
            arquivo_atual = "prompts/prompt_sistema.txt"
            if tipo_prompt == "Suporte Técnico":
                arquivo_atual = "prompts/prompt_suporte.txt"
            elif tipo_prompt == "Comercial":
                arquivo_atual = "prompts/prompt_comercial.txt"
            elif tipo_prompt == "Mentor de Código":
                arquivo_atual = "prompts/prompt_mentor.txt"
                
            with open(arquivo_atual, 'w', encoding='utf-8') as f:
                f.write(prompt_editado)
            
            st.sidebar.success("✅ Prompt salvo no arquivo!")
            # Limpa cache para recarregar
            st.cache_data.clear()
            st.rerun()
            
        except Exception as e:
            st.sidebar.error(f"❌ Erro ao salvar: {str(e)}")
    
    prompt_sistema = prompt_editado

# Parâmetros do modelo (usando valores do config)
st.sidebar.write("### 🎛️ Parâmetros do Modelo")

temperatura = st.sidebar.slider(
    "🌡️ Temperatura:",
    0.0, 1.0, 
    config.get("temperatura_padrao", 0.2), 
    0.1
)

max_tokens = st.sidebar.number_input(
    "📊 Máximo de Tokens:",
    50, 1000, 
    config.get("max_tokens_padrao", 400), 
    50
)

modelo = st.sidebar.selectbox(
    "🧠 Modelo:",
    ["gpt-4o-mini","gpt-4.1-nano", "gpt-4o", "gpt-3.5-turbo"],
    index=0 if config.get("modelo_padrao") == "gpt-4o" else 0
)

# ═══════════════════════════════════════════════════════
# AÇÕES DA SIDEBAR
# ═══════════════════════════════════════════════════════

st.sidebar.write("### 🛠️ Ações")

col1, col2 = st.sidebar.columns(2)
with col1:
    if st.button("🗑️ Limpar", use_container_width=True):
        st.session_state["lista_mensagens"] = []
        st.rerun()

with col2:
    if st.button("🔄 Recarregar", use_container_width=True):
        st.cache_data.clear()  # Limpa cache dos arquivos
        st.rerun()

# ═══════════════════════════════════════════════════════
# INFORMAÇÕES E STATUS
# ═══════════════════════════════════════════════════════

st.sidebar.write("---")
st.sidebar.write("### 📊 Status")

# Inicializa mensagens
if "lista_mensagens" not in st.session_state:
    st.session_state["lista_mensagens"] = []

total_mensagens = len(st.session_state["lista_mensagens"])
st.sidebar.metric("💬 Mensagens", total_mensagens)

# Mostra arquivo sendo usado
st.sidebar.write("### 📁 Arquivos")
st.sidebar.caption("📄 Prompt: prompts/prompt_sistema.txt")
st.sidebar.caption("⚙️ Config: config/bot_config.json")

# ═══════════════════════════════════════════════════════
# FUNÇÃO PARA INCLUIR SYSTEM MESSAGE
# ═══════════════════════════════════════════════════════

def obter_mensagens_completas():
    """Inclui o system message no início da lista de mensagens"""
    system_msg = {"role": "system", "content": prompt_sistema.strip()}
    return [system_msg] + st.session_state["lista_mensagens"]

# ═══════════════════════════════════════════════════════
# INTERFACE PRINCIPAL DO CHAT
# ═══════════════════════════════════════════════════════

# Exibe histórico
for msg in st.session_state["lista_mensagens"]:
    if msg["role"] == "user":
        st.chat_message("user").write(msg["content"])
    else:
        st.chat_message("assistant").write(msg["content"])

# Entrada do usuário
mensagem_usuario = st.chat_input("💭 Escreva sua mensagem aqui...")

# ═══════════════════════════════════════════════════════
# PROCESSAMENTO DA MENSAGEM
# ═══════════════════════════════════════════════════════

if mensagem_usuario:
    # Adiciona mensagem do usuário
    st.session_state["lista_mensagens"].append({
        "role": "user", 
        "content": mensagem_usuario
    })
    
    # Exibe mensagem do usuário
    st.chat_message("user").write(mensagem_usuario)
    
    # Processa resposta da IA
    with st.chat_message("assistant"): #, avatar="🤖"):
        with st.spinner("🤔 Pensando..."):
            try:
                resposta = client.chat.completions.create(
                    model=modelo,
                    messages=obter_mensagens_completas(),
                    temperature=temperatura,
                    max_tokens=max_tokens,
                    top_p=0.9,
                    frequency_penalty=0.1
                )
                
                resposta_ia = resposta.choices[0].message.content
                st.write(resposta_ia)
                
                # Adiciona ao histórico
                st.session_state["lista_mensagens"].append({
                    "role": "assistant", 
                    "content": resposta_ia
                })
                
            except Exception as e:
                st.error(f"❌ Erro na API: {str(e)}")

# ═══════════════════════════════════════════════════════
# RODAPÉ
# ═══════════════════════════════════════════════════════

#if total_mensagens == 0:
#    st.info(f"👋 Olá! {tipo_prompt} ativo. Como posso ajudá-lo?")

#st.write("---")
#st.caption("📁 Prompts carregados de arquivos externos • 🔧 Configure na barra lateral")