# Tipos de operação
COMPRA = "COMPRA"
VENDA = "VENDA"
BONIFICACAO = "BONIFICAÇÃO"

TIPO_ENTRADA = {COMPRA, BONIFICACAO}
TIPO_SAIDA = {VENDA}
# -------------------------------------------------------------------

# Colunas obrigatórias para o cálculo do livro de operações
COLUNAS_OPERACOES = ["ativo_id", "ticker", "tipo", "data",
                     "quantidade", "preco_unitario", "taxas"]

# Colunas obrigatórias para o cálcuclo de posição atual
COLUNAS_ATIVOS = ["ativo_id", "ticker", "classe"]
COLUNAS_COTACOES = ["ativo_id", "data", "preco_fechamento"]
# --------------------------------------------------------------------
