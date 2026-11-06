"""Camada de cálculo: recebe DataFrames e devolve DataFrames."""

import numpy as np
import pandas as pd

from constants import constants
from utils.dataframe_validation import validate_required_columns

_EPS = 1e-9  # tolerância para erros de arredondamento


def build_book(operacoes: pd.DataFrame) -> pd.DataFrame:
    """ Percorre as operações em ordem e anota a situação da posição depois de cada uma.

    Regras: 
      - COMPRA: a quantidade sobe e o custo total sobe (taxas incluídas).
      - BONOIFICAÇÃO: igual à compra, com o custo atribuído pela empresa.
      - VENDA: o preço médio NÃO muda; o custo sai na proporção do preço médio.
        Lucro realizado = valor recebido (líquido de taxas) - quantidade x preço médio.
        - Zerou a posição: o preço médio recomeça do zero na próxima compra.
        - No mesmo dia, as entradas são processadas antes das vendas.
    """

    # Validar se as colunas obrigatórias estão presentes.
    validate_required_columns(
        operacoes, constants.COLUNAS_OPERACOES, "operacoes")
    df = operacoes.copy()
    invalidos = set(df["tipo"]) - constants.TIPO_ENTRADA - constants.TIPO_SAIDA
    if invalidos:
        raise ValueError(
            f"Tipo de operação não reconhecido: {sorted(invalidos)}")

    # Calcula valor da operação com taxas: entradas somam as taxas; saidas descontam as taxas
    bruto = df['quantidade'] * df['preco_unitario']
    is_entrada = df['tipo'].isin(constants.TIPO_ENTRADA)
    df['valor_total'] = np.where(
        is_entrada, bruto + df['taxas'], bruto - df['taxas'])

    # Ordena por ativo, por data  e, no mesmo dia, entradas antes das saídas
    df['_ordem'] = (~is_entrada).astype(int)  # 0 para entradas, 1 para saídas
    df = df.sort_values(['ativo_id', 'ticker', 'data', '_ordem'],
                        # ordena por ativo, data e, em caso de empate, por _ordem (entradas(0) antes das saídas(1))
                        kind='stable').reset_index(drop=True)
    state = {}  # {ativo: (quantidade, custo_total)}
    qtd_apos, custo_apos, medio_apos, lucro = [], [], [], []
    for op in df.itertuples(index=False):
        qnt, custo = state.get(op.ativo_id, (0.0, 0.0))
        lucro_da_operacao = 0.0

        if op.tipo in constants.TIPO_ENTRADA:
            qnt += op.quantidade
            custo += op.valor_total
        else:  # VENDA, os tipos desconhecidos já foram rejeitados antes
            if op.quantidade > qnt + _EPS:
                raise ValueError(
                    f"Venda de {op.quantidade} maior que posição atual de {qnt} para ativo {op.ativo_id} em {op.data}")
            preco_medio = custo / qnt
            lucro_da_operacao = op.valor_total - (op.quantidade * preco_medio)
            custo -= op.quantidade * preco_medio
            qnt -= op.quantidade
            if qnt < _EPS:  # posicao zerada
                qnt = 0.0
                custo = 0.0

        state[op.ativo_id] = (qnt, custo)
        qtd_apos.append(qnt)
        custo_apos.append(custo)
        medio_apos.append(custo / qnt if qnt > 0 else 0.0)
        lucro.append(lucro_da_operacao)

    df["quantidade_apos"] = qtd_apos
    df["custo_total_apos"] = custo_apos
    df["preco_medio_apos"] = medio_apos
    df["lucro_realizado"] = lucro
    return df.drop(columns=['_ordem'])
