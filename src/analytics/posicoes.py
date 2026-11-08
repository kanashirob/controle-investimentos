"""Camada de cálcuclo: recebe DataFrames e devolve DataFrames. Não acessa o banco de dados."""

import numpy as np
import pandas as pd


from constants import constants
from utils import dataframe_validation
from analytics import livro_operacoes


def current_position(
        ativos: pd.DataFrame,
        operacoes: pd.DataFrame,
        cotacoes: pd.DataFrame,
        incluir_zerados: bool = False) -> pd.DataFrame:
    """Uma linha por ativo: quantidade, preço médio, valor investido, valor atual e resultado.

    O preço atual é a cotação mais recente de cada ativo. Sem cotação, os campos de valor atual e resultado ficam vazios (NaN) em vez de inventar um número.
    """
    dataframe_validation.validate_required_columns(
        ativos, constants.COLUNAS_ATIVOS, "ativos")
    dataframe_validation.validate_required_columns(
        cotacoes, constants.COLUNAS_COTACOES, "cotacoes")

    colunas_saida = ["ticker",
                     "classe",
                     "quantidade",
                     "preco_medio",
                     "valor_investido",
                     "preco_atual",
                     "data_cotacao",
                     "valor_atual",
                     #  "resultado", # Em avaliação se faz sentido ficar aqui ou na posição mensal
                     #  "resultado_pct", # Em avaliação se faz sentido ficar aqui ou na posição mensal
                     "lucro_realizado"]

    livro = livro_operacoes.build_book(operacoes)
    if livro.empty:
        return pd.DataFrame(columns=colunas_saida)
    # situação de cada ativo depois da última operação
    ultimo = livro.groupby("ativo_id").tail(1).set_index("ativo_id")
    # lucro total realizado por ativo
    lucro = livro.groupby("ativo_id")["lucro_realizado"].sum()
    # ordena as cotacoes por ativo e data, mantendo a ordem original em caso de empate
    cot = cotacoes.sort_values(["ativo_id", "data"], kind="stable")
    # cotação mais recente de cada ativo com a respectiva data
    preco_atual = cot.groupby("ativo_id")[["preco_fechamento", "data"]].last()
    # Une as informações de ativos, quantidade atual, valor investido e preço médio
    df = ativos.set_index("ativo_id")[["ticker", "classe"]].join(
        ultimo[[
            "quantidade_apos",
            "custo_total_apos",
            "preco_medio_apos",
        ]],
        how="inner",
    )
    df = df.rename(columns={
        "quantidade_apos": "quantidade",
        "custo_total_apos": "valor_investido",
        "preco_medio_apos": "preco_medio",
    })
    # preco atual do ativo, se houver cotação
    df["preco_atual"] = preco_atual["preco_fechamento"].reindex(df.index)
    # data da cotação mais recente do ativo, se houver cotação
    df["data_cotacao"] = preco_atual["data"].reindex(df.index)
    # valor atual do ativo, se houver cotação
    df["valor_atual"] = df["quantidade"] * df["preco_atual"]
    # resultado do ativo, o resultado é calculado com base na cotação atual, portanto haverá valores mesmo que o ativo não tenha sido vendido.
    df["resultado"] = df["valor_atual"] - df["valor_investido"]
    # resultado percentual do ativo, se houver valor investido
    df["resultado_pct"] = (
        df["resultado"] / df["valor_investido"]).where(df["valor_investido"] > 0)
    # lucro realizado do ativo, soma de todas as operações de venda
    df["lucro_realizado"] = lucro.reindex(df.index).fillna(0.0)

    if not incluir_zerados:
        df = df[df["quantidade"] > 0]
    return df.sort_values("ticker").reset_index(drop=True)[colunas_saida]


def monthly_position(
        ativos: pd.DataFrame,
        operacoes: pd.DataFrame,
        cotacoes: pd.DataFrame,
        incluir_zerados: bool = False) -> pd.DataFrame:
    """ Uma linha por ativo para cada fechamento de mês, começando pelo mês da primeira compra até zerar a posição deste ativo.
        colunas: ticker, data, quantidade, preco_fechamento, valor_fechamento, preco_medio, valor_investido"""

    dataframe_validation.validate_required_columns(
        ativos, constants.COLUNAS_ATIVOS, "ativos")
    dataframe_validation.validate_required_columns(
        cotacoes, constants.COLUNAS_COTACOES, "cotacoes")

    colunas_saida = [
        "ticker",
        "quantidade",
        "data",
        "preco_fechamento",
        "valor_fechamento",
        "preco_medio",
        "valor_investido",
        "resultado",
        "resultado_pct"
    ]

    livro = livro_operacoes.build_book(operacoes)
    if livro.empty:
        return pd.DataFrame(columns=colunas_saida)

    # Ordenando as cotações por ativo e mês
    cotacoes_mes = cotacoes.sort_values(["data", "ativo_id"]).copy()
    cotacoes_mes["mes"] = cotacoes_mes["data"].dt.to_period(
        "M")  # Criando uma coluna para indicar o mês
    # Agrupando as cotações por ativo e mês e pegando a última cotação de cada ativo/mês
    cotacoes_mes = cotacoes_mes.loc[cotacoes_mes.groupby(["ativo_id", "mes"])[
        "data"].idxmax()]
    cotacoes_mes = cotacoes_mes.drop(columns=["mes"])  # Excluindo coluna mês
    cotacoes_mes = cotacoes_mes.reset_index(drop=True)  # Redefine os índices
    livro_por_data = livro[["ativo_id", "data", "quantidade_apos", "preco_medio_apos"]].sort_values(
        ["data", "ativo_id"]).drop_duplicates(["ativo_id", "data"], keep="last")
    cotacoes_mes = cotacoes_mes.sort_values(
        ["data", "ativo_id"], kind="stable").reset_index(drop=True)
    cotacoes_mes = pd.merge_asof(
        cotacoes_mes,
        livro_por_data,
        on="data",
        by="ativo_id",
        direction="backward"
    )
    cotacoes_mes["quantidade_apos"] = (
        cotacoes_mes["quantidade_apos"].fillna(0))
    cotacoes_mes["preco_medio_apos"] = (
        cotacoes_mes["preco_medio_apos"].fillna(0))
    cotacoes_mes = cotacoes_mes.rename(columns={
        "data_cotacao": "data",
        "quantidade_apos": "quantidade",
        "preco_medio_apos": "preco_medio"
    })
    cotacoes_mes["valor_fechamento"] = cotacoes_mes["quantidade"] * \
        cotacoes_mes["preco_fechamento"]
    cotacoes_mes["valor_investido"] = cotacoes_mes["quantidade"] * \
        cotacoes_mes["preco_medio"]
    cotacoes_mes["resultado"] = cotacoes_mes["valor_fechamento"] - \
        cotacoes_mes["valor_investido"]
    cotacoes_mes["resultado_pct"] = (cotacoes_mes["resultado"] / cotacoes_mes["valor_investido"]
                                     ) * 100 if cotacoes_mes["valor_investido"].sum() != 0 else 0
    if not incluir_zerados:
        cotacoes_mes = cotacoes_mes[cotacoes_mes["quantidade"] > 0]
    return cotacoes_mes.sort_values("data").reset_index(drop=True)[colunas_saida]
