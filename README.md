# Secretaria Virtual FAMED/UFPA
## Etapa 1 — Calendário Acadêmico 2026 (Protótipo Piloto)

Interface conversacional que responde perguntas sobre o Calendário Acadêmico 2026 da UFPA utilizando RAG (Retrieval-Augmented Generation) com Gemma 3 1B via Ollama.

---

## Pré-requisitos

- Python >= 3.10
- Node.js >= 18
- [Ollama](https://ollama.com/) instalado e em execução

---

## 1. Configurar o Ollama

`ash
# Instalar o modelo Gemma 3 1B
ollama pull gemma3:1b

# Verificar se está rodando
ollama list
`

---

## 2. Backend (FastAPI + RAG)

### Criar ambiente virtual e instalar dependências

`ash
cd backend
python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux/Mac
source .venv/bin/activate

pip install -r requirements.txt
`

### Copiar e configurar o .env

`ash
# O arquivo .env já está criado com as configurações padrão.
# Edite se necessário (ex: trocar porta do Ollama).
`

### Indexar o PDF (execute uma única vez)

`ash
# Ainda dentro de backend/, com o .venv ativado:
python -m app.rag.vectorstore
`

Este comando processa o PDF data/Calendario_Academico_da_UFPA_2026.pdf,
gera os embeddings e salva o banco vetorial em chroma_db/.

> Tempo estimado: 1–3 minutos (download do modelo de embeddings na primeira execução).

### Iniciar o servidor

`ash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
`

A API estará disponível em:
- http://localhost:8000 — health check
- http://localhost:8000/docs — Swagger UI (teste os endpoints)

---

## 3. Frontend (React + Vite)

`ash
cd frontend
npm install
npm run dev
`

O frontend estará disponível em http://localhost:5173

---

## 4. Testar

1. Acesse http://localhost:5173
2. Clique no ícone de chat no canto inferior direito
3. Faça perguntas sobre o Calendário Acadêmico 2026:
   - *"Quando começa o semestre letivo de 2026?"*
   - *"Quais são os feriados acadêmicos?"*
   - *"Quando é o período de matrícula?"*

---

## Estrutura do projeto

`
Secretaria-Virtual-FAMED/
├── backend/
│   ├── app/
│   │   ├── main.py              # Entry point FastAPI
│   │   ├── config.py            # Configurações via .env
│   │   ├── routers/
│   │   │   └── chat.py          # POST /chat
│   │   └── rag/
│   │       ├── loader.py        # Carrega e chunka o PDF
│   │       ├── embeddings.py    # Modelo de embeddings
│   │       ├── vectorstore.py   # ChromaDB
│   │       └── chain.py         # RAG chain (LangChain + Ollama)
│   ├── data/
│   │   └── Calendario_Academico_da_UFPA_2026.pdf
│   ├── chroma_db/               # Banco vetorial (gerado após indexação)
│   ├── requirements.txt
│   ├── .env
│   └── .env.example
│
├── frontend/
│   ├── src/
│   │   ├── App.jsx              # Página principal
│   │   ├── App.css
│   │   ├── main.jsx
│   │   ├── index.css
│   │   └── components/
│   │       ├── ChatWidget.jsx   # Ícone flutuante + toggle
│   │       ├── ChatWidget.css
│   │       ├── ChatWindow.jsx   # Janela de chat
│   │       ├── ChatWindow.css
│   │       ├── MessageBubble.jsx
│   │       ├── MessageBubble.css
│   │       ├── ChatInput.jsx
│   │       └── ChatInput.css
│   ├── index.html
│   ├── package.json
│   └── vite.config.js
│
└── README.md
`

---

## Atualizar o documento

Para substituir o PDF do calendário por uma versão mais recente:

1. Substitua o arquivo em ackend/data/.
2. Delete a pasta ackend/chroma_db/.
3. Execute novamente: python -m app.rag.vectorstore
4. Reinicie o servidor.
