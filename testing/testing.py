from time import sleep

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import random
from selenium.webdriver.common.keys import Keys

BASE_URL = "http://localhost:8080/index.php"  # Zmień na faktyczny URL
TIMEOUT = 5  # Maksymalny czas oczekiwania na element
ADD_PRODUCTS = 1
SEARCH_PRODUCT = "T-shirt"
ADRESS = "ulica 1"
KOD_POCZTOWY = "11-000"
MIASTO = "Gdansk"

class PrestaShopTest:
    def __init__(self, url):
        chrome_options = webdriver.ChromeOptions()
       # chrome_options.add_argument("--headless")
       # chrome_options.add_argument("--window-size=1920,1080")

        self.driver = webdriver.Chrome(options=chrome_options)
        self.base_url = url
        self.wait = WebDriverWait(self.driver, TIMEOUT)

    def tearDown(self):
        self.driver.quit()
        print("Test zakończony.")

    def _wait_and_click(self, by, value):
        self.wait.until(EC.element_to_be_clickable((by, value))).click()

    def _wait_and_send_keys(self, by, value, keys):
        element = self.wait.until(EC.visibility_of_element_located((by, value)))
        element.send_keys(keys)

    def add_products(self, products):
        category_links = ["?id_category=3&controller=category", "?id_category=9&controller=category"]

        for i in range(products):
            category_url = self.base_url + random.choice(category_links)
            self.driver.get(category_url)

            # Wyszukanie wszystkich produktów na stronie
            product_cards = self.wait.until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".product-miniature"))
            )

            if not product_cards:
                print("Brak produktów w kategorii")
                continue

            random_product = random.choice(product_cards)
            random_product.find_element(By.CSS_SELECTOR, "a.product-thumbnail").click()

            qty = random.randint(1, 4)
            qty_input = self.wait.until(EC.presence_of_element_located((By.ID, "quantity_wanted")))
            qty_input.clear()
            for i in range(qty):
                self._wait_and_click(By.CSS_SELECTOR, ".btn.btn-touchspin.js-touchspin.bootstrap-touchspin-up")

            self._wait_and_click(By.CSS_SELECTOR, ".add-to-cart.btn.btn-primary")

            self._wait_and_click(By.XPATH, "//button[text()='Kontynuuj zakupy']")
            print(f"Prawidłowo dodano: {i} produkt(y) w tej kategorii")
        print(f"Dodano {products} produktów do koszyka")

    def search_and_add_random_product(self, search_term):

        category_url = self.base_url
        self.driver.get(category_url)
        search_input = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".ui-autocomplete-input")))
        search_input.send_keys(search_term)
        search_input.send_keys(Keys.ENTER)

        product_results = self.wait.until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".product-miniature"))
        )

        if product_results:
            random_product_card = random.choice(product_results)
            random_product_card.find_element(By.CSS_SELECTOR, "a.product-thumbnail").click()

            self._wait_and_click(By.CSS_SELECTOR, ".add-to-cart.btn.btn-primary")
            self._wait_and_click(By.XPATH, "//button[text()='Kontynuuj zakupy']")  # Zamknięcie modalu
        else:
            print(f"Brak wyników dla frazy: {search_term}")

    def remove_3_products_from_cart(self):
        self.driver.get(self.base_url + "?controller=cart&action=show")

        item_rows = self.wait.until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".cart-item"))
        )

        if len(item_rows) >= 3:
            for i in range(3):
                self._wait_and_click(By.CSS_SELECTOR, ".cart-item:nth-child(1) .remove-from-cart")
                time.sleep(
                    1)  # Lepsze byłoby oczekiwanie na zniknięcie elementu, ale time.sleep(1) często wystarcza w tym przypadku.
        else:
            print("W koszyku jest mniej niż 3 produkty. Pomijam usuwanie.")

    def register_new_account(self, email, password):
        self.driver.get(self.base_url + "?controller=authentication&back=my-account")
        self._wait_and_click(By.CSS_SELECTOR, ".no-account")

        GENDER_MAN_SELECTOR = "label[for='field-id_gender-1']"
        self._wait_and_click(By.CSS_SELECTOR, GENDER_MAN_SELECTOR)

        self._wait_and_send_keys(By.NAME, "firstname", "Jan")
        self._wait_and_send_keys(By.NAME, "lastname", "Testowy")
        self._wait_and_send_keys(By.NAME, "email", email)
        self._wait_and_send_keys(By.NAME, "password", password)

        checkbox = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[name='customer_privacy']"))
        )
        self.driver.execute_script("""
            arguments[0].checked = true;
            arguments[0].dispatchEvent(new Event('change', {bubbles: true}));
            arguments[0].dispatchEvent(new Event('input', {bubbles: true}));
        """, checkbox)

        try:
            psg = WebDriverWait(self.driver, 3).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[name='psgdpr']"))
            )
            self.driver.execute_script(
                "arguments[0].checked = true; arguments[0].dispatchEvent(new Event('change', {bubbles:true}));", psg)
        except Exception:
            pass

        self._wait_and_click(By.CSS_SELECTOR, ".btn.btn-primary.form-control-submit.float-xs-right")

    def checkout_and_finalize(self, adress, kod_pocztowy, miasto):
        self.driver.get(self.base_url + "?controller=cart&action=show")

        item_rows = self.wait.until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".cart-item"))
        )
        self._wait_and_click(By.CSS_SELECTOR, ".btn.btn-primary")

        self._wait_and_send_keys(By.ID, "field-address1", adress)
        self._wait_and_send_keys(By.NAME, "postcode", kod_pocztowy)
        self._wait_and_send_keys(By.NAME, "city", miasto)
        self._wait_and_click(By.NAME, "confirm-addresses")

        self._wait_and_click(By.NAME, "confirmDeliveryOption")  # sposob dostawy, wiec skip

        PAYMENT_OPTION = "label[for='payment-option-1']"
        self._wait_and_click(By.CSS_SELECTOR, PAYMENT_OPTION)

        checkbox = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[name='conditions_to_approve[terms-and-conditions]']"))
        )

        self.driver.execute_script("""
                    arguments[0].checked = true;
                    arguments[0].dispatchEvent(new Event('change', {bubbles: true}));
                    arguments[0].dispatchEvent(new Event('input', {bubbles: true}));
                """, checkbox)

        self._wait_and_click(By.CSS_SELECTOR, ".btn.btn-primary.center-block")
        print(f"Twoje zamówienie zostało potwierdzone")

    def download_invoice(self):
        self.driver.get(self.base_url + "?controller=history")

        invoice_link = self.wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, ".order-actions .btn-link"))   # clas name dla pobrania faktury jak juz bedzie oddana
        )


        invoice_link.click()
        print("Faktura VAT została pobrana.") # Jesli bedzie dodana w prestashop



if __name__ == "__main__":
    test = PrestaShopTest(BASE_URL)
    EMAIL = f"test_{int(time.time())}@test.com"
    PASSWORD = "Password"

    try:
        start_global_time = time.time()

        test.register_new_account(EMAIL, PASSWORD)
        test.add_products(ADD_PRODUCTS)
        test.search_and_add_random_product(SEARCH_PRODUCT)
        test.remove_3_products_from_cart()
        test.checkout_and_finalize(ADRESS, KOD_POCZTOWY, MIASTO)
        #test.download_invoice()

        end_global_time = time.time()
        total_time = end_global_time - start_global_time

        print(f"\nCZAS WYKONANIA: {total_time:.2f} sekund.")

    except Exception as e:
        print(f"\nBŁĄD PODCZAS WYKONANIA TESTU: {e}")
        time.sleep(1000)
    #finally:
    #    test.tearDown()