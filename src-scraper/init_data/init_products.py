import requests
import json
import os
import re
import random
from dotenv import load_dotenv
from unidecode import unidecode
import time
import xml.etree.ElementTree as ET

# --- KONFIGURACJA ---
load_dotenv()

API_KEY = os.getenv("API_KEY")
API_URL = os.getenv("API_URL")
if API_URL and API_URL.endswith('/'):
    API_URL = API_URL[:-1]

ID_LANG = 1
SOURCE_FILE = '../../results/products.json'
HEADERS = {'Content-Type': 'application/xml'}
VAT_RATE = 1.23 

# Cache Kategorii
CATEGORY_MAP = {} 

# --- FUNKCJE POMOCNICZE ---

def clean_link(link):
    if not link: return "produkt"
    link = unidecode(link).lower()
    link = re.sub(r'[^a-z0-9\-]+', '-', link)
    return link.strip('-')

def clean_price(price_str):
    if not price_str: return 0.0
    if isinstance(price_str, (float, int)): return float(price_str)
    
    text = str(price_str)
    text = text.replace('–', '-').replace('—', '-')
    if '-' in text: text = text.split('-')[0]

    import re
    matches = re.findall(r'(\d+(?:[\.,]\d+)?)', text)
    if not matches: return 0.0
    
    clean = matches[-1].replace(',', '.')
    if clean.count('.') > 1:
        clean = clean.replace('.', '', clean.count('.') - 1)
        
    try:
        val = float(clean)
        if val > 5000: val = val / 100 
        return val
    except ValueError:
        return 0.0

def clean_weight(weight_str):
    fallback_weight = round(random.uniform(0.2, 0.8), 3)
    if not weight_str: return fallback_weight
    text = str(weight_str).lower().replace(' ', '').replace(',', '.')
    try:
        if 'kg' in text:
            text = text.replace('kg', '')
            val = float(text)
        else:
            text = text.replace('g', '')
            val = float(text)
            if val > 10: val = val / 1000.0
            
        if val <= 0.05: return fallback_weight
        return val
    except ValueError:
        return fallback_weight

def clean_sku(sku_str):
    if not sku_str: return ""
    return sku_str.replace('SKU:', '').strip()

# --- LOGIKA KATEGORII ---

def build_category_map():
    print("Pobieram hierarchiczną mapę kategorii...")
    try:
        r = requests.get(f"{API_URL}/categories?display=full", auth=(API_KEY, ''))
        if r.status_code == 200:
            root = ET.fromstring(r.content)
            for cat in root.findall(".//category"):
                cat_id = cat.find('id').text
                
                parent_node = cat.find('id_parent')
                parent_id = int(parent_node.text) if parent_node is not None else 0
                
                name_node = cat.find(f".//name/language[@id='{ID_LANG}']")
                if name_node is None: name_node = cat.find(".//name/language")
                
                if name_node is not None and name_node.text:
                    name_key = name_node.text.strip().lower()
                    if name_key not in CATEGORY_MAP:
                        CATEGORY_MAP[name_key] = []
                    CATEGORY_MAP[name_key].append({'id': int(cat_id), 'parent': parent_id})
            
            print(f"Załadowano mapę (wpisów: {sum(len(v) for v in CATEGORY_MAP.values())})")
    except Exception as e:
        print(f"Błąd mapy: {e}")

def resolve_product_categories(list_of_paths):
    if not list_of_paths:
        return {'default_id': 2, 'all_ids': [2]}

    collected_ids = {2}
    potential_default_ids = []

    for path in list_of_paths:
        current_parent_id = 2 
        path_valid = True
        
        for cat_name in path:
            name_key = cat_name.strip().lower()
            candidates = CATEGORY_MAP.get(name_key, [])
            match = None
            
            for cand in candidates:
                if cand['parent'] == current_parent_id:
                    match = cand
                    break
            
            if match:
                found_id = match['id']
                collected_ids.add(found_id)
                current_parent_id = found_id
            else:
                path_valid = False
                break
        
        if path_valid and current_parent_id != 2:
            potential_default_ids.append(current_parent_id)

    default_id = potential_default_ids[-1] if potential_default_ids else 2
    return {'default_id': default_id, 'all_ids': list(collected_ids)}

# --- ATRIBUTES & FEATURES ---

def get_or_create_attribute_group(group_name):
    clean = group_name.strip()
    params = {'filter[name]': f'[{clean}]', 'display': '[id]', 'limit': 1}
    try:
        r = requests.get(f"{API_URL}/product_options", auth=(API_KEY, ''), params=params)
        node = ET.fromstring(r.content).find('.//product_option/id')
        if node is not None: return node.text
    except: pass

    xml = f"""<prestashop xmlns:xlink="http://www.w3.org/1999/xlink">
        <product_option>
            <is_color_group>0</is_color_group>
            <group_type>select</group_type>
            <name><language id="{ID_LANG}">{clean}</language></name>
            <public_name><language id="{ID_LANG}">{clean}</language></public_name>
        </product_option></prestashop>"""
    r = requests.post(f"{API_URL}/product_options", auth=(API_KEY, ''), headers=HEADERS, data=xml.encode('utf-8'))
    if r.status_code in [200, 201]: return ET.fromstring(r.content).findtext('.//id')
    return None

def get_or_create_attribute_value(group_id, value_name):
    params = {'filter[id_attribute_group]': f'[{group_id}]', 'display': 'full'} 
    try:
        r = requests.get(f"{API_URL}/product_option_values", auth=(API_KEY, ''), params=params)
        if r.status_code == 200:
            for val in ET.fromstring(r.content).findall('.//product_option_value'):
                name_node = val.find(f'.//name/language[@id="{ID_LANG}"]')
                if name_node is None: name_node = val.find('.//name/language')
                if name_node is not None and name_node.text == str(value_name):
                    return val.find('id').text
    except: pass

    xml = f"""<prestashop xmlns:xlink="http://www.w3.org/1999/xlink">
        <product_option_value>
            <id_attribute_group>{group_id}</id_attribute_group>
            <name><language id="{ID_LANG}">{value_name}</language></name>
        </product_option_value></prestashop>"""
    r = requests.post(f"{API_URL}/product_option_values", auth=(API_KEY, ''), headers=HEADERS, data=xml.encode('utf-8'))
    if r.status_code in [200, 201]: return ET.fromstring(r.content).findtext('.//id')
    return None

def add_feature(feature_name, feature_value):
    clean = feature_name.strip()
    params = {'filter[name]': f'[{clean}]', 'display': '[id]', 'limit': 1}
    fid = None
    try:
        r = requests.get(f"{API_URL}/product_features", auth=(API_KEY, ''), params=params)
        node = ET.fromstring(r.content).find('.//product_feature/id')
        if node is not None: fid = node.text
    except: pass

    if not fid:
        xml = f"""<prestashop><product_feature><name><language id="{ID_LANG}">{clean}</language></name></product_feature></prestashop>"""
        r = requests.post(f"{API_URL}/product_features", auth=(API_KEY, ''), headers=HEADERS, data=xml.encode('utf-8'))
        if r.status_code in [200, 201]: fid = ET.fromstring(r.content).findtext('.//id')
        else: return None
    
    xml_v = f"""<prestashop><product_feature_value>
        <id_feature>{fid}</id_feature>
        <value><language id="{ID_LANG}">{feature_value}</language></value>
        <custom>1</custom></product_feature_value></prestashop>"""
    r = requests.post(f"{API_URL}/product_feature_values", auth=(API_KEY, ''), headers=HEADERS, data=xml_v.encode('utf-8'))
    if r.status_code in [200, 201]: return {'id': fid, 'id_feature_value': ET.fromstring(r.content).findtext('.//id')}
    return None

# --- STOCK & IMAGES ---

def update_stock_available(product_id, attribute_id, quantity):
    url = f"{API_URL}/stock_availables?display=full&filter[id_product]={product_id}&filter[id_product_attribute]={attribute_id}"
    try:
        r = requests.get(url, auth=(API_KEY, ''))
        root = ET.fromstring(r.content)
        stock_node = root.find('.//stock_available')
        
        if stock_node is None:
            print(f"Stock nie znaleziony (Prod: {product_id}, Attr: {attribute_id})")
            return

        stock_id = stock_node.find('id').text
        id_shop = stock_node.find('id_shop').text if stock_node.find('id_shop') is not None else "1"
        depends = stock_node.find('depends_on_stock').text if stock_node.find('depends_on_stock') is not None else "0"
        out_of = stock_node.find('out_of_stock').text if stock_node.find('out_of_stock') is not None else "2"

        xml_update = f"""<?xml version="1.0" encoding="UTF-8"?>
        <prestashop xmlns:xlink="http://www.w3.org/1999/xlink">
            <stock_available>
                <id>{stock_id}</id>
                <id_product>{product_id}</id_product>
                <id_product_attribute>{attribute_id}</id_product_attribute>
                <quantity>{quantity}</quantity>
                <id_shop>{id_shop}</id_shop>
                <out_of_stock>{out_of}</out_of_stock>
                <depends_on_stock>{depends}</depends_on_stock>
            </stock_available>
        </prestashop>"""
        
        r_put = requests.put(f"{API_URL}/stock_availables/{stock_id}", auth=(API_KEY, ''), headers=HEADERS, data=xml_update.encode('utf-8'))
        
        if r_put.status_code != 200:
            print(f"Błąd Stock ({r_put.status_code}): {r_put.text}")

    except Exception as e:
        print(f"Wyjątek Stock: {e}")

def upload_images(product_id, image_urls):
    for url in image_urls:
        try:
            img_resp = requests.get(url, timeout=10)
            if img_resp.status_code == 200:
                files = {'image': ('image.jpg', img_resp.content, 'image/jpeg')}
                r_img = requests.post(f"{API_URL}/images/products/{product_id}", auth=(API_KEY, ''), files=files)
                if r_img.status_code != 200:
                    print(f"Błąd zdjęcia ({url}): {r_img.status_code}")
            else:
                print(f"Nie pobrano zdjęcia (HTTP {img_resp.status_code}): {url}")
        except Exception as e:
            print(f"Wyjątek zdjęcia: {e}")

# --- PRODUKT I KOMBINACJE ---

def create_product(data, category_data, feature_list, weight):
    name = data.get('name')
    reference = clean_sku(data.get('sku'))
    price_gross = clean_price(data.get('price'))
    price_net = price_gross / VAT_RATE
    description = data.get('description', '')
    link_rewrite = clean_link(name) 
    
    default_cat_id = category_data['default_id']
    all_cat_ids = category_data['all_ids']
    if not default_cat_id: default_cat_id = 2
    if not all_cat_ids: all_cat_ids = [2]

    categories_xml = "".join([f"<category><id>{cid}</id></category>" for cid in all_cat_ids])
    features_xml = "".join([f"<product_feature><id>{f['id']}</id><id_feature_value>{f['id_feature_value']}</id_feature_value></product_feature>" for f in feature_list])

    xml_data = f"""
    <prestashop xmlns:xlink="http://www.w3.org/1999/xlink">
        <product>
            <state>1</state>
            <active>1</active>
            <indexed>1</indexed>
            <show_price>1</show_price>
            <minimal_quantity>1</minimal_quantity>
            <available_for_order>1</available_for_order>
            <id_shop_default>1</id_shop_default>
            <id_category_default>{default_cat_id}</id_category_default>
            
            <price>{price_net:.6f}</price>
            <weight>{weight:.3f}</weight>
            <id_tax_rules_group>1</id_tax_rules_group>
            
            <reference>{reference}</reference>
            <name><language id="{ID_LANG}"><![CDATA[{name}]]></language></name>
            <link_rewrite><language id="{ID_LANG}"><![CDATA[{link_rewrite}]]></language></link_rewrite>
            <description><language id="{ID_LANG}"><![CDATA[{description}]]></language></description>
            <associations>
                <categories>{categories_xml}</categories>
                <product_features>{features_xml}</product_features>
            </associations>
        </product>
    </prestashop>
    """

    response = requests.post(f"{API_URL}/products", auth=(API_KEY, ''), headers=HEADERS, data=xml_data.encode('utf-8'))
    
    if response.status_code in [200, 201]:
        return ET.fromstring(response.content).findtext('.//id')
    
    elif response.status_code == 500:
        # Awaryjnie szukamy po sku
        try:
            params = {'filter[reference]': f'[{reference}]', 'display': '[id]', 'limit': 1}
            r = requests.get(f"{API_URL}/products", auth=(API_KEY, ''), params=params)
            if r.status_code == 200:
                node = ET.fromstring(r.content).find('.//product/id')
                if node is not None: return node.text
        except: pass
    
    print(f"Błąd API (Produkt): {response.status_code}")
    return None

def create_combination(product_id, attribute_value_id, quantity=5):
    variant_ref = f"{product_id}-{attribute_value_id}"
    
    xml = f"""<prestashop xmlns:xlink="http://www.w3.org/1999/xlink">
        <combination>
            <id_product>{product_id}</id_product>
            <minimal_quantity>1</minimal_quantity>
            <price>0.000000</price>
            <unit_price_impact>0.000000</unit_price_impact>
            <weight>0.000000</weight>
            <default_on>0</default_on>
            <reference>{variant_ref}</reference>
            <associations>
                <product_option_values>
                    <product_option_value><id>{attribute_value_id}</id></product_option_value>
                </product_option_values>
            </associations>
        </combination>
    </prestashop>"""
    
    response = requests.post(f"{API_URL}/combinations", auth=(API_KEY, ''), headers=HEADERS, data=xml.encode('utf-8'))
    
    if response.status_code in [200, 201]:
        return ET.fromstring(response.content).findtext('.//id')
    else:
        print(f"Błąd Wariantu: {response.status_code}")
        print(response.text)
        return None

if __name__ == "__main__":
    print("Start importu produktów...")
    
    build_category_map()
    size_group_id = get_or_create_attribute_group("Rozmiar")
    if not size_group_id: 
        print("Błąd Grupy Atrybutów"); exit()
    
    try:
        with open(SOURCE_FILE, 'r', encoding='utf-8') as f: raw_products = json.load(f)
    except: 
        print("Brak pliku JSON"); exit()
        
    if isinstance(raw_products, dict): raw_products = [raw_products]

    print("Scalanie duplikatów...")
    unique_products = {}
    for item in raw_products:
        raw_sku = item.get('sku')
        if not raw_sku: continue
        sku = clean_sku(raw_sku)
        current_cats = item.get('category', [])
        if sku in unique_products:
            merged = list(set(unique_products[sku].get('category', []) + current_cats))
            unique_products[sku]['category'] = merged
            unique_products[sku]['all_paths'].append(current_cats)
        else:
            unique_products[sku] = item
            unique_products[sku]['all_paths'] = [current_cats]

    print(f"Unikalnych: {len(unique_products)}")

    for sku, data in unique_products.items():
        name = data.get('name')
        print(f"{name}")
        
        category_data = resolve_product_categories(data['all_paths'])
        
        feature_list = []
        add_info = data.get('additional_info', {})
        
        raw_weight = add_info.get('Waga', None)
        weight = clean_weight(raw_weight)

        for k, v in add_info.items():
            f = add_feature(k, str(v))
            if f: feature_list.append(f)

        new_prod_id = create_product(data, category_data, feature_list, weight)

        if new_prod_id:
            sizes = data.get('sizes', [])
            if sizes:
                for size in sizes:
                    val_id = get_or_create_attribute_value(size_group_id, size)
                    if val_id:
                        comb_id = create_combination(new_prod_id, val_id)
                        if comb_id:
                            update_stock_available(new_prod_id, comb_id, quantity=random.randint(2, 10))
            else:
                update_stock_available(new_prod_id, 0, quantity=random.randint(2, 10))

            imgs = data.get('images', [])
            if imgs: upload_images(new_prod_id, imgs)