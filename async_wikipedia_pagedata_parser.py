
# 20.07.25 - 6614 элементов
# 21.07.25 - 13148 элементов
# - Пробуем написать асинхронный парсер,
# после тестирования на списке из 10 адресов работает примерно в 15 раз быстрее!
# 24.07.25 асинхронный парсер страниц поиска написан и работает
# - Переписал и парсер по странице человека для асинхронной работы.
# Оказалось что удобнее создавать список уже из ссылок, а не ФИО,
# так как модуль wikipedia очень медленный. Он нужен только для summary.
# - После примерно 1000 страниц:
# ConnectionResetError: [WinError 10054] Удаленный хост принудительно разорвал существующее подключение
# 25.07.25 - Даже 100 запросов отключает, попробуем делить список запросов на чанки -> по 50 работает нормально.
# 28.07.25 - 14332 элементов - думаю убрать summary, чтобы парсить быстрее.
# 03.08.25 - Убрал парсер summary, можно бужет добавлять уже потом, при конкретном запросе
#          - 46100 элементов

# 04.08.25 - Парсит страницы Википедии. Ссылки на них загружаются из файла .txt (вводится в терминале).
# Работает асинхронно, может парсить файл с ~100000 ссылок (протестировано). 
# Но оптимально разбивать tasks на чанки по ~50-80 ссылок.
# При большем числе одновременных запросов Википедия может отключить соединение.
# На странице Википедии парсит данные из инфобокса. См. код.
# На выходе парсера - словарь, он сохраняется в список словарей по каждой url.
# Этот список сохраняется поэлементно в базу данных sqlite3
# 16.08.25 - 92000 элементов
# 17.08.25 - 100127 элементов

import requests
import wikipedia
import sqlite3
import aiohttp
import asyncio
import time
from bs4 import BeautifulSoup
from datetime import datetime

# Пока ненужная. Получает список по существующей странице Вики


def get_list_with_names(query):

    wikipedia.set_lang("ru")  # Устанавливаем язык на русский

    # Объект страницы со списком людей
    try:
        page = wikipedia.page(query, auto_suggest=False)
        list = page.links
        print(f'Найдено {len(list)} ссылок.')
        return list
    except Exception as e:
        print(f'>>> Нет страницы: {query}')
        return []


def load_list_with_names(filename):
    """Функция для загрузки строк из файла в список."""
    with open(filename, 'r', encoding='utf-8') as file:
        lines = file.readlines()  # Читает все строки из файла

    # Удаляем символы новой строки и пробелы
    list_with_names = [line.strip() for line in lines]
    return list_with_names


def get_urls_list(list_with_names):
    urls_list = []
    wikipedia.set_lang("ru")  # Устанавливаем язык на русский

    # Парсим каждую страницу по элементу из list_with_names
    for i in range(len(list_with_names)):  # len(list_with_names)
        try:
            urls_list.append(wikipedia.page(
                list_with_names[i], auto_suggest=False).url)
            print(f'Urls в списке: {i}')
        except:
            print(f'>>> Нет страницы: {list_with_names[i]}')
    return urls_list


def add_result_to_db(items_list: list):

    # Устанавливаем соединение с базой данных
    connection = sqlite3.connect('my_database.db')
    cursor = connection.cursor()

    # Создаем таблицу Users
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS public_artists_ussr (
    url TEXT,
    name TEXT,
    summary TEXT,
    occupation TEXT,
    bday TEXT,
    dday TEXT,
    lifespan_days INTEGER
       )
    ''')
    cnt = 0
    for result in items_list:
        # Добавляем нового пользователя
        if result:
            query = 'INSERT OR IGNORE INTO public_artists_ussr (url, name, summary, occupation, bday, dday, lifespan_days) VALUES (?, ?, ?, ?, ?, ?, ?)'
            cursor.execute(query, (result['url'], result['name'], result['summary'], result['occupation'],
                                   result['bday'], result['dday'], result['lifespan_days']))
            print(f"+++ Добавлен в базу {result['name']}.")
            cnt += 1

    # Сохраняем изменения и закрываем соединение
    connection.commit()
    connection.close()
    print(f' Добавлено в базу элементов: {cnt}.')


async def extract_data_from_url(session, url):
    wikipedia.set_lang("ru")  # Устанавливаем язык на русский

    data = {
        "url": url,
        "name": None,
        "summary": None,
        "occupation": None,
        "bday": None,
        "dday": None,
        "lifespan_days": None,
    }

    # ...
    try:
        async with session.get(url) as response:
            html = await response.text()
            soup = BeautifulSoup(html, 'html.parser')

            # 1. Текст поля <span> с атрибутом class="bday"
            bday_span = soup.find('span', class_='bday')
            if bday_span:
                data["bday"] = bday_span.text.strip()

            # 2. Текст поля <span> с атрибутом class="dday"
            dday_span = soup.find('span', class_='dday')
            if dday_span:
                data["dday"] = dday_span.text.strip()

            # 3. Расчет продолжительности жизни в днях - lifespan_days
            if data["bday"] and data["dday"]:
                try:
                    birth_date = datetime.strptime(data["bday"], '%Y-%m-%d')
                    death_date = datetime.strptime(data["dday"], '%Y-%m-%d')
                    data["lifespan_days"] = (death_date - birth_date).days
                except ValueError:
                    print(
                        f"!!! Не удалось преобразовать даты в формат YYYY-MM-DD для URL: {url}")
                    data["lifespan_days"] = None
            else:
                print(f"--- Не удалось найти bday или dday для элемента.")
                return None

            # 4. Текст поля <span> с атрибутом class="mw-page-title-main" - name
            title_span = soup.find('span', class_='mw-page-title-main')
            if title_span:
                data["name"] = title_span.text.strip()
                print(f'Парсим страницу: {data["name"]}...')

            # 5. Текст атрибута data-name из поля <table> с атрибутами style и data-name - occupation
            # или  soup.select_one('table[style][data-name]')
            table = soup.find(
                'table', attrs={'style': True, 'data-name': True})
            if table:
                data["occupation"] = table.get('data-name')

            # 6. Summary
            # page_for_parse = wikipedia.page(data["name"], auto_suggest=False)
            # if page_for_parse:
            #    data["summary"] = page_for_parse.summary
            

            return data
    except requests.exceptions.RequestException as e:
        print(f">>> Ошибка при запросе к URL {url}: {e}")
    except Exception as e:
        print(f">>> Произошла ошибка при обработке URL {url}: {e}")


# Запрос страницы со списком элементов по названию статьи Википедии
# и формирование списка элементов list_with_names
# query_for_page_with_names = "Список народных артистов СССР"
# list_with_names = get_list_with_names(query_for_page_with_names)

# Формирование списка элементов списка элементов list_with_names
# из файла filename
# filename = 'artists.txt'
# with open(filename, 'r', encoding='utf-8') as file:
#    list_with_names = file.read().splitlines()

async def main():
    
    filename = input('Имя файла со ссылками: ')

    start_time = time.time()
    print('Пуск!')
    urls_list = load_list_with_names(filename)[:]

    # Весь список ссылок делим на чанки, чтобы не перегружать запросами сайт
    chunk_size = 80
    for i in range(0, len(urls_list), chunk_size):
        # urls_list = get_urls_list(list_with_names)
        print(f'+++ Сформирован список urls_list {(i+chunk_size)//chunk_size}/{len(urls_list)//chunk_size} из {len(urls_list[i:i + chunk_size])} элемента(ов)')

        async with aiohttp.ClientSession() as session:
            tasks = [extract_data_from_url(session, url)
                     for url in urls_list[i:i + chunk_size]]

            # Получаем items_list - список из словарей результатов по каждой url
            items_list = await asyncio.gather(*tasks)

            if items_list:
                print(
                    f'>>> Спарсили список items_list из {len(items_list)} элемента(ов).')
            add_result_to_db(items_list)
            time_delta = time.time() - start_time
            # print(f'Затрачено: %.2f с.' % time_delta)
            print(f'Затрачено: {time_delta//60} мин. {time_delta%60} c.')
            print("Done!")

loop = asyncio.get_event_loop()
loop.run_until_complete(main())
