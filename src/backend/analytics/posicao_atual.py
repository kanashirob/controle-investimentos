"""Camada de cálcuclo: recebe DataFrames e devolve DataFrames. Não acessa o banco de dados."""

import numpy as np
import pandas as pd


from backend.constants import constants
from backend.utils.dataframe_validation import validate_required_columns
from backend.analytics.livro_operacoes import build_book


def current_position(
        ativos: pd.DataFrame,
        operacoes: pd.DataFrame,
        cotacoes: pd.DataFrame,
        incluir_zerados: bool = False) -> pd.DataFrame:
    """Uma linha por ativo: quantidade, preço médio, valor investido, valor atual e resultado.

    O preço atual é a cotação mais recente de cada ativo. Sem cotação, os campos de valor atual e resultado ficam vazios (NaN) em vez de inventar um número.
    """
    validate_required_columns(ativos, constants.COLUNAS_ATIVOS, "ativos")
    validate_required_columns(cotacoes, constants.COLUNAS_COTACOES, "cotacoes")

    colunas_saida = ["ticker",
                     "classe",
                     "quantidade",
                     "preco_medio",
                     "valor_investido",
                     "preco_atual",
                     "data_cotacao",
                     "valor_atual",
                     "resultado",
                     "resultado_pct",
                     "lucro_realizado"]

    livro = build_book(operacoes)
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
