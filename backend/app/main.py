"""
Entry point da aplicação FastAPI — Secretaria Virtual FAMED/UFPA.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import chat, feedback

app = FastAPI(
    title="Secretaria Virtual FAMED/UFPA",
    description="API da Secretaria Virtual — Protótipo Piloto: Calendário Acadêmico 2026",
    version="0.1.0",
)

# ---------------------------------------------------------------------------
# CORS — permite requisições do frontend React em desenvolvimento
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permite requisições de localhost e de dispositivos na rede local (celular)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------
app.include_router(chat.router)
app.include_router(feedback.router)


@app.get("/", tags=["health"])
async def root():
    return {
        "status": "ok",
        "service": "Secretaria Virtual FAMED/UFPA",
        "version": "0.1.0",
    }


@app.get("/health", tags=["health"])
async def health():
    return {"status": "ok"}
