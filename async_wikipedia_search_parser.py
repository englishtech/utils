# 03.08.25 - Добавлен ввод строки поиска в терминале
# 04.08.25 - Парсит все ссылки на странице поиска Википедии (https://ru.wikipedia.org/w/index.php?search=&title=...)
# по строке запроса, вводимого в терминале.
# Настраивается пагинация, если результаты поиска не помещаются на одну страницу (макс. 5000 элементов/стр.)
# В Википедии есть ограничение на 10000 элементов в поисковой выдаче.
# Сохраняет ссылки построчно в текстовый файл, название - "транслитерированный_запрос.txt"

import requests
from bs4 import BeautifulSoup
from urllib.parse import quote_plus
import aiohttp
import asyncio
from time import time as tm


def get_urls_list(query):
    # На вход функции подается запрос (query)
    # и имя файла (filename) для сохранения списка items_list
    phrase = "Дата смерти"          # Обязательная фраза
    limit = 100                    # Сколько элементов на странице
    offset = 0                      # С какой страницы начинаем

    # Преобразуем русские в url
    query_url = quote_plus(query, safe='/?&=')
    phrase_url = quote_plus(phrase, safe='/?&=')

    # Парсим первую страницу поиска, чтобы определить число элементов items_total
    url = 'https://ru.wikipedia.org/w/index.php?title=%D0%A1%D0%BB%D1%83%D0%B6%D0%B5%D0%B1%D0%BD%D0%B0%D1%8F:%D0%9F%D0%BE%D0%B8%D1%81%D0%BA&limit=' + str(limit) + \
        '&offset=' + str(offset) + '&ns0=1&search=' + query_url + '+%22' + phrase_url + \
        '%22&advancedSearch-current=%7B%22fields%22%3A%7B%22phrase%22%3A%22' + \
        phrase_url + '%22%7D%7D'

    urls_list = []

    # Извлекаем с первой страницы число элементов items_total
    try:
        response = requests.get(url)
        response.raise_for_status()  # Проверка на успешный запрос
        soup = BeautifulSoup(response.content, 'html.parser')

    except requests.exceptions.RequestException as e:
        print(f">>> Ошибка при запросе к URL {url}: {e}")
    except Exception as e:
        print(f">>> Произошла ошибка при обработке URL {url}: {e}")

    items_total = soup.find('div', class_='results-info').get('data-mw-num-results-total')
    print(f'Для запроса "{query}" найдено {items_total} элементов.')

    # По начальному url получаем список url в количестве items_total
    # Каждая url содержит limit элементов
    for i in range(0, int(items_total), limit):
        temp_url = 'https://ru.wikipedia.org/w/index.php?title=%D0%A1%D0%BB%D1%83%D0%B6%D0%B5%D0%B1%D0%BD%D0%B0%D1%8F:%D0%9F%D0%BE%D0%B8%D1%81%D0%BA&limit=' + str(limit) + \
            '&offset=' + str(i) + '&ns0=1&search=' + query_url + '+%22' + phrase_url + \
            '%22&advancedSearch-current=%7B%22fields%22%3A%7B%22phrase%22%3A%22' + \
            phrase_url + '%22%7D%7D'
        urls_list.append(temp_url)
    print(f'Создан список из {len(urls_list)} страниц для поиска.')
    
    user_input = input("Продолжаем? (y/n д/н): ").strip().lower()  # Читаем ввод
    if user_input in 'yд':
        print("Продолжаем...")
        return urls_list
    elif user_input in 'nн':
        return []
    



def transliterate_to_english(russian_text):
    """Функция для транслитерации русского текста в английские буквы."""
    # Словарь для замены кириллицы на латиницу
    translit_dict = {
        'А': 'A', 'Б': 'B', 'В': 'V', 'Г': 'G', 'Д': 'D', 'Е': 'E', 'Ё': 'Yo', 'Ж': 'Zh',
        'З': 'Z', 'И': 'I', 'Й': 'Y', 'К': 'K', 'Л': 'L', 'М': 'M', 'Н': 'N', 'О': 'O',
        'П': 'P', 'Р': 'R', 'С': 'S', 'Т': 'T', 'У': 'U', 'Ф': 'F', 'Х': 'Kh', 'Ц': 'Ts',
        'Ч': 'Ch', 'Ш': 'Sh', 'Щ': 'Shch', 'Ы': 'Y', 'Э': 'E', 'Ю': 'Yu', 'Я': 'Ya',
        'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'yo', 'ж': 'zh',
        'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm', 'н': 'n', 'о': 'o',
        'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u', 'ф': 'f', 'х': 'kh', 'ц': 'ts',
        'ч': 'ch', 'ш': 'sh', 'щ': 'shch', 'ы': 'y', 'э': 'e', 'ю': 'yu', 'я': 'ya',
        ' ': ' ', ',': ',', '.': '.', '!': '!', '?': '?', '-': '-', 'ь': '-', 'ъ': '-'
    }

    # Транслитерация
    transliterated_text = ''.join(translit_dict.get(
        char, char) for char in russian_text)
    return transliterated_text


def save_to_txt(items_list, query):
    filename_en = transliterate_to_english(query) + ".txt"
    # Сохраняем множество set(items_list) в файл filename в виде элементов на каждой строке
    with open(filename_en, 'w', encoding='utf-8') as file:
        for item in items_list:
            file.write(f'{item}\n')
    print(f'Сохранено в файл [{filename_en}]')


async def fetch_and_parse(session, url):

    items_list = []         # Список для всех результатов на выходе

    # ...
    try:
        async with session.get(url) as response:
            html = await response.text()
            soup = BeautifulSoup(html, 'html.parser')

            # Работа только с блоком результатов поиска
            results_container = soup.find(
                'div', class_="mw-search-results-container")

            if results_container:
                # Поиск по всем блокам, содержащим ссылку
                for item in results_container.find_all('a', href=True):
                    try:
                        # Извлекаем текст ссылки
                        # или по тегу item.get('data-prefixedtext')   |   item.text.strip()
                        # и добавляем в список items_list
                        items_list.append('https://ru.wikipedia.org' + item.get('href'))
                    except Exception as e:
                        print(f'>>> Ошибка добавления в items_list: {item}')
            else:
                print(f'!!! Пустой results_container для ссылки:\n{url}')
            print(f'Добавлено {len(items_list)} эл.', sep='\n')
    except Exception as e:
        print(f">>> Произошла ошибка при обработке URL {url}: {e}")
    return items_list


async def main():
    
    urls_list = []
    while not urls_list:
        query = input("Введите строку поиска: ")               # Кого ищем
        urls_list = get_urls_list(query)    # Получаем список url для парсинга
        
    start_time = tm()
    print(f'Пуск!')

    async with aiohttp.ClientSession() as session:
        tasks = [fetch_and_parse(session, url) for url in urls_list]

        # Получаем items_list - список из списков результатов по каждой url
        items_list = await asyncio.gather(*tasks)

        # Все сбрасываем в один список, исключаем повторы
        flat_items_list = list(
            set([item for sublist in items_list for item in sublist]))
        print(
            f'Список flat_items_list сформирован - {len(flat_items_list)} элемента(ов).')

        # Сохраняем в файл query.txt (название транслитерируем)
        save_to_txt(flat_items_list, query)

    time_delta = tm() - start_time
    # print(f'Затрачено: %.2f с.' % time_delta)
    print(f'Затрачено: {time_delta//60} мин. {time_delta%60} c.')
    
loop = asyncio.get_event_loop()
loop.run_until_complete(main())
