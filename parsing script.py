import requests
import os
from bs4 import BeautifulSoup
from pathvalidate import sanitize_filename
from urllib.parse import urljoin


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


for i in range(1, 10):
    book_title_author = f"http://tululu.org/b{i}/"
    book_download_txt = f"http://tululu.org/txt.php?id={i}"
    soup = BeautifulSoup(requests.get(book_title_author).text, 'lxml')
    title_and_author = soup.find('table').find('h1').text.split('::')

    if len(title_and_author) is 2 and 'скачать txt' in soup.find(class_='d_book').text:
        book_image = soup.find(class_='bookimage').find('img')['src']
        book_image_url = urljoin('http://tululu.org/', book_image)
        book_comments = soup.find_all(class_='texts')
        for comment in book_comments:
            print(comment.find(class_='black').text)

        # download_image(url=book_image_url, filename=book_image.split('/')[-1])
        # download_txt(url=book_download_txt, filename=f'{i}. {title_and_author[0].strip()}')
