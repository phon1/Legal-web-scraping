import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import time

def get_additional_info(link):
    try:
        response = requests.get(link)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, "html.parser")
            
            # Extract posted_date
            time_element = soup.find("time", class_="author-time")
            posted_date = time_element["datetime"] if time_element else ""
            try:
                # Convert the posted_date to the desired format (2022-03-20 18:00:00)
                posted_date = datetime.strptime(posted_date, "%Y-%m-%d %H:%M").strftime("%Y-%m-%d %H:%M:%S")
            except ValueError:
                posted_date = ""
            # print(f"Posted Date: {posted_date}")
            
            # Extract summary
            summary_element = soup.find("h2", class_="singular-sapo")
            summary = summary_element.get_text().strip() if summary_element else ""
            # print(f"Summary: {summary}")
            
            # Extract content
            content_element = soup.find("div", class_="singular-content")
            paragraphs = content_element.find_all("p") if content_element else []
            content = " ".join(p.get_text() for p in paragraphs)
            # print(f"Updated content: {content}")
            
            return posted_date, summary, content
        elif response.status_code == 403:
            print("Error 403: Forbidden. Retrying...")
            for _ in range(10):
                time.sleep(5)
                posted_date, summary, content = get_additional_info(link)
                if posted_date or summary or content:
                    return posted_date, summary, content
    except Exception as e:
        print(f"An error occurred while processing '{link}': {e}")
    
    return "", "", ""


def extract_data_from_url(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")
    article_elements = soup.find_all("article", class_="article-item")
    data_list = []

    for article in article_elements:
        title_element = article.find("h3", class_="article-title")
        title = title_element.a.text.replace('\\"', '"') if title_element else ""

        link = ""
        if title_element and title_element.a.has_attr("href"):
            link = "https://dantri.com.vn" + title_element.a["href"]

        summary_element = article.find("div", class_="article-excerpt")
        summary = summary_element.a.text.replace('\\"', '"') if summary_element else ""

        entry = {
            "id": 0,  # We'll set the "id" field to 0 for now
            "title": title,
            "link": link,
            "summary": summary,
        }
        data_list.append(entry)

    return data_list


# Read URLs and extract data
base_urls = [
    "https://dantri.com.vn/ban-doc/tu-van-phap-luat.htm",
    *[f"https://dantri.com.vn/ban-doc/tu-van-phap-luat/trang-{page_num}.htm" for page_num in range(2, 31)]
]

all_data = []
for url in base_urls:
    data = extract_data_from_url(url)
    all_data.extend(data)

# Add id to each entry in the list and update with additional info
for i, entry in enumerate(all_data, start=1):
    entry["id"] = i
    if entry["link"]:
        posted_date, summary, content = get_additional_info(entry["link"])
        if posted_date:
            entry["posted_date"] = posted_date
            print(f"{i} Updated posted_date, url: {entry['link']}")
        if summary:
            entry["summary"] = summary
            print(f"{i} Updated summary, url: {entry['link']}")
        if content:
            entry["content"] = content
            print(f"{i} Updated content, url: {entry['link']}")
        

# Export the data to JSON format
output_file = "DanTri_TuVanPhapLuat.json"
with open(output_file, "w", encoding="utf-8") as json_file:
    json.dump(all_data, json_file, ensure_ascii=False, indent=2)

print(f"Data exported to '{output_file}' successfully.")
