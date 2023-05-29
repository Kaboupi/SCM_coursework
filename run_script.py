import numpy as np
import pandas as pd
from sqlalchemy import create_engine, text as sql_text
from crud.crud import *
from crud.params import get_yaml, get_queries
from datetime import datetime, timedelta
from loguru import logger

params = get_yaml('./src/params.yaml')['connection']
engine = create_engine(f"postgresql://{params['user']}:{params['password']}@{params['host']}:{5432}/{params['database']}")
conn = engine.connect()
logger.success('Подключились к базе данных postgres')

q_create, q_insert, query = get_queries('./sql')
logger.info('Считали параметры подключения')
conn.execute(q_create)
logger.info('Создали таблицы')
conn.execute(q_insert)
logger.info('Занесли значения')


if __name__ == '__main__':
    so_df = pd.read_sql("SELECT * FROM Standard_Operation;", conn, index_col='operation_id')
    df = pd.read_sql(query, conn, index_col='sales_order_id')
    logger.info('Загрузили таблицу в датафрейм')
    
    df = pd.concat([df, get_tolerance(df)], axis=1)
    df = df.join(calculate_required_resources(df, so_df, conn), on=df.index)

    res_df = get_res_df(df, conn)
    res_df.to_sql('mrp', conn, if_exists='replace')
    logger.success('Таблица успешно выгружена в mrp')
    res_df.to_csv('./result_output/MRP.csv')
    logger.success('Таблица успешно сохранена в .csv')
