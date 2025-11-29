import json
import re
import os

def save_json(data, filename):
    results_dir = os.path.join(os.path.dirname(__file__), '..', 'results')
    os.makedirs(results_dir, exist_ok=True)

    filepath = os.path.join(results_dir, filename)

    with open(filepath, 'w', encoding='utf8') as outfile:
        json.dump(data, outfile, ensure_ascii=False, indent=4)

def get_number_of_pages(soup, products_per_page):
    text = soup.find('div', class_='kadence-woo-results-count').text.strip()
    nums = re.findall(r'\d+', text)
    if not nums:
        return 1
    number_of_products = int(nums[-1])
    if int(number_of_products) % products_per_page == 0:
        return int(number_of_products)//products_per_page
    return int(number_of_products)//products_per_page + 1