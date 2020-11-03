import requests
import os
import re
import json
import argparse
from bs4 import BeautifulSoup
from pathvalidate import sanitize_filename
from urllib.parse import urljoin


def download_txt(url, filename, folder='books/'):
    os.makedirs(folder, exist_ok=True)
    book_folder = f'{os.path.join(folder, sanitize_filename(filename))}.txt'
    with open(book_folder, 'wb') as file:
        file.write(requests.get(url).content)
    requests.get(url).raise_for_status()
    return book_folder


def download_image(url, filename, folder='images/'):
    os.makedirs(folder, exist_ok=True)
    book_image_folder = f'{os.path.join(folder, sanitize_filename(filename))}'
    with open(book_image_folder, 'wb') as file:
        file.write(requests.get(url).content)
    requests.get(url).raise_for_status()
    return book_image_folder


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--start_page', default=1, type=int)
    parser.add_argument('--end_page', default=701, type=int)
    parser.add_argument('--dest_folder', default='books_images/')
    parser.add_argument('--json_path', default='all_books.json')
    parser.add_argument('--skip_imgs', action='store_true')
    parser.add_argument('--skip_txt', action='store_true')
    args = parser.parse_args()

    all_books = []
    for page_number in range(args.start_page, args.end_page):
        page_with_fantastic_books = BeautifulSoup(
            requests.get(f'http://tululu.org/l55/{page_number}').text, 'lxml')
        all_cards_book = page_with_fantastic_books.select("table.d_book div.bookimage a")
        for book in all_cards_book:
            current_book = {}
            book_link = urljoin('http://tululu.org', book.get('href'))
            book_id = re.findall(r"\d+", book_link)[0]
            link_to_download_the_book = f"http://tululu.org/txt.php?id={book_id}"
            try:
                book_page = BeautifulSoup(requests.get(book_link).text, 'lxml')
            except requests.exceptions.ConnectionError:
                status_code = "Connection refused"
                continue
            title_and_author = book_page.select_one('table h1').text.split('::')
            title_book = title_and_author[0].strip()
            author_book = title_and_author[1].strip()

            current_book['title'] = title_book
            current_book['author'] = author_book

            if 'txt' in book_page.select_one('table.d_book a img').get('alt'):
                book_image = book_page.select_one('div.bookimage img')['src']
                book_image_url = urljoin('http://tululu.org/', book_image)

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
                            filename=book_image.split('/')[-1])
                    if not args.skip_txt:
                        current_book['book_path'] = download_txt(
                            url=link_to_download_the_book,
                            filename=title_book)
                except requests.exceptions.ConnectionError:
                    status_code = "Connection refused"
                    continue

            all_books.append(current_book)

    with open(args.json_path, "w", encoding='utf8') as json_file:
        json.dump(all_books, json_file, ensure_ascii=False, sort_keys=True, indent=4)
