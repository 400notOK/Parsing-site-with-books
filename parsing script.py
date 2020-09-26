import requests
import os
from bs4 import BeautifulSoup
from pathvalidate import sanitize_filename


def download_txt(url, filename, folder='books/'):
    if not os.path.exists(folder):
        os.makedirs(folder, exist_ok=True)
    book_folder = f'{os.path.join(folder, sanitize_filename(filename))}.txt'
    with open(book_folder, 'wb') as file:
        file.write(requests.get(url).content)
    return book_folder


for i in range(1, 10):
    book_title_author = f"http://tululu.org/b{i}/"
    book_download_txt = f"http://tululu.org/txt.php?id={i}"
    soup = BeautifulSoup(requests.get(book_title_author).text, 'lxml')
    title_and_author = soup.find('table').find('h1').text.split('::')

    if len(title_and_author) is 2:
        download_txt(book_download_txt, f'{i}. {title_and_author[0].strip()}')
