from functools import lru_cache
from typing import Annotated
from fastapi import Depends
from sqlalchemy import Engine
from src.database import dados
from dataclasses import dataclass

import pandas as pd


@lru_cache
def get_engine() -> Engine:
    """Cria o engine na primeira vez que alguém pedir e reaproveita nas próximas."""
    return dados.create_db_engine()


EngineDep = Annotated[Engine, Depends(get_engine)]


@dataclass
class Dados:
    """Classe para carregar as tabelas do banco de dados necessárias para os endpoints da API."""
    ativos: pd.DataFrame
    operacoes: pd.DataFrame
    cotacoes: pd.DataFrame


def get_dados(engine: EngineDep) -> Dados:
    return Dados(
        ativos=dados.load_ativos(engine),
        operacoes=dados.load_operacoes(engine),
        cotacoes=dados.load_cotacoes(engine)
    )


DadosDep = Annotated[Dados, Depends(get_dados)]
