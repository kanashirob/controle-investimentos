import os

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine

load_dotenv()  # lê o arquivo .env e coloca DATABASE_URL no ambiente

engine = create_engine(os.environ["DATABASE_URL"])

sql = """
    select table_name
    from information_schema.tables
    where table_schema = 'investimentos'
    order by 1
"""
tabelas = pd.read_sql(sql, engine)

print(tabelas)
print(f"\n{len(tabelas)} tabelas encontradas (esperado: 10)")
