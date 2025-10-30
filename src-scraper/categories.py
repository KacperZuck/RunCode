from bs4 import BeautifulSoup
import requests
from urllib.parse import urljoin
from config import BASE_URL

def print_categories(categories):
    for category in categories:
        print(f'Category {category["name"]}')
        for subcategory in category['subcategories']:
            print(f' - {subcategory["name"]} -> {subcategory["url"]}')
            for item in subcategory['items']:
                print(f' -- {item["name"]} -> {item["url"]}')
        print()

def get_categories():
    html_text = requests.get(BASE_URL).text
    soup = BeautifulSoup(html_text, 'lxml')

    menu = soup.find('div', id='menubar-366')
    if not menu:
        print("Nie znaleziono menu!")
        exit()

    categories = []

    for li in menu.find_all('li', class_='e-n-menu-item', recursive=True):
        title = li.find('span', class_='e-n-menu-title-text')
        if not title:
            continue
        category_name = title.get_text(strip=True)
        if category_name == "Blog":
            continue
        main_link = li.find('a', class_="e-link")
        category_url = None
        if main_link and main_link.get('href'):
            category_url = urljoin(BASE_URL, main_link.get('href')).rstrip('/')+'/'

        category = {
            'name': category_name,
            'url': category_url,
            'subcategories': []
        }

        submenu = li.find('div', class_='e-n-menu-content')
        if submenu:
            containers = submenu.select('div.elementor-widget-container')

            last_subcategory = None

            for container in containers:
                heading = container.select_one('.elementor-heading-title')
                icon_list = container.select('.elementor-icon-list-item a')

                if heading:
                    subcategory_name = heading.get_text(strip=True)
                    link_tag = heading.find('a')
                    subcategory_url = None
                    if link_tag and link_tag.get('href'):
                        subcategory_url = urljoin(BASE_URL, link_tag.get('href')).rstrip('/')+'/'

                    last_subcategory ={
                        'name': subcategory_name,
                        'url': subcategory_url,
                        'items': []
                    }
                    category['subcategories'].append(last_subcategory)

                elif icon_list and last_subcategory:
                    for item_link in icon_list:
                        item_name = item_link.get_text(strip=True)
                        item_url = urljoin(BASE_URL, item_link.get('href')).rstrip('/')+'/'
                        last_subcategory['items'].append({
                            'name': item_name,
                            'url': item_url
                        })

        categories.append(category)

    return categories