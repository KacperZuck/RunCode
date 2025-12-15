BASE_URL = "https://brooks-running.pl"

# ustawienia Selenium
SELENIUM_OPTIONS = {
    "headless": True,
    "no_sandbox": True,
    "disable_dev_shm_usage": True,
    "disable_gpu": True,
    "window_size=1920,1080": True
}

# timeouty
PAGE_LOAD_TIMEOUT = 20
WAIT_BETWEEN_PAGES = 0.5

# pliki wynikowe
CATEGORIES_FILE = "categories.json"
PRODUCTS_FILE = "products.json"

# liczba produktów na stronę (WooCommerce standard)
PRODUCTS_PER_PAGE = 24