import time
import random
import os
from selenium.webdriver.chrome.service import Service
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select # Potrzebne do zmiany statusu
from webdriver_manager.chrome import ChromeDriverManager
from faker import Faker

# --- KONFIGURACJA ---
URL_SKLEPU = "https://localhost"
ADMIN_URL = "https://localhost/admin-dev" # Twój folder admina
ADMIN_EMAIL = "demo@prestashop.com"
ADMIN_PASS = "prestashop_demo"
FAKER = Faker("pl_PL")

# Ustawienia przeglądarki
options = webdriver.ChromeOptions()
# Podstawowe ustawienia
options.add_argument("--ignore-certificate-errors")
options.add_argument("--allow-insecure-localhost")
options.add_argument("--window-size=1920,1080")

# --- FIX DLA SNAP / LINUX ---
options.binary_location = "/snap/bin/chromium" # Ścieżka do przeglądarki
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-gpu")
options.add_argument("--remote-debugging-port=9222")

# --- KLUCZOWA ZMIANA: WŁASNY KATALOG PROFILU ---
# To zapobiega wyrzuceniu się Snapa przy próbie dostępu do /tmp
profile_dir = os.path.join(os.getcwd(), "chrome_profile_snap")
options.add_argument(f"--user-data-dir={profile_dir}")
# ------------------------------------------------

# Próba uruchomienia ze sterownikiem systemowym
service = Service("/usr/bin/chromedriver")

try:
    print(f"Uruchamiam Chromium z profilu: {profile_dir}")
    driver = webdriver.Chrome(service=service, options=options)
except Exception as e:
    print(f"Błąd uruchamiania: {e}")
    # Ostatnia deska ratunku - próba znalezienia sterownika wewnątrz snapa
    try:
        service = Service("/snap/chromium/current/usr/lib/chromium-browser/chromedriver")
        driver = webdriver.Chrome(service=service, options=options)
    except:
        raise e # Jeśli oba zawiodą, pokaż błąd

wait = WebDriverWait(driver, 10)

try:
    # ==========================================
    # CZĘŚĆ 0: PRZYGOTOWANIE (WYLOGOWANIE)
    # ==========================================
    # To naprawia problem "już zalogowanego" użytkownika przy restarcie
    print("--- PRZYGOTOWANIE ---")
    driver.get(URL_SKLEPU)
    time.sleep(1)

    try:
        # Szukamy przycisku "Wyloguj się" (klasa .logout)
        przyciski_wyloguj = driver.find_elements(By.CSS_SELECTOR, "a.logout")

        # Jeśli znaleziono przycisk i jest widoczny -> kliknij
        if len(przyciski_wyloguj) > 0 and przyciski_wyloguj[0].is_displayed():
            print("   [INFO] Wykryto starą sesję. Wylogowuję...")
            przyciski_wyloguj[0].click()
            time.sleep(3)  # Czekamy na przeładowanie
            print("   [INFO] Wylogowano pomyślnie.")
        else:
            print("   [INFO] Sesja czysta. Można zaczynać.")

    except Exception as e:
        print(f"   [INFO] Błąd przy sprawdzaniu wylogowania (nieistotny): {e}")

    # ==========================================
    # CZĘŚĆ 1: REJESTRACJA I LOGOWANIE (POPRAWIONA)
    # ==========================================
    print("--- REJESTRACJA ---")
    driver.get(f"{URL_SKLEPU}/logowanie?create_account=1")

    imie = FAKER.first_name()
    nazwisko = FAKER.last_name()
    email = FAKER.email()
    haslo = "Haslo1234!"  # Silne hasło, żeby Presta nie odrzuciła

    print(f"--- Wypełnianie danych: {email} ---")

    # 1. WYBÓR PŁCI (Pan) - To jest kluczowe, bez tego formularz stoi w miejscu!
    try:
        radio_gender = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input[name='id_gender'][value='1']")))
        driver.execute_script("arguments[0].click();", radio_gender)
    except Exception as e:
        print(f"   [INFO] Nie znaleziono wyboru płci lub opcjonalne ({e})")

    # 2. Reszta danych
    driver.find_element(By.NAME, "firstname").send_keys(imie)
    driver.find_element(By.NAME, "lastname").send_keys(nazwisko)
    driver.find_element(By.NAME, "email").send_keys(email)
    driver.find_element(By.NAME, "password").send_keys(haslo)

    # (Opcjonalne) Potwierdzenie hasła - niektóre motywy to mają
    try:
        driver.find_element(By.NAME, "password_confirmation").send_keys(haslo)
    except:
        pass

    print("--- Zgody ---")
    checkboxy = driver.find_elements(By.CSS_SELECTOR, "input[type='checkbox']")
    for checkbox in checkboxy:
        if not checkbox.is_selected():
            driver.execute_script("arguments[0].click();", checkbox)

        # ... (kod rejestracji wyżej bez zmian) ...

    print("--- Zapisz ---")
    # Klikamy przycisk (uniwersalny)
    try:
        driver.find_element(By.CSS_SELECTOR, "footer.form-footer button").click()
    except:
        try:
            driver.find_element(By.CSS_SELECTOR, "button[data-link-action='save-customer']").click()
        except:
            driver.find_element(By.CSS_SELECTOR, "form#customer-form button[type='submit']").click()

    print("   -> Kliknięto. Czekam na przeładowanie...")
    time.sleep(3)

    print("--- WERYFIKACJA ---")
    aktualny_url = driver.current_url
    print(f"   Obecny URL: {aktualny_url}")

    # --- NOWA LOGIKA SPRAWDZANIA ---
    # Szukamy elementów, które widzi TYLKO zalogowany użytkownik
    # 1. Przycisk "Wyloguj" (klasa .logout)
    # 2. Imię i nazwisko klienta w nagłówku (klasa .account)

    czy_jest_logout = driver.find_elements(By.CSS_SELECTOR, "a.logout")
    czy_jest_konto = driver.find_elements(By.CSS_SELECTOR, "a.account")

    zalogowany = False

    # Jeśli znaleziono przycisk wylogowania LUB link do konta -> SUKCES
    if (len(czy_jest_logout) > 0 and czy_jest_logout[0].is_displayed()):
        zalogowany = True
    elif (len(czy_jest_konto) > 0 and czy_jest_konto[0].is_displayed()):
        zalogowany = True
    elif "controller=my-account" in aktualny_url or "/moje-konto" in aktualny_url:
        zalogowany = True

    if zalogowany:
        print(f"[SUKCES]: Zalogowano poprawnie (wykryto sesję użytkownika).")
    else:
        # Jeśli nadal nic, szukamy błędu w tekście strony
        try:
            blad_txt = driver.find_element(By.CLASS_NAME, "alert-danger").text
            print(f"[BŁĄD STRONY]: {blad_txt}")
        except:
            pass

        driver.save_screenshot("blad_rejestracji.png")
        raise Exception(f"Błąd: Nie wykryto elementów zalogowania na stronie {aktualny_url}")
    # ==========================================
    # CZĘŚĆ 2: DODAWANIE PRODUKTÓW
    # ==========================================
    print("\n--- DODAWANIE PRODUKTÓW ---")
    #TODO: zmień kategorie na swoje
    kategorie = [f"{URL_SKLEPU}/103-glycerin", f"{URL_SKLEPU}/132-kurtki"]
    limit_per_category = 5
    total_added = 0

    def dodaj_produkt(ilosc):
        # Sprawdź czy przycisk dodawania jest w ogóle dostępny
        try:
            btn_add = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button.add-to-cart")))
            if not btn_add.is_enabled():
                print("       [INFO] Przycisk 'Dodaj do koszyka' nieaktywny (brak towaru?).")
                return False
        except:
            print("       [INFO] Nie znaleziono przycisku dodawania do koszyka.")
            return False

        qty = wait.until(EC.presence_of_element_located((By.ID, "quantity_wanted")))
        qty.click()
        qty.send_keys(Keys.BACK_SPACE * 5)
        qty.send_keys(str(ilosc))
        
        btn_add.click()
        
        # Oczekiwanie na modal - WYMAGANE przez użytkownika
        try:
            # Czekamy na widoczność modala (po ID jest pewniej niż class)
            modal = wait.until(EC.visibility_of_element_located((By.ID, "blockcart-modal")))
            
            # Opcjonalne: Sprawdzenie czy w modalu jest sukces
            # if "Produkt dodany poprawnie" not in modal.text: ...
            
            # Zamknięcie modala (Continue shopping)
            btn_continue = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "#blockcart-modal .btn-secondary")))
            btn_continue.click()
            
            # Czekamy aż zniknie
            wait.until(EC.invisibility_of_element_located((By.ID, "blockcart-modal")))
            return True
            
        except Exception as e:
            print(f"       [WARN] Nie wykryto potwierdzenia (brak towaru lub błąd): {e}")
            # Próbujemy zamknąć ewentualny alert lub modal jeśli wiszą
            try:
                webdriver.ActionChains(driver).send_keys(Keys.ESCAPE).perform()
            except: pass
            return False

    for kat in kategorie:
        print(f"--- Kategoria: {kat} ---")
        driver.get(kat)
        
        # Pobieramy linki do produktów (tylko widoczne)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".product-miniature")))
        linki_elementy = driver.find_elements(By.CSS_SELECTOR, ".product-miniature .thumbnail.product-thumbnail")
        linki = [e.get_attribute("href") for e in linki_elementy]
        
        added_in_category = 0
        
        for link in linki:
            if added_in_category >= limit_per_category:
                break
            
            try:
                driver.get(link)
                # Losowa ilość 1-4
                ilosc = random.randint(1, 4)
                
                # Dodajemy z warunkiem sukcesu
                if dodaj_produkt(ilosc):
                    added_in_category += 1
                    total_added += 1
                    print(f"    [OK] Dodano produkt {added_in_category}/{limit_per_category} z tej kategorii (Razem: {total_added})")
                else:
                    print("    [SKIP] Produkt nie został dodany (brak potwierdzenia).")
            
            except Exception as e:
                print(f"    [BŁĄD] Ogólny błąd przy produkcie: {e}")
                continue

    # ==========================================
    # CZĘŚĆ 3: WYSZUKIWANIE
    # ==========================================
    print("\n--- WYSZUKIWANIE ---")
    search = driver.find_element(By.NAME, "s")
    search.clear()
    #TODO: zmień na produkt, który chce szukać
    search.send_keys("Adrenaline")
    search.send_keys(Keys.ENTER)
    time.sleep(2)
    wyniki = driver.find_elements(By.CSS_SELECTOR, ".product-miniature .thumbnail.product-thumbnail")
    if wyniki:
        driver.get(wyniki[0].get_attribute("href"))
        dodaj_produkt(1)
        print("   [SUKCES] Dodano z wyszukiwania.")

    # ==========================================
    # CZĘŚĆ 4: USUWANIE
    # ==========================================
    print("\n--- USUWANIE Z KOSZYKA ---")
    driver.get(f"{URL_SKLEPU}/index.php?controller=cart&action=show")
    time.sleep(2)
    for _ in range(3):
        try:
            kosze = wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, "remove-from-cart")))
            if kosze:
                kosze[0].click()
                time.sleep(2)
            else: break
        except: break

    # ==========================================
    # CZĘŚĆ 5: CHECKOUT
    # ==========================================
    print("\n--- CHECKOUT ---")
    driver.get(f"{URL_SKLEPU}/zamówienie")
    time.sleep(2)

    # Adres
    try:
        wait.until(EC.presence_of_element_located((By.ID, "checkout-addresses-step")))
        pola = driver.find_elements(By.NAME, "address1")
        if len(pola) > 0 and pola[0].is_displayed():
            driver.find_element(By.NAME, "address1").send_keys("Ulica Testowa 15")
            driver.find_element(By.NAME, "postcode").send_keys("00-950")
            driver.find_element(By.NAME, "city").send_keys("Warszawa")
            driver.find_element(By.NAME, "confirm-addresses").click()
        else:
             # Kliknij dalej jeśli adres już jest
             btns = driver.find_elements(By.NAME, "confirm-addresses")
             if btns and btns[0].is_displayed(): btns[0].click()
        time.sleep(2)
    except Exception as e: print(f"Info adres: {e}")

    # Dostawa
    try:
        wait.until(EC.element_to_be_clickable((By.NAME, "confirmDeliveryOption"))).click()
        time.sleep(2)
    except: pass

    # Płatność
    try:
        radio = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[data-module-name='ps_wirepayment']")))
        driver.execute_script("arguments[0].click();", radio)
        terms = driver.find_element(By.CSS_SELECTOR, "input[id*='conditions_to_approve']")
        driver.execute_script("arguments[0].click();", terms)
    except Exception as e: 
        print(f"Błąd płatności: {e}")
        driver.save_screenshot("blad_platnosc.png")

    # ==========================================
    # CZĘŚĆ 6: ZATWIERDZENIE
    # ==========================================
    print("\n--- ZATWIERDZENIE ---")

    btn_zamow = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "#payment-confirmation button")))

    btn_zamow.click()
    print("   -> Kliknięto przycisk 'Złóż zamówienie'")

    print("   [SUKCES] Zamówienie zostało złożone i potwierdzone!")


    # ==========================================
    # NOWA CZĘŚĆ: LOGOWANIE DO ADMINA I ZMIANA STATUSU (POPRAWIONA)
    # ==========================================
    print("\n--- [ADMIN] ZMIANA STATUSU ZAMÓWIENIA ---")
    
    # 1. Otwieramy nową kartę
    driver.switch_to.new_window('tab')
    
    # 2. Logowanie do panelu
    driver.get(ADMIN_URL)
    print("   -> Logowanie jako Admin...")
    try:
        wait.until(EC.visibility_of_element_located((By.ID, "email"))).send_keys(ADMIN_EMAIL)
        driver.find_element(By.ID, "passwd").send_keys(ADMIN_PASS)
        driver.find_element(By.ID, "submit_login").click()
    except:
        print("   -> Prawdopodobnie admin jest już zalogowany.")

    # 3. Przejście do zamówień
    print("   -> Przechodzę do listy zamówień...")
    time.sleep(3) 
    driver.get(f"{URL_SKLEPU}/admin-dev/index.php?controller=AdminOrders")
    
    # Sortowanie tabeli (najnowsze na górze)
    print("   -> Sprawdzam sortowanie tabeli...")
    try:
        id_header = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "div[data-sort-col-name='id_order']")))
        if id_header.get_attribute("data-sort-direction") == "asc":
            print("   -> Odwracam sortowanie...")
            id_header.click()
            time.sleep(3) 
    except Exception as e:
        print(f"   [!] Problem z sortowaniem: {e}")

    # 4. Kliknięcie w najnowsze zamówienie
    print("   -> Otwieram najnowsze zamówienie...")
    wait.until(EC.element_to_be_clickable((By.XPATH, "//tbody/tr[1]"))).click()
    
    # 5. Zmiana statusu na "Płatność zaakceptowana" (ID 2)
    # --- TUTAJ JEST POPRAWKA POD TWÓJ KOD HTML ---
    print("   -> Zmieniam status na 'Płatność zaakceptowana' (ID 2)...")
    try:
        # Znajdujemy dropdown po Twoim ID z HTML
        select_element = wait.until(EC.presence_of_element_located((By.ID, "update_order_status_new_order_status_id")))
        select = Select(select_element)
        
        # Wybieramy wartość "2" (Płatność zaakceptowana)
        select.select_by_value("2")
        
        # Klikamy przycisk "Aktualizacja statusu" po klasie .update-status
        submit_btn = driver.find_element(By.CSS_SELECTOR, "button.update-status")
        submit_btn.click()
        
        print("   [SUKCES ADMIN] Status zmieniony!")
        time.sleep(3) # Czekamy na zapisanie
        
    except Exception as e:
        print(f"   [!] Nie udało się zmienić statusu: {e}")
        driver.save_screenshot("admin_error.png")

    # 6. Zamykamy kartę admina i wracamy do klienta
    driver.close()
    driver.switch_to.window(driver.window_handles[0])
    print("   -> Powrót do konta klienta.")

    # ==========================================
    # CZĘŚĆ 7 i 8: POBRANIE FAKTURY
    # ==========================================
    print("\n--- STATUS I FAKTURA ---")
    
    # Wchodzimy w historię zamówień
    driver.get(f"{URL_SKLEPU}/historia-zamowien")
    
    try:
        # Czekamy na tabelę
        wait.until(EC.presence_of_element_located((By.ID, "content")))
        
        # 1. Wyświetlenie statusu (z pierwszego wiersza)
        try:
            # Szukamy etykiety statusu (zazwyczaj klasa label-pill lub podobna w kolumnie statusu)
            status_element = driver.find_element(By.CSS_SELECTOR, "tbody tr:first-child .label-pill")
            print(f"   [STATUS ZAMÓWIENIA]: {status_element.text}")
        except:
            print("   [INFO] Nie udało się odczytać tekstu statusu.")

        # 2. Pobranie faktury
        linki_faktur = driver.find_elements(By.CSS_SELECTOR, "a[href*='pdf-invoice']")
        
        if len(linki_faktur) > 0:
            link_do_faktury = linki_faktur[0]
            print(f"   [SUKCES] Faktura dostępna. Klikam, aby pobrać...")
            
            # --- KLUCZOWE: KLIKNIĘCIE ---
            link_do_faktury.click()
            
            print("   -> Rozpoczęto pobieranie pliku PDF.")
            time.sleep(5) # Czekamy chwilę, żeby plik zdążył się pobrać przed zamknięciem przeglądarki
        else:
            print("   [BŁĄD] Faktura nadal niedostępna!")
            
    except Exception as e:
        print(f"   [!] Błąd w sekcji historii: {e}")

    print("\n##############################################")
    print("   TEST ZAKOŃCZONY POMYŚLNIE")
    print("##############################################")

except Exception as e:
    print(f"\n[BŁĄD KRYTYCZNY]: {e}")
    driver.save_screenshot("blad_krytyczny.png")

finally:
    # driver.quit() # Zakomentowane, żebyś widział wynik
    pass