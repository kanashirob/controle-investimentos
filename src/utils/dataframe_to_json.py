import json

import pandas as pd


def dataframe_to_json(df: pd.DataFrame) -> list[dict]:
    """Converte um DataFrame em uma lista de dicionários segura para JSON.

    NaN vira null e datas viram texto no formato ISO (o JSON não tem NaN nem tipo data).
    """
    return json.loads(df.to_json(orient="records", date_format="iso"))
