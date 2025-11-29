import requests
import json
import os
import re
import time
from dotenv import load_dotenv
from unidecode import unidecode
from xml.etree import ElementTree

load_dotenv()

API_KEY = os.getenv("API_KEY")
API_URL = os.getenv("API_URL")
ID_LANG = 1

CATEGORIES_URL = f"{API_URL}/categories"
SOURCE_FILE = '../../results/categories.json'

def clean_link(link):
    link = unidecode(link).lower()
    link = re.sub(r'[^a-z0-9\-]+', '-', link)
    return link.strip('-')


def determine_link(item):
    source_url = item.get('url')
    source_name = item.get('name')

    if source_url:
        parts = source_url.split('/')
        return parts[-1]
    
    return clean_link(source_name)

def create_category(item, parent_id):
    name = item.get('name')
    link = determine_link(item)

    xml_data = f"""
    <prestashop xmlns:xlink="http://www.w3.org/1999/xlink">
        <category>
            <id_parent><![CDATA[{parent_id}]]></id_parent>
            <active><![CDATA[1]]></active>
            <name>
                <language id="{ID_LANG}"><![CDATA[{name}]]></language>
            </name>
            <link_rewrite>
                <language id="{ID_LANG}"><![CDATA[{link}]]></language>
            </link_rewrite>
        </category>
    </prestashop>
    """

    headers = {'Content-Type': 'application/xml'}

    response = requests.post(CATEGORIES_URL, auth=(API_KEY, ''), headers=headers, data=xml_data.encode('utf-8'))

    if response.status_code in [200, 201]:
        tree = ElementTree.fromstring(response.content)
        new_id = tree.findtext('.//id')
        return new_id
    else:
        print(f"Błąd API dla '{name}' (link: {link}): {response.status_code}")
        #print(response.text)
        return None
    

def process_category_tree(category_list, parent_id=2):
    for item in category_list:
        name = item.get('name')
        print(f"Przetwarzam: {name}")
        new_id = create_category(item, parent_id)

        if new_id:
            children = item.get('subcategories', [])
            if not children:
                children = item.get('items', [])
            
            if children:
                process_category_tree(children, parent_id=new_id)
            time.sleep(0.1)



if __name__ == "__main__":
    print("Start importu kategorii...")
    if os.path.exists(SOURCE_FILE):
        with open(SOURCE_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            process_category_tree(data)
    else:
        print("Nie znaleziono pliku {SOURCE_FILE}")