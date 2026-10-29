"""Camada de cálculo: recebe DataFrames e devolve DataFrames. Não acessa o banco."""
import numpy as np
import pandas as pd

COMPRA = "COMPRA"
VENDA = "VENDA"
BONIFICACAO = "BONIFICAÇÃO"
_ENTRADAS = {COMPRA, BONIFICACAO}  # tipos que aumentam a posição
_EPS = 1e-9                        # tolerância para erros de arredondamento

COLUNAS_OPERACOES = ["ativo_id", "tipo", "data",
                     "quantidade", "preco_unitario", "taxas"]
COLUNAS_ATIVOS = ["ativo_id", "ticker", "classe"]
COLUNAS_COTACOES = ["ativo_id", "data", "preco_fechamento"]


def _validar(df: pd.DataFrame, colunas: list, nome: str) -> None:
    """Garante que a tabela recebida tem as colunas de que o cálculo precisa."""
    faltando = [c for c in colunas if c not in df.columns]
    if faltando:
        raise ValueError(f"'{nome}' sem as colunas obrigatórias: {faltando}")


def construir_livro(operacoes: pd.DataFrame) -> pd.DataFrame:
    """Percorre as operações em ordem e anota a situação da posição depois de cada uma.

    Regras:
      - COMPRA: a quantidade sobe e o custo total sobe (taxas incluídas).
      - BONIFICAÇÃO: igual à compra, com o custo atribuído pela empresa.
      - VENDA: o preço médio NÃO muda; o custo sai na proporção do preço médio.
        Lucro realizado = valor recebido (líquido de taxas) - quantidade x preço médio.
      - Zerou a posição: o preço médio recomeça do zero na próxima compra.
      - No mesmo dia, as entradas são processadas antes das vendas.
    """
    _validar(operacoes, COLUNAS_OPERACOES, "operacoes")
    df = operacoes.copy()

    invalidos = set(df["tipo"]) - _ENTRADAS - {VENDA}
    if invalidos:
        raise ValueError(
            f"Tipo de operação não reconhecido: {sorted(invalidos)}")

    # valor da operação: entradas somam as taxas; a venda desconta as taxas
    bruto = df["quantidade"] * df["preco_unitario"]
    eh_entrada = df["tipo"].isin(_ENTRADAS)
    df["valor_total"] = np.where(
        eh_entrada, bruto + df["taxas"], bruto - df["taxas"])

    # ordem: por ativo, por data e, no mesmo dia, entradas (0) antes das vendas (1)
    df["_ordem"] = (~eh_entrada).astype(int)
    df = df.sort_values(["ativo_id", "data", "_ordem"],
                        kind="stable").reset_index(drop=True)

    estado = {}  # para cada ativo: (quantidade, custo_total)
    qtd_apos, custo_apos, medio_apos, lucro = [], [], [], []
    for op in df.itertuples(index=False):
        qtd, custo = estado.get(op.ativo_id, (0.0, 0.0))
        lucro_da_operacao = 0.0

        if op.tipo in _ENTRADAS:
            qtd += op.quantidade
            custo += op.valor_total
        else:  # VENDA
            if op.quantidade > qtd + _EPS:
                raise ValueError(
                    f"Venda de {op.quantidade:g} em {op.data:%d/%m/%Y} é maior que a posição "
                    f"({qtd:g}) do ativo_id={op.ativo_id}. Falta alguma compra?"
                )
            preco_medio = custo / qtd
            lucro_da_operacao = op.valor_total - op.quantidade * preco_medio
            custo -= op.quantidade * preco_medio
            qtd -= op.quantidade
            if qtd < _EPS:  # zerou a posição
                qtd, custo = 0.0, 0.0

        estado[op.ativo_id] = (qtd, custo)
        qtd_apos.append(qtd)
        custo_apos.append(custo)
        medio_apos.append(custo / qtd if qtd > 0 else 0.0)
        lucro.append(lucro_da_operacao)

    df["quantidade_apos"] = qtd_apos
    df["custo_total_apos"] = custo_apos
    df["custo_medio_apos"] = medio_apos
    df["lucro_realizado"] = lucro
    return df.drop(columns="_ordem")


def calcular_posicao_atual(
    ativos: pd.DataFrame,
    operacoes: pd.DataFrame,
    cotacoes: pd.DataFrame,
    incluir_zerados: bool = False,
) -> pd.DataFrame:
    """Uma linha por ativo: quantidade, preço médio, valor investido, valor atual e resultado.

    O preço atual é a cotação mais recente de cada ativo. Sem cotação, os campos de
    valor atual e resultado ficam vazios (NaN) em vez de inventar um número.
    """
    _validar(ativos, COLUNAS_ATIVOS, "ativos")
    _validar(cotacoes, COLUNAS_COTACOES, "cotacoes")

    colunas_saida = ["ticker", "classe", "quantidade", "preco_medio", "valor_investido",
                     "preco_atual", "valor_atual", "resultado", "resultado_pct", "lucro_realizado"]
    livro = construir_livro(operacoes)
    if livro.empty:
        return pd.DataFrame(columns=colunas_saida)

    # situação de cada ativo depois da sua última operação
    ultimo = livro.groupby("ativo_id").tail(1).set_index("ativo_id")
    lucro = livro.groupby("ativo_id")["lucro_realizado"].sum()

    # cotação mais recente de cada ativo
    cot = cotacoes.sort_values("data", kind="stable")
    preco_atual = cot.groupby("ativo_id")["preco_fechamento"].last()

    df = ativos.set_index("ativo_id")[["ticker", "classe"]].join(
        ultimo[["quantidade_apos", "custo_total_apos",
                "custo_medio_apos"]], how="inner"
    )
    df = df.rename(columns={
        "quantidade_apos": "quantidade",
        "custo_total_apos": "valor_investido",
        "custo_medio_apos": "preco_medio",
    })
    df["preco_atual"] = preco_atual.reindex(df.index)
    df["valor_atual"] = df["quantidade"] * df["preco_atual"]
    df["resultado"] = df["valor_atual"] - df["valor_investido"]
    df["resultado_pct"] = (
        df["resultado"] / df["valor_investido"]).where(df["valor_investido"] > 0)
    df["lucro_realizado"] = lucro.reindex(df.index).fillna(0.0)

    if not incluir_zerados:
        df = df[df["quantidade"] > 0]
    return df.sort_values("ticker").reset_index(drop=True)[colunas_saida]


def calcular_resumo(posicao: pd.DataFrame) -> pd.Series:
    """Totais da carteira a partir da posição atual.

    O resultado soma só os ativos que têm cotação; `ativos_sem_preco` diz quantos ficaram de fora.
    """
    com_preco = posicao["valor_atual"].notna()
    investido = posicao["valor_investido"].sum()
    investido_com_preco = posicao.loc[com_preco, "valor_investido"].sum()
    # ativos sem cotação têm resultado vazio e não entram
    resultado = posicao["resultado"].sum()
    return pd.Series({
        "total_investido": investido,
        "valor_atual": posicao["valor_atual"].sum(),
        "resultado": resultado,
        "resultado_pct": resultado / investido_com_preco if investido_com_preco > 0 else np.nan,
        "lucro_realizado": posicao["lucro_realizado"].sum(),
        "ativos_sem_preco": int((~com_preco).sum()),
    })
