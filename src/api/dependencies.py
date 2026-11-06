from functools import lru_cache
from typing import Annotated

from fastapi import Depends
from sqlalchemy import Engine

from src.database import dados


@lru_cache
def get_engine() -> Engine:
    """Cria o engine na primeira vez que alguém pedir e reaproveita nas próximas."""
    return dados.create_db_engine()


EngineDep = Annotated[Engine, Depends(get_engine)]
