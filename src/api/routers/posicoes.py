from fastapi import APIRouter
from src.utils import dataframe_to_json
from src.database import dados
from src.api.dependencies import EngineDep
from src.analytics import posicoes


router = APIRouter(prefix="/posicoes", tags=["Posições"])


@router.get("/atual")
def posicao_atual(engine: EngineDep):
    ativos = dados.load_ativos(engine)
    operacoes = dados.load_operacoes(engine)
    cotacoes = dados.load_cotacoes(engine)
    posicao = posicoes.current_position(ativos, operacoes, cotacoes)
    return dataframe_to_json.dataframe_to_json(posicao)


@router.get("/mensal")
def posicao_mensal(engine: EngineDep):
    ativos = dados.load_ativos(engine)
    operacoes = dados.load_operacoes(engine)
    cotacoes = dados.load_cotacoes(engine)
    posicao = posicoes.monthly_position(ativos, operacoes, cotacoes)
    return dataframe_to_json.dataframe_to_json(posicao)
