# Webscraping for dishwasher parts
import json
import urllib.request
from bs4 import BeautifulSoup
from dataclasses import dataclass
import re as regex
import csv 

@dataclass
class DishwasherPart:
    name: str
    price: float
    in_stock: bool
    rating: float
    review_count: int
    part_select_number: str
    manufacturer_part_number: str
    item_description: str
    fixes_these_symptoms: list[str]
    replaces_these_parts: list[str]
    installation_instructions: str
    is_compatible_with: list[str]

base_url = "https://www.partselect.com"
dishwasher_parts_url = base_url + "/Dishwasher-Parts.htm"
page = urllib.request.urlopen(dishwasher_parts_url)
soup = BeautifulSoup(page, 'html.parser')

part_header_id = "ShopByPartType"
parts_header = soup.find('h2', id=part_header_id)
parts_links_list = parts_header.find_next('ul')
links = []
for link in parts_links_list.find_all('a'):
    _item = {'href': link.get('href'), 'text': link.text}
    links.append(_item)

dishwasher_parts: list[DishwasherPart] = []

for link in links:
    url = base_url + link['href']
    print(f"Searching '{url}'")
    part_page = urllib.request.urlopen(url)
    part_soup = BeautifulSoup(part_page, 'html.parser')
    part_class = "nf__part mb-3"
    site_parts = part_soup.find_all('div', class_=part_class)
    for part in site_parts:
        part_name_class_name = "nf__part__detail__title"
        part_rating_class_name = "nf__part__detail__rating"
        rating_div_class_name = "rating__stars__upper"
        part_price_div_name = "mt-sm-2 price"
        in_stock_div_class_name = "nf__part__left-col__basic-info__stock"
        part_review_count_span_name = "rating__count"
        part_select_number_div_class_name = "nf__part__detail__part-number"
        part_manufacturer_number_div_class_name = "nf__part__detail__part-number mb-2"
        fixes_symptoms_class_name = "nf__part__detail__symptoms"

        part_find = part.find('a', class_=part_name_class_name)
        if part_find is not None:    
            part_name = part_find.text.strip()

        if part.find('div', class_=part_price_div_name) is not None:
            part_price = float(part.find('div', class_=part_price_div_name).text.replace('$', '').strip())
        else:
            part_price = 0.0

        if part.find('div', class_=in_stock_div_class_name) is not None:
            part_in_stock = "In Stock" in part.find('div', class_=in_stock_div_class_name).find_next('span').text.strip()
        else:
            part_in_stock = False

        if part.find('div', class_=rating_div_class_name) is not None:
            part_rating_style = part.find('div', class_=rating_div_class_name).get('style')
        else: 
            part_rating_style = '0.0'

        part_rating = float(part_rating_style.replace('width:', '').replace('%', '').strip()) / 20.0

        if part.find('span', class_=part_review_count_span_name) is not None:
            part_review_count_text = part.find('span', class_=part_review_count_span_name).text.strip().replace('(', '').replace(')', '')
            part_review_count = regex.findall(r'\d+', part_review_count_text)[0]
            part_review_count = int(part_review_count)
        else:
            part_review_count = 0

        part_select_number = part.find('div', class_=part_select_number_div_class_name).find('strong').text.strip()
        part_manufacturer_part_number = part.find('div', class_=part_manufacturer_number_div_class_name).find('strong').text.strip()
        part_item_description = part.find('div', class_=part_manufacturer_number_div_class_name).find_next_sibling(string=True).strip()

        part_fixes_these_symptoms = []
        part_replaces_these_parts = []
        part_is_compatible_with_models = []
        part_installation_instructions = "Has no instructions"

        symptoms_section = part.find('div', class_=fixes_symptoms_class_name)
        instructions_section = None

        try:
            see_more_link = symptoms_section.find('a', class_='underline', href=True)
            if see_more_link:
                subpage_url = base_url + see_more_link['href']
                print(f"\tSearching {subpage_url}")
                subpage = urllib.request.urlopen(subpage_url)
                subpage_soup = BeautifulSoup(subpage, 'html.parser')

                troubleshooting_section = subpage_soup.find('div', id='Troubleshooting')
                if troubleshooting_section:
                    pd_wrap = troubleshooting_section.find_next('div', class_='pd__wrap')
                    if (pd_wrap):
                        symptoms_div = pd_wrap.find('div', class_='bold mb-1', string="This part fixes the following symptoms:")
                        if symptoms_div:
                            symptoms_text = symptoms_div.find_next_sibling(string=True)
                            if symptoms_text:
                                part_fixes_these_symptoms.extend([s.strip().replace('\u2019', "'") for s in symptoms_text.split(" | ")])

                        replaces_div = pd_wrap.find('div', class_='bold mb-1', string=regex.compile(r"Part#"))
                        if replaces_div:
                            replaces_text = replaces_div.find_next_sibling('div').text.strip()
                            part_replaces_these_parts = [p.strip() for p in replaces_text.split(",")]

                video_div = subpage_soup.find('div', class_='yt-video')
                if video_div and 'data-yt-init' in video_div.attrs:
                    youtube_video_id = video_div['data-yt-init']
                    youtube_link = f"https://www.youtube.com/watch?v={youtube_video_id}"
                    part_installation_instructions = youtube_link

                else:
                    instructions_section = subpage_soup.find('img', class_="yt-video__thumb loaded")
                    if instructions_section:
                        yt_id = instructions_section.get('data-src')
                        if yt_id:
                            yt_id = yt_id.split('/')[-2]
                            youtube_link = f"https://youtube.com/watch?v={yt_id}"
                            part_installation_instructions = youtube_link

                is_compatible_section = subpage_soup.find('div', id="ModelCrossReference")
                if is_compatible_section:
                    rows = subpage_soup.find_all('div', class_='row')
                    if rows:
                        for row in rows:
                            a_tag = row.find('a', class_='col-6 col-md-3 col-lg-2')
                            if a_tag:
                                model_number = a_tag.text.strip()
                                part_is_compatible_with_models.append(model_number)
                            else:
                                continue 
                else:
                    part_is_compatible_with_models.append('No information on model compatability')


        except AttributeError as e:
            part_installation_instructions = "Instructions not available"


        if instructions_section:
            instruction_texts = instructions_section.find_all('span', class_=False)
            if instruction_texts:
                part_installation_instructions = " ".join([text.strip() for text in instruction_texts])
            else:
                alt_instruction_section = part.find('div', class_="alternative-instructions-class")
                if alt_instruction_section:
                    part_installation_instructions = alt_instruction_section.text.strip()

        dishwasher_part = DishwasherPart(
            name=part_name,
            price=part_price,
            in_stock=part_in_stock,
            rating=part_rating,
            review_count=part_review_count,
            part_select_number=part_select_number,
            manufacturer_part_number=part_manufacturer_part_number,
            item_description=part_item_description,
            fixes_these_symptoms=part_fixes_these_symptoms,
            replaces_these_parts=part_replaces_these_parts,
            installation_instructions=part_installation_instructions,
            is_compatible_with=part_is_compatible_with_models 
        )
        dishwasher_parts.append(dishwasher_part)

# Export as json file
with open('output.json', 'w') as out_file:
    dishwasher_parts_dicts = [part.__dict__ for part in dishwasher_parts]
    json.dump(dishwasher_parts_dicts, out_file, indent=2)

# Export as csv file
with open('dish_parts.csv', mode='w', newline='') as file:
    writer = csv.writer(file)
    
    writer.writerow([
        "partName", "partPrice", "inStock", "partRating", "partReviews", 
        "PSNumber", "MPNumber", "partDescription", 
        "partSymptoms", "partReplaces", "partInstallation", 
        "partCompatible"
    ])
    
    for part in dishwasher_parts:
        writer.writerow([
            part.name, part.price, part.in_stock, part.rating, part.review_count, 
            part.part_select_number, part.manufacturer_part_number, part.item_description, 
            ", ".join(part.fixes_these_symptoms), ", ".join(part.replaces_these_parts), 
            part.installation_instructions, ", ".join(part.is_compatible_with)
        ])

print("CSV file created successfully.")