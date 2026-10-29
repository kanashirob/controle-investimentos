"""Carrega os dados e exibe a posição atual dos ativos."""

from backend.analytics.posicao_atual import current_position
from backend.database.dados import (
    create_db_engine,
    load_ativos,
    load_cotacoes,
    load_operacoes,
    load_aportes
)


def main() -> None:
    engine = create_db_engine()
    ativos = load_ativos(engine)
    operacoes = load_operacoes(engine)
    cotacoes = load_cotacoes(engine)
    aportes = load_aportes(engine)

    posicao = current_position(ativos, operacoes, cotacoes)
    print(posicao.to_string(index=False))
    # print(aportes)


if __name__ == "__main__":
    main()
