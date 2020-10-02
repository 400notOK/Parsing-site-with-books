import requests
import os
import re
import json
import argparse
from bs4 import BeautifulSoup
from pathvalidate import sanitize_filename
from urllib.parse import urljoin


parser = argparse.ArgumentParser()
parser.add_argument('--start_page', default=1, type=int)
parser.add_argument('--end_page', default=701, type=int)
parser.add_argument('--dest_folder', default='books_images/')
parser.add_argument('--json_path', default='all_books.json')
parser.add_argument('--skip_imgs', action='store_true')
parser.add_argument('--skip_txt', action='store_true')
args = parser.parse_args()


def download_txt(url, filename, folder='books/'):
    if not os.path.exists(folder):
        os.makedirs(folder, exist_ok=True)
    book_folder = f'{os.path.join(folder, sanitize_filename(filename))}.txt'
    with open(book_folder, 'wb') as file:
        file.write(requests.get(url).content)
    return book_folder


def download_image(url, filename, folder='images/'):
    if not os.path.exists(folder):
        os.makedirs(folder, exist_ok=True)
    book_image_folder = f'{os.path.join(folder, sanitize_filename(filename))}'
    with open(book_image_folder, 'wb') as file:
        file.write(requests.get(url).content)
    return book_image_folder


all_books = []
if __name__ == '__main__':
    for i in range(args.start_page, args.end_page):
        current_book = {}
        page_fantastic_books = BeautifulSoup(requests.get(f'http://tululu.org/l55/{i}').text, 'lxml')
        book_all_cards = page_fantastic_books.select("table.d_book div.bookimage a")
        for book in book_all_cards:
            book_title_author = urljoin('http://tululu.org', book.get('href'))
            book_id = re.findall(r"\d+", book_title_author)[0]
            book_download_txt = f"http://tululu.org/txt.php?id={book_id}"
            print(book_title_author)
            try:
                book_page = BeautifulSoup(requests.get(book_title_author).text, 'lxml')
            except requests.exceptions.ConnectionError:
                status_code = "Connection refused"
                continue
            title_and_author = book_page.select_one('table h1').text.split('::')

            if len(title_and_author) is 2 and 'txt' in book_page.select_one('table.d_book a img').get('alt'):
                book_image = book_page.select_one('div.bookimage img')['src']
                book_image_url = urljoin('http://tululu.org/', book_image)

                current_book['comments'] = []
                for comment in book_page.select('div.texts'):
                    current_book['comments'].append(comment.select_one('span.black').text)

                current_book['genres'] = []
                for genre in book_page.select('span.d_book a'):
                    current_book['genres'].append(genre.text)

                current_book['title'] = book_title_author
                current_book['author'] = title_and_author[1].strip()
                try:
                    if not args.skip_imgs:
                        print(True)
                        current_book['img_src'] = download_image(
                            url=book_image_url, filename=book_image.split('/')[-1], folder=args.dest_folder)
                    if not args.skip_txt:
                        print(True)
                        current_book['book_path'] = download_txt(
                            url=book_download_txt, filename=title_and_author[0].strip(), folder=args.dest_folder)
                except requests.exceptions.ConnectionError:
                    status_code = "Connection refused"
                    continue

                all_books.append(current_book)

    print(len(all_books))
    with open("all_books.json", "w", encoding='utf8') as fout:
        json.dump(all_books, fout, ensure_ascii=False, sort_keys=True, indent=4)
