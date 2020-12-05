import requests
import os
import re
import json
import argparse
import sys
import logging
import urllib3
from pathlib import Path
from bs4 import BeautifulSoup
from pathvalidate import sanitize_filename


class TululuError(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.message = message


def check_tululu_response(response, message):
    response.raise_for_status()
    if response.url == 'http://tululu.org/':
        raise TululuError(message)


def download_txt(url, filename, book_id, folder='books/'):
    os.makedirs(folder, exist_ok=True)
    response = requests.get(url, verify=False)

    sanitized_filename = sanitize_filename(filename)
    full_file_name = f'{sanitized_filename}_{book_id}'
    book_path = Path(folder).joinpath(f'{full_file_name}.txt')

    check_tululu_response(response, f"Book was not downloaded from the url: {url}")
    with open(book_path, 'wb') as book:
        book.write(response.content)
    return str(book_path)


def download_image(url, filename, book_id, folder='images/'):
    os.makedirs(folder, exist_ok=True)
    response = requests.get(url, verify=False)
    sanitized_filename = sanitize_filename(filename)
    img_extension = Path(url).suffix
    full_filename = f'{sanitized_filename}_{book_id}{img_extension}'
    book_image_path = f'{os.path.join(folder, full_filename)}'

    check_tululu_response(response, f"Book image was not downloaded from the url: {url}")
    with open(book_image_path, 'wb') as image:
        image.write(response.content)
    return str(book_image_path)


def parsing_cmd_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('--start_page', default=1, type=int)
    parser.add_argument('--end_page', default=701, type=int)
    parser.add_argument('--dest_folder', default='books_images/')
    parser.add_argument('--json_path', default='all_books.json')
    parser.add_argument('--skip_imgs', action='store_true')
    parser.add_argument('--skip_txt', action='store_true')
    return parser.parse_args()


if __name__ == '__main__':
    args = parsing_cmd_arguments()

    urllib3.disable_warnings()
    all_books = []
    for page_number in range(args.start_page, args.end_page):
        specified_page_with_books = requests.get(
            f'http://tululu.org/l55/{page_number}', verify=False)
        check_tululu_response(specified_page_with_books, 'Found redirect to the index page')

        page_with_fantastic_books = BeautifulSoup(specified_page_with_books.text, 'lxml')
        all_books_on_the_page = page_with_fantastic_books.select("table.d_book div.bookimage a")
        for book in all_books_on_the_page:
            current_book = {}
            book_link = f'http://tululu.org{book.get("href")}'
            book_id = re.findall(r"\d+", book_link)[0]
            link_to_download_the_book = f"http://tululu.org/txt.php?id={book_id}"

            book_page = BeautifulSoup(requests.get(book_link, verify=False).text, 'lxml')
            check_tululu_response(
                requests.get(book_link, verify=False), 'Found redirect to the index page')

            title_and_author = book_page.select_one('table h1').text.split('::')
            title_book = title_and_author[0].strip()
            author_book = title_and_author[1].strip()

            current_book['title'] = title_book
            current_book['author'] = author_book
            if 'txt' in book_page.select_one('table.d_book a img').get('alt'):
                book_image = book_page.select_one('div.bookimage img')['src']
                book_image_url = f'http://tululu.org/{book_image}'

                current_book['comments'] = []
                for comment in book_page.select('div.texts'):
                    current_book['comments'].append(comment.select_one('span.black').text)

                current_book['genres'] = []
                for genre in book_page.select('span.d_book a'):
                    current_book['genres'].append(genre.text)

                try:
                    if not args.skip_imgs:
                        current_book['img_src'] = download_image(
                            url=book_image_url,
                            filename=book_image.split('/')[-1],
                            book_id=book_id)
                except TululuError as e:
                    logging.error(str(e))
                    print(str(e), file=sys.stderr)
                    sys.exit()

                try:
                    if not args.skip_txt:
                        current_book['book_path'] = download_txt(
                            url=link_to_download_the_book,
                            filename=title_book,
                            book_id=book_id)
                except TululuError as e:
                    logging.error(str(e))
                    print(str(e), file=sys.stderr)
                    sys.exit()

            all_books.append(current_book)

    with open(args.json_path, "w", encoding='utf8') as json_file:
        json.dump(all_books, json_file, ensure_ascii=False, sort_keys=True, indent=4)
