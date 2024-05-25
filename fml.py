import sys
import requests
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET
import glob

if len(sys.argv) != 2:
    print("Usage: python3 script.py <id>")
    sys.exit(1)

npc_id = sys.argv[1]
url = f'https://l2db.club/?show=npc_info&id={npc_id}'

response = requests.get(url)
html_content = response.text

soup = BeautifulSoup(html_content, 'html.parser')
tr_tags = soup.find_all('tr')

parsed_data = {}

for tr_tag in tr_tags:
    img_tag = tr_tag.find('img', class_='icon')
    td_amount_tag = tr_tag.find('td', class_='uk-text-center')
    td_chance_tag = tr_tag.find('td', class_='uk-text-right')
    
    if img_tag and td_amount_tag and td_chance_tag:
        item_id = img_tag['title'].split(': ')[1]
        amount = td_amount_tag.text.strip()
        chance = td_chance_tag.text.strip()

        if '%' in chance:
            chance_value = float(chance.strip('%')) / 100
        elif '/' in chance:
            numerator, denominator = map(float, chance.split('/'))
            chance_value = numerator / denominator
        else:
            chance_value = float(chance)

        parsed_data[item_id] = (amount, chance_value)

xml_files = glob.glob('*.xml')

for xml_file_path in xml_files:
    print(f'Processing file: {xml_file_path}')
    tree = ET.parse(xml_file_path)
    root = tree.getroot()

    npc_element = root.find(f".//npc[@id='{npc_id}']")
    
    if npc_element is not None:
        print(f'Found <npc> element with id={npc_id}')
        drop_lists = npc_element.find('dropLists')
        if drop_lists is not None:
            for item in drop_lists.findall('.//item'):
                item_id = item.get('id')
                if item_id == '57':
                    continue
                if item_id in parsed_data:
                    amount, chance_value = parsed_data[item_id]
                    if '-' in amount:
                        min_val, max_val = amount.split(' - ')
                    else:
                        min_val = max_val = amount
                    print(f'Updating item ID {item_id} in file {xml_file_path} with min={min_val}, max={max_val}, and chance={chance_value}')
                    item.set('min', min_val)
                    item.set('max', max_val)
                    item.set('chance', str(chance_value))
        tree.write(xml_file_path)
        print(f'Updated file: {xml_file_path}')
    else:
        print(f'No <npc> element with id={npc_id} found in file {xml_file_path}')
