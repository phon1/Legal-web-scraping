import json
from bs4 import BeautifulSoup
import requests
from datetime import datetime

def parse_time(front_time):
    # Convert the date part to a datetime object
    date_obj = datetime.strptime(front_time, "%H:%M | %d/%m/%Y")
    
    # Return the formatted time
    return date_obj.strftime("%Y/%d/%m %H:%M:%S")

def extract_text_from_div(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")
    div_model_detail = soup.find("div", class_="divModelDetail")

    if div_model_detail:
        content = div_model_detail.get_text().strip()
        return content
    else:
        return ''

def extract_data_from_ul(ul_element, start_id):
    data_list = []
    current_id = start_id

    for li in ul_element.find_all("li", class_="tt"):
        title = li.find("a").text.strip()
        link = 'https://thuvienphapluat.vn' + li.find("a")["href"]
        date_time = li.find_next("span").text.strip()
        time = parse_time(date_time)

        summary_element = li.find_next("li", class_="it")
        summary = summary_element.text.strip() if summary_element else ""

        content = extract_text_from_div(link)

        entry = {
            "id": current_id,
            "title": title,
            "link": link,
            "posted_date": time,
            "summary": summary,
            "content": content
        }
        data_list.append(entry)
        current_id += 1

    return data_list, current_id

def extract_data_from_url(url, start_id):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")
    ul_elements = soup.find_all("ul", class_="ulTinList")
    data_list = []
    current_id = start_id

    for ul in ul_elements:
        data, current_id = extract_data_from_ul(ul, current_id)
        data_list.extend(data)

    return data_list, current_id

# URLs to scrape
urls = [
    f"https://thuvienphapluat.vn/chinh-sach-phap-luat-moi/vn/thoi-su-phap-luat/tu-van-phap-luat?p={i}"
    # Sửa 849 tùy theo số page tối đa theo từng đợt code
    for i in range(1, 849)
]

all_data = []
current_id = 1

# Extract data from each URL and combine it
for url in urls:
    try:
        data, current_id = extract_data_from_url(url, current_id)
        all_data.extend(data)
    except Exception as e:
        print(f"Error extracting data from URL: {url}, {e}")

# Export the combined data to JSON format
output_file = "tvpl_TuVan.json"
with open(output_file, "w", encoding="utf-8") as json_file:
    json.dump(all_data, json_file, ensure_ascii=False, indent=2)

print(f"Data exported to '{output_file}' successfully.")
