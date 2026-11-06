from fastapi import FastAPI

from api.routers import health, posicoes

tags_metadata = [
    {"name": "Saúde", "description": "Verifica se o servidor está funcionando."},
    {"name": "Posições", "description": "Posição atual e evolução mensal da carteira."},
]

app = FastAPI(title="Controle de Investimentos", openapi_tags=tags_metadata)

app.include_router(health.router)
app.include_router(posicoes.router)
