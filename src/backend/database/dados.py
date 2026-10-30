# Camada que lê os dados do banco de dados e retorna dataframes pandas
from __future__ import annotations
import os
import pandas as pd

from dotenv import load_dotenv
from sqlalchemy import create_engine, Engine

# Conexão com o banco de dados


def create_db_engine() -> Engine:
    """Conecta usando a variável DATABASE_URL (lida do arquivo .env)."""
    load_dotenv()
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError(
            "DATABASE_URL não encontrada. Verifique o arquivo .env na raiz do projeto.")
    return create_engine(url)

# Conversor de tipos numeric e date (postgresql) para float e datetime (pandas)


def _normalizar(df: pd.DataFrame, colunas_data=(), colunas_numero=()) -> pd.DataFrame:
    """O PostgreSQL devolve numeric como Decimal e date como objeto; convertemos para float e datetime."""
    for col in colunas_data:
        df[col] = pd.to_datetime(df[col]).astype("datetime64[ns]")
    for col in colunas_numero:
        df[col] = df[col].astype(float)
    return df


def load_ativos(engine: Engine) -> pd.DataFrame:
    sql = """
        select a.id_ativos as ativo_id, a.ticker, c.classe_ativo as classe
        from investimentos.ativos a
        join investimentos.classe_ativo c using (id_classe_ativo)
        order by a.ticker
    """
    return pd.read_sql(sql, engine)


def load_operacoes(engine: Engine) -> pd.DataFrame:
    sql = """
        select o.id_ativos as ativo_id, a.ticker, o.tipo_operacao as tipo, o.data_operacao as data,
               o.quantidade, o.preco_unitario, o.taxa_rateada as taxas
        from investimentos.operacoes o
        join investimentos.ativos a using(id_ativos)
        order by data_operacao, id_operacao
    """
    df = pd.read_sql(sql, engine)
    return _normalizar(df, ["data"], ["quantidade", "preco_unitario", "taxas"])


def load_cotacoes(engine: Engine) -> pd.DataFrame:
    sql = """
        select c.id_ativos as ativo_id, a.ticker, c.data_cotacao as data, c.preco_fechamento
        from investimentos.cotacoes c
        join investimentos.ativos a using(id_ativos)
        order by id_ativos, data_cotacao
    """
    df = pd.read_sql(sql, engine)
    return _normalizar(df, ["data"], ["preco_fechamento"])


def load_aportes(engine: Engine) -> pd.DataFrame:
    sql = """
        select if.nome as instituicao_financeiria, a.data_aporte, a.valor_aporte
        from investimentos.aportes a
        join investimentos.instituicao_financeira if using(id_inst_financeira)
        order by data_aporte
    """
    df = pd.read_sql(sql, engine)
    return _normalizar(df)
