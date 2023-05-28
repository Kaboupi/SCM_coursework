import yaml
from os import listdir
from loguru import logger

def get_yaml(path: str) -> dict:
    """### Возвращает список параметров из произвольного .yaml

    Args:
        path (str): Путь к .yaml

    Returns:
        dict: Список параметров подключения из params.yaml
    """
    with open(path) as f:
        params = yaml.load(f, Loader=yaml.FullLoader)
    
    return params


def get_queries(folder_path: str):
    res_li = []
    
    def read_file(file_path: str) -> str:
        with open(file_path, 'r') as f:
            file_contents = f.read()
        return file_contents
    
    for file in listdir(folder_path):
        res_li.append(read_file(f'{folder_path}/{file}'))
        
    logger.info('Считали запросы')
    return res_li