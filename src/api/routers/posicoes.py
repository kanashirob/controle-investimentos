from fastapi import APIRouter
from utils import dataframe_to_json
from api.dependencies import DadosDep
from analytics import posicoes


router = APIRouter(prefix="/api/posicoes", tags=["Posições"])


@router.get("/atual")
def posicao_atual(dados: DadosDep):
    return dataframe_to_json.dataframe_to_json(posicoes.current_position(dados.ativos, dados.operacoes, dados.cotacoes))


@router.get("/mensal")
def posicao_mensal(dados: DadosDep):
    return dataframe_to_json.dataframe_to_json(posicoes.monthly_position(dados.ativos, dados.operacoes, dados.cotacoes))
