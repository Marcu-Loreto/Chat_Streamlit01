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

# ═══════════════════════════════════════════════════════
# FUNÇÕES RAG - RETRIEVAL AUGMENTED GENERATION
# ═══════════════════════════════════════════════════════

@st.cache_data
def carregar_base_conhecimento(caminho_arquivo="conhecimento/base_conhecimento.txt"):
    """
    Carrega e processa a base de conhecimento de um arquivo .txt
    """
    try:
        Path(caminho_arquivo).parent.mkdir(parents=True, exist_ok=True)
        
        # Se arquivo não existir, cria com conteúdo exemplo
        if not os.path.exists(caminho_arquivo):
            conteudo_exemplo = """STREAMLIT - GUIA DE DESENVOLVIMENTO

1. INSTALAÇÃO E CONFIGURAÇÃO
Para instalar o Streamlit use: pip install streamlit
Para executar uma aplicação: streamlit run app.py
A aplicação roda por padrão na porta 8501

2. COMPONENTES BÁSICOS
st.write() - Exibe texto, markdown, dataframes
st.title() - Título principal da página
st.header() - Cabeçalhos de seção
st.subheader() - Subcabeçalhos
st.text() - Texto simples sem formatação
st.markdown() - Texto com formatação markdown

3. WIDGETS DE ENTRADA
st.text_input() - Campo de texto simples
st.text_area() - Área de texto multilinha
st.number_input() - Entrada numérica
st.slider() - Controle deslizante
st.selectbox() - Lista suspensa
st.multiselect() - Seleção múltipla
st.checkbox() - Caixa de seleção
st.radio() - Botões de opção

4. SESSION STATE
st.session_state permite manter dados entre execuções
Para inicializar: if "chave" not in st.session_state: st.session_state.chave = valor
Para acessar: st.session_state.chave
Para modificar: st.session_state.chave = novo_valor

5. LAYOUTS E ORGANIZAÇÃO
st.sidebar - Barra lateral para controles
st.columns() - Colunas lado a lado
st.container() - Container para agrupar elementos
st.expander() - Seção expansível
st.tabs() - Abas para organizar conteúdo

6. CACHE E PERFORMANCE
@st.cache_data - Para cachear dados (recomendado)
@st.cache_resource - Para recursos como modelos ML
st.rerun() - Reinicia a execução da aplicação

7. CHAT INTERFACE
st.chat_message() - Container para mensagens de chat
st.chat_input() - Input específico para chat
Usar com avatars: st.chat_message("user", avatar="👤")

8. PROBLEMAS COMUNS
Erro de rerrun infinito: evite modificar session_state em loops
Performance lenta: use cache adequadamente
Layout quebrado: organize com containers e colunas

9. DEPLOY
Streamlit Community Cloud - deploy gratuito
Heroku - para aplicações mais robustas
Docker - para containerização
AWS/GCP - para produção escalável

10. BOAS PRÁTICAS
- Use session_state para dados persistentes
- Implemente cache para operações custosas
- Organize código em funções
- Use sidebar para configurações
- Teste responsividade em dispositivos móveis"""
            
            with open(caminho_arquivo, 'w', encoding='utf-8') as f:
                f.write(conteudo_exemplo)
            st.info(f"📚 Base de conhecimento criada em: {caminho_arquivo}")
        
        # Lê e processa o conteúdo
        with open(caminho_arquivo, 'r', encoding='utf-8') as f:
            conteudo = f.read()
        
        # Divide em blocos (parágrafos)
        blocos = [bloco.strip() for bloco in conteudo.split('\n\n') if bloco.strip()]
        
        # Divide em sentenças também
        sentencas = []
        for bloco in blocos:
            # Remove numeração e formatação
            bloco_limpo = re.sub(r'^\d+\.\s*', '', bloco)
            # Divide em sentenças
            sents = [s.strip() for s in bloco_limpo.split('\n') if s.strip()]
            sentencas.extend(sents)
        
        return {
            'blocos': blocos,
            'sentencas': sentencas,
            'texto_completo': conteudo
        }
        
    except Exception as e:
        st.error(f"❌ Erro ao carregar base de conhecimento: {str(e)}")
        return {'blocos': [], 'sentencas': [], 'texto_completo': ''}

def calcular_similaridade(texto1, texto2):
    """Calcula similaridade entre dois textos usando SequenceMatcher"""
    # Converte para minúsculas e remove caracteres especiais
    t1 = re.sub(r'[^\w\s]', '', texto1.lower())
    t2 = re.sub(r'[^\w\s]', '', texto2.lower())
    
    return SequenceMatcher(None, t1, t2).ratio()

def buscar_contexto_relevante(pergunta, base_conhecimento, max_resultados=3):
    """
    Busca os trechos mais relevantes na base de conhecimento
    usando similaridade de texto simples
    """
    if not base_conhecimento['blocos']:
        return "Nenhuma informação disponível na base de conhecimento."
    
    resultados = []
    
    # Busca em blocos (parágrafos)
    for bloco in base_conhecimento['blocos']:
        similaridade = calcular_similaridade(pergunta, bloco)
        if similaridade > 0.1:  # Threshold mínimo
            resultados.append((similaridade, bloco, 'bloco'))
    
    # Busca em sentenças individuais
    for sentenca in base_conhecimento['sentencas']:
        if len(sentenca) > 20:  # Ignora sentenças muito curtas
            similaridade = calcular_similaridade(pergunta, sentenca)
            if similaridade > 0.15:  # Threshold um pouco maior para sentenças
                resultados.append((similaridade, sentenca, 'sentenca'))
    
    # Ordena por similaridade (maior primeiro)
    resultados.sort(key=lambda x: x[0], reverse=True)
    
    # Pega os melhores resultados
    contexto_relevante = []
    for i, (sim, texto, tipo) in enumerate(resultados[:max_resultados]):
        contexto_relevante.append(f"[Relevância: {sim:.2f}] {texto}")
    
    if contexto_relevante:
        return "\n\n".join(contexto_relevante)
    else:
        return "Não foi encontrada informação relevante na base de conhecimento para esta pergunta."
   #++++++++++++++++++++++++++++++++++++++++++++++++++++++
   # Prompt
   #   ++++++++++++++++++++++++++++++++++++++++++++++++
   @st.cache_data
def carregar_prompt_do_arquivo(caminho_arquivo="prompts/prompt_sistema.txt"):
    """Carrega o prompt do sistema de um arquivo externo"""
    try:
        Path(caminho_arquivo).parent.mkdir(parents=True, exist_ok=True)
        
        if not os.path.exists(caminho_arquivo):
            prompt_padrao = """Você é um assistente de suporte técnico especializado em Streamlit e desenvolvimento Python.

Instruções importantes:
- SEMPRE use as informações fornecidas no CONTEXTO para responder
- Se a informação não estiver no contexto, diga que não tem essa informação na base de conhecimento
- Seja preciso e técnico, mas mantenha linguagem clara
- Forneça exemplos de código quando apropriado
- Cite as fontes do contexto quando possível

Formato de resposta:
1. Responda a pergunta usando o CONTEXTO fornecido
2. Se houver código relevante, inclua exemplos
3. Se não houver informação suficiente no contexto, seja honesto sobre isso"""
            
            with open(caminho_arquivo, 'w', encoding='utf-8') as f:
                f.write(prompt_padrao)
        
        with open(caminho_arquivo, 'r', encoding='utf-8') as f:
            prompt = f.read().strip()
            
        return prompt
        
    except Exception as e:
        st.error(f"❌ Erro ao carregar prompt: {str(e)}")
        return "Você é um assistente técnico. Use sempre o contexto fornecido para responder."

@st.cache_data
def carregar_configuracao_json(caminho_arquivo="config/bot_config.json"):
    """Carrega configurações do bot de um arquivo JSON"""
    try:
        Path(caminho_arquivo).parent.mkdir(parents=True, exist_ok=True)
        
        if not os.path.exists(caminho_arquivo):
            config_padrao = {
                "temperatura_padrao": 0.1,  # Mais baixa para RAG
                "max_tokens_padrao": 500,   # Maior para respostas com contexto
                "modelo_padrao": "gpt-4o",
                "max_contexto_rag": 3,
                "threshold_similaridade": 0.15
            }
            
            with open(caminho_arquivo, 'w', encoding='utf-8') as f:
                json.dump(config_padrao, f, indent=2, ensure_ascii=False)
        
        with open(caminho_arquivo, 'r', encoding='utf-8') as f:
            config = json.load(f)
            
        return config
        
    except Exception as e:
        st.error(f"❌ Erro ao carregar configuração: {str(e)}")
        return {"temperatura_padrao": 0.1, "max_tokens_padrao": 500, "modelo_padrao": "gpt-4o"}


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
        messages=st.session_state["lista_mensagens"],
        #prompt = " Voce é um assitente de suporte de uma empresa de software. Responda de forma clara e objetiva.",
        #temperature=0.2,
        #max_tokens=300,
    )

    resposta_ia = resposta.choices[0].message.content

    # Guarda e mostra a resposta da IA
    st.chat_message("assistant").write(resposta_ia)
    st.session_state["lista_mensagens"].append({"role": "assistant", "content": resposta_ia})
