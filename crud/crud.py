import numpy as np
import pandas as pd
from sqlalchemy import create_engine, engine
from datetime import datetime, timedelta
from typing import List
from loguru import logger


def get_tolerance(data: pd.DataFrame) -> pd.DataFrame:
    """### Возвращает pandas.DataFrame со значеними допуска для материалов

    Args:
        data (pd.DataFrame): Основной DataFrame для расчётов 

    Returns:
        pd.DataFrame: Возвращает pandas.DataFrame со значениями допуска для материалов. \n
        Содержит две колонки - `Значение_допуска` и `Допуск`
    """
    tol_val = (data['so_weight'] // data['unit_weight']).astype(np.int16)
    res = np.where(data['so_weight'] - tol_val * data['unit_weight'] >= 0, 'Допуск', 'Нет допуска')
    
    logger.info('Получили pd.DataFrame с допусками')    
    return pd.DataFrame({
        'Значение_допуска': tol_val,
        'Допуск': res
        })


def get_datetime(data: pd.DataFrame, time: pd.DataFrame) -> list:
    """### Возвращает список итоговых дат выполнения заказа

    Args:
        data (pd.DataFrame): Основной DataFrame для расчётов
        time (pd.DataFrame): Заполненный DataFrame с агрегатами

    Returns:
        list: Список с заполненными значениями в формате `YYYY-MM-DD`
    """
    delay_array = np.zeros(data.shape[0], dtype=np.int32)
    time_loc = time.set_index(data.index)
    dates = pd.to_datetime(data['due_date'], format='%Y-%m-%d')
    res_list = []
        
    for idx, val in enumerate(time_loc.index):
        delay_array[idx] += ((time_loc.loc[val] > 23) & (time_loc.loc[val] != np.inf)).sum()
    del time_loc
                
    for i, day in enumerate(dates):
        res_list.append((day + pd.to_timedelta(delay_array[i], unit='d')).strftime('%Y-%m-%d'))
        
    return res_list


def get_empty(data: pd.DataFrame, standard_operation: pd.DataFrame) -> List:
    """### Возвращает два pandas.DataFrame, заполненные нулями

    Args:
        data (pd.DataFrame): Основной DataFrame
        standard_operation (pd.DataFrame): Таблица Standard_Operation

    Returns:
        List: Список из двух `pandas.DataFrame` - resources, power
        
    Examples
    --------
    >>> get_empty(df, so)[0]
            col_1   col_2
    idx_0       0       0
    idx_1       0       0
    idx_2       0       0
    
    где `idx_n` - индексы `data` 
    """
    resources = standard_operation['product_id'].value_counts().max()
    power = standard_operation['product_id'].nunique()
    
    resources_df = pd.DataFrame(np.zeros((data.shape[0], resources), dtype=float) + 0, index=np.sort(data.index)                        )
    power_df = pd.DataFrame(np.zeros((data.shape[0], power), dtype=float) + 0, index=np.sort(data.index))
    
    del resources, power
    logger.info('Создали pd.DataFrame для дат выполнения заказа')
    logger.info('Создали pd.DataFrame для требуемых ресурсов')
    return [resources_df, power_df]


def get_product_query(num: int) -> str:
    return """SELECT
               o.product_id,
               o.performance,
               o.yield,
               r.resource_desc
           FROM
               Standard_operation o,
               Resources r
           WHERE
               o.resource_id = r.resource_id
               AND
               o.product_id = {}
           ORDER BY
               o.operation_id ASC""".format(num)


def calculate_required_resources(data: pd.DataFrame, 
                                 standard_operation: pd.DataFrame, 
                                 conn: engine.Connection) -> pd.DataFrame:
    """### Возвращает pandas.DataFrame с данными для таблицы `MRP`

    Args:
        data (pd.DataFrame): Основной DataFrame для обработки
        standard_operation (pd.DataFrame): Таблица `Standard_Operation`
        conn (engine.Connection): Подключение к базе данных `postgres`

    Returns:
        pd.DataFrame: Результирующий DataFrame с рассчитанными значениями
    """
    product_idxs = np.arange(data['product_id'].nunique()) + 1
    resources, power = get_empty(data, standard_operation)
    
    for iter in product_idxs:
        query = get_product_query(iter)

        indexes = data[data['product_id'] == iter].index
        yields = pd.read_sql(query, conn)['yield'].values
        performance = pd.read_sql(query, conn)['performance'].values[::-1]
        
        for i, col in enumerate(indexes.values):
            resources.loc[col].iloc[:yields.shape[0] - 1] = yields[:-1]
            power.loc[col].iloc[:performance.shape[0]] = performance
        
    resources.iloc[:, 0] = data['so_weight'] / 0.984
    power.iloc[:, 0] = resources.iloc[:, 0] / power.iloc[:, 0]
    
    for i in np.arange(resources.shape[1])[1:]:
        resources.iloc[:, i] = resources.iloc[:, i - 1] / resources.iloc[:, i]
        power.iloc[:, i] = resources.iloc[:, i - 1] / power.iloc[:, i]
    data['Дата_начала'] = get_datetime(data, power)
    
    del indexes, performance, yields
    power = power.T.replace(np.inf, 0).sum()
    resources = resources.T.replace(np.inf, 0).max()
    logger.info('Рассчитали требуемые данные для таблицы MRP.')

    return pd.DataFrame({
            'Требуемые_ресурсы': np.round(resources, 3),
            'Требуемая_мощность': np.round(power, 3)
            })

    
def get_res_df(df: pd.DataFrame, conn: engine.Connection) -> pd.DataFrame:
    """### Возвращает итоговый pandas.DataFrame с колонкой даты начала

    Args:
        data (pd.DataFrame): DataFrame после обработки с требованиями

    Returns:
        pd.DataFrame: Итоговый DataFrame MRP
    """
    df = df.sort_index()
    df['Дата_завершения'] = pd.read_sql('select so_due_date from sales_orders;', conn).values
    
    date = pd.to_datetime(df['Дата_завершения'], format='%Y-%m-%d')
    start_date = date - pd.to_timedelta(df['Требуемая_мощность'], unit='h')
    df['Дата_начала'] = start_date.dt.date

    return df[['Значение_допуска',
                 'Допуск',
                 'Требуемые_ресурсы',
                 'Требуемая_мощность',
                 'Дата_начала',
                 'Дата_завершения']]
