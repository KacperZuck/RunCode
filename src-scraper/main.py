from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from config import SELENIUM_OPTIONS, BASE_URL, CATEGORIES_FILE, PRODUCTS_FILE
from categories import get_categories
from products import get_products_url, parse_product_page
from utils import save_json

def create_driver():
    options = Options()
    for opt in SELENIUM_OPTIONS:
        if SELENIUM_OPTIONS[opt]:
            options.add_argument(f"--{opt.replace('_', '-')}")
    return webdriver.Chrome(options=options)


def main():
    print("Pobieranie kategorii...")
    categories = get_categories()
    save_json(categories, CATEGORIES_FILE)
    print(f"Kategorie zapisane do {CATEGORIES_FILE}")

    driver = create_driver()
    products = []

    for category in categories:
        if category["subcategories"] == []:
            if category.get("url"):
                links=[]
                print(category["url"])
                get_products_url(category['url'], driver, links)
                print(links)
                for link in links:
                    product = parse_product_page(link, driver, [category['name']])
                    products.append(product)
                    print(product["name"])
                continue
        else:
            for sub in category["subcategories"]:
                if sub["items"] == []:
                    if sub.get("url"):
                        links=[]
                        get_products_url(sub['url'], driver, links)
                        for link in links:
                            product = parse_product_page(link, driver, [category['name'], sub['name']])
                            products.append(product)
                            print(product["name"])
                        continue
                else:
                    for item in sub["items"]:
                        if item.get("url"):
                            links=[]
                            get_products_url(item['url'], driver, links)
                            for link in links:
                                product = parse_product_page(link, driver, [category['name'], sub['name'], item['name']])
                                products.append(product)
                                print(product["name"])


    driver.quit()
    save_json(products, PRODUCTS_FILE)


if __name__ == "__main__":
    main()