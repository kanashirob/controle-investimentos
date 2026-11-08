from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routers import health, posicoes

tags_metadata = [
    {"name": "Saúde", "description": "Verifica se o servidor está funcionando."},
    {"name": "Posições", "description": "Posição atual e evolução mensal da carteira."},
]

app = FastAPI(title="Controle de Investimentos", openapi_tags=tags_metadata)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(posicoes.router)
