from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from utils import get_number_of_pages
from config import PAGE_LOAD_TIMEOUT, PRODUCTS_PER_PAGE
import time
import re


def get_products_url(category_url, driver, links, i=1):
    driver.get(category_url)
    print(category_url)
    try:
        WebDriverWait(driver, PAGE_LOAD_TIMEOUT).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'woo-archive-btn-text'))
        )
    except:
        print("pusta strona")
        return

    html_text = driver.page_source
    soup = BeautifulSoup(html_text, "lxml")

    pages = get_number_of_pages(soup, PRODUCTS_PER_PAGE)

    products_list = soup.find('ul', class_='woo-archive-btn-text')
    items = products_list.find_all('li')
    for item in items:
        links.append(item.find('a')['href'])

    if pages > i:
        i = i + 1
        if i > 2:
            tmp = category_url.rstrip('/').rsplit('/', 2)[0]
            category_url= tmp + '/'

        category_url += f"page/{i}/"
        get_products_url(category_url, driver, links, i)


def parse_product_page(url, driver, category_hierarchy):
    product = {
        "name": None,
        "url": None,
        "sku": None,
        "price": None,
        "sizes": [],
        "description": None,
        "additional_info": {},
        "category": category_hierarchy,
        "images": []
    }

    driver.get(url)
    time.sleep(0.5)# do poprawy
    html_text = driver.page_source

    soup = BeautifulSoup(html_text, "lxml")

    name_tag = soup.select_one('h1.product_title')
    if not name_tag:
        name_tag = soup.select_one('h2.product_title')
    product['name'] = name_tag.text.strip()

    product['url'] = url

    sku_number = soup.find(string=re.compile(r'SKU:'))
    if sku_number:
        product['sku'] = sku_number.text.strip()

    price_tag = soup.find('p', class_='price')
    if price_tag:
        product['price'] = price_tag.text.strip()

    size_tags = soup.find_all('div', class_='cfvsw-swatches-option cfvsw-label-option')
    for size in size_tags:
        classes = size.get('class', [])
        if 'cfvsw-swatches-disabled' not in classes:
            product['sizes'].append(size.text.strip())

    description_container = soup.find('div', class_="elementor-widget-woocommerce-product-content")
    texts = []
    if description_container:
        for tag in description_container.find_all(['p', 'h2', 'h3', 'li']):
            text = tag.get_text(strip=True)
            if text:
                texts.append(text)
    if texts:
        product['description'] = ' '.join(texts)

    table = soup.find('table', class_="woocommerce-product-attributes shop_attributes")
    if table:
        for row in table.find_all('tr'):
            label_tag=row.find('th')
            value_tag=row.find('td')

            if label_tag and value_tag:
                label=label_tag.text.strip()
                value=value_tag.text.strip()
                product['additional_info'][label]=value

    images=[]
    gallery = soup.find('div', class_='woocommerce-product-gallery__wrapper')
    if gallery:
        for img in gallery.find_all('a', href=True):
            img_src = img.get('href', '').strip()
            if img_src:
                images.append(img_src)

    if images:
        product['images'] = images[:2]

    return product