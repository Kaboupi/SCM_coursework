# Курсовая работа по дисциплине SCM
---

![SCM](https://ircgroupglobal.com/wp-content/uploads/2020/01/0.jpg)

### Порядок запуска:
1. Иметь поднятую PostgreSQL DB
2. Указать параметры подключения в `.src/params.yaml`
3. Прописать следующие команды:

    Создаём виртуальное окружение
    ```bash
    python -m venv venv
    ```
    Активируем виртуальное окружение
    ```bash
    venv/Scripts/activate
    ```
    Устанавливаем зависимости и библиотеки
    ```bash
    pip install -Ur ./src/requirements.txt
    ```
4. Запускаем скрипт
    ```bash
    python run_script.py
    ```
5. Вставляем запрос `./src/mrp.sql` в PostgreSQL
6. Готово!
