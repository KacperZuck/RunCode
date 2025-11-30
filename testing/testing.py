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
ADRESS = "ulica 1"
KOD_POCZTOWY = "11-000"
MIASTO = "Gdansk"

class PrestaShopTest:
    def __init__(self, url):
        chrome_options = webdriver.ChromeOptions()
       # chrome_options.add_argument("--headless")
       # chrome_options.add_argument("--window-size=1920,1080")

        # Inicjalizacja WebDriver (zakładamy, że ChromeDriver jest w PATH lub używamy Service)
        self.driver = webdriver.Chrome(options=chrome_options)
        self.base_url = url
        self.wait = WebDriverWait(self.driver, TIMEOUT)
      #  print("Driver uruchomiony w trybie bezgłowym.")

    def tearDown(self):
        self.driver.quit()
        print("Test zakończony.")

    def _wait_and_click(self, by, value):
        self.wait.until(EC.element_to_be_clickable((by, value))).click()

    def _wait_and_send_keys(self, by, value, keys):
        element = self.wait.until(EC.visibility_of_element_located((by, value)))
        element.send_keys(keys)

    def add_products(self, products):
        start_time = time.time()

        # Przykładowe selektory do list produktów (MUSZĄ BYĆ PRAWIDŁOWE DLA TEMPLATKI)
        category_links = ["?id_category=3&controller=category", "?id_category=9&controller=category"]

        for i in range(products):
            # Losowy wybór kategorii
            category_url = self.base_url + random.choice(category_links)
            self.driver.get(category_url)

            # Wyszukanie wszystkich produktów na stronie
            # PRZYKŁAD SELEKTORA KARTY PRODUKTU:
            product_cards = self.wait.until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".product-miniature"))
            )

            if not product_cards:
                print("Brak produktów w kategorii")
                continue

            # Losowy wybór jednego produktu
            random_product = random.choice(product_cards)

            # 1. Kliknięcie w link do produktu (lub przycisk 'Dodaj do koszyka' jeśli widoczny)
            # OPTYMALNIE: Spróbuj użyć szybkiego przycisku 'Dodaj do koszyka' (jeśli jest bez atrybutów)
            # LUB: Przejdź na stronę produktu, aby manipulować ilością

            # Kliknięcie w link do produktu
            random_product.find_element(By.CSS_SELECTOR, "a.product-thumbnail").click()

            # Zmiana ilości na losową (1 do 5)
            qty = random.randint(1, 3)
            qty_input = self.wait.until(EC.presence_of_element_located((By.ID, "quantity_wanted")))
            qty_input.clear()
            for i in range(qty):
                self._wait_and_click(By.CSS_SELECTOR, ".btn.btn-touchspin.js-touchspin.bootstrap-touchspin-up")

            # 2. Kliknięcie "Dodaj do koszyka"
            # PRZYKŁAD SELEKTORA PRZYCISKU:
            self._wait_and_click(By.CSS_SELECTOR, ".add-to-cart.btn.btn-primary")

            # 3. Poczekaj na pojawienie się modalu (pop-upu) i zamknij go LUB poczekaj na aktualizację koszyka
            # Czekamy na przycisk kontynuacji zakupów w modalu (CSS selector dla zamknięcia pop-upu)
            self._wait_and_click(By.XPATH, "//button[text()='Kontynuuj zakupy']")
            print(f"Prawidłowo dodano: {i} produkt")
        print(f"Dodano 10 produktów. Czas: {time.time() - start_time:.2f}s")

    def search_and_add_random_product(self, search_term="Sukienka"):

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

        PRIVACY_LABEL = "label[for='field-customer_privacy']"
        self._wait_and_click(By.CSS_SELECTOR, PRIVACY_LABEL)
        RODO_LABEL_SELECTOR = "label[for='field-psgdpr']"
        self._wait_and_click(By.CSS_SELECTOR, RODO_LABEL_SELECTOR)

        self._wait_and_click(By.CSS_SELECTOR, ".btn.btn-primary.form-control-submit.float-xs-right")

    def checkout_and_finalize(self, adress, kod_pocztowy, miasto):
        self.driver.get(self.base_url + "?controller=cart&action=show")

        item_rows = self.wait.until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".cart-item"))
        )
        self._wait_and_click(By.CSS_SELECTOR, ".btn.btn-primary")

        carriers = self.wait.until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".delivery-option input[type='radio']"))
        )
        if len(carriers) >= 2:
            random.choice(carriers[0:2]).click()

        self._wait_and_click(By.NAME, "address1", adress)
        self._wait_and_click(By.NAME, "postcode", kod_pocztowy)
        self._wait_and_click(By.NAME, "city", miasto)
        CITY_SELCETOR = "label[for='field-id_country']"
        self._wait_and_click(By.CSS_SELECTOR, CITY_SELCETOR, 14)
        self._wait_and_click(By.NAME, "confirm-addresses")

        self._wait_and_click(By.NAME, "confirmDeliveryOption")

        PAYMENT_SELECTOR = "label[for='field-payment-option']"
        self._wait_and_click(By.ID, PAYMENT_SELECTOR)  # Zakładamy ID = 2 MA BYC PRZY ODBIORZE

        self._wait_and_click(By.ID, "conditions_to_approve[terms-and-conditions]")

        self._wait_and_click(By.ID, "payment-confirmation")

        order_success_message = self.wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#content-wrapper h3"))
        ).text
        assert "Twoje zamówienie zostało potwierdzone" in order_success_message
        print(f"Status zamówienia: {order_success_message}")


if __name__ == "__main__":
    test = PrestaShopTest(BASE_URL)
    EMAIL = f"test_{int(time.time())}@test.com"
    PASSWORD = "Password"

    try:
        start_global_time = time.time()

        test.register_new_account(EMAIL, PASSWORD)
        test.add_products(1)
       # test.search_and_add_random_product("T-shirt")
        #test.remove_3_products_from_cart()
        test.checkout_and_finalize(ADRESS, KOD_POCZTOWY, MIASTO)
        #test.download_invoice()

        end_global_time = time.time()
        total_time = end_global_time - start_global_time

        print(f"\nCZAS WYKONANIA: {total_time:.2f} sekund.")

    except Exception as e:
        print(f"\nBŁĄD PODCZAS WYKONANIA TESTU: {e}")

    #finally:
    #    test.tearDown()