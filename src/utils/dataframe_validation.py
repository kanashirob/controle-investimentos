import pandas as pd


def validate_required_columns(df: pd.DataFrame, colunas: list, nome: str) -> None:
    """ Garante que a tabela recebida tem as colunas necessárias para o cálculo. """
    colunas_faltando = [c for c in colunas if c not in df.columns]
    if colunas_faltando:
        raise ValueError(
            f"'{nome}' sem as conlunas obrigatórias:{colunas_faltando}")
