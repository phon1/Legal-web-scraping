import requests
from bs4 import BeautifulSoup
import json
import time
from newspaper import Article


MAX_RETRY = 20
def clean_text(text):
    return text.strip()

def download_article_with_retry(url):
    retry_count = 0
    while retry_count < MAX_RETRY:
        try:
            response = requests.get(url, timeout=2)  # Thêm timeout là 2 giây
            if response.status_code == 200:
                articles = Article(url)
                articles.set_html(response.text)
                articles.parse()
                return articles
        except (requests.exceptions.RequestException, ValueError):
            print(f"Retrying ({retry_count + 1}/{MAX_RETRY}) for URL: {url}")
            retry_count += 1
    return None


def extract_data_from_url(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")
    article_elements = soup.find_all("div", class_="box-category-content")
    data_list = []

    for article in article_elements:
        link_element = article.find("a", class_="box-category-link-title")
        link = "https://tuoitre.vn" + link_element["href"] if link_element else ""


        articles = download_article_with_retry(link)

        articles.title
        articles.text
        articles.publish_date
        articles.authors

        title_element = articles.title
        title = title_element if title_element else ""

        summary_element = article.find("p", class_="box-category-sapo")
        summary = clean_text(summary_element.text) if summary_element else ""

        # Additional scraping for summary
        if not summary:
            try:
                summary_element = soup.find("h2", class_="detail-sapo")
                summary = clean_text(summary_element.text) if summary_element else ""
            except:
                pass

        # Additional scraping for posted_date
        posted_date = ""
        try:
            # Find the specific article URL and fetch its content
            article_url = link
            article_response = requests.get(article_url)
            article_soup = BeautifulSoup(article_response.content, "html.parser")

            posted_date_element = article_soup.find("div", {"data-role": "publishdate"})
            posted_date = posted_date_element.text.strip()
            # Format posted_date from "dd/mm/yyyy h:m GMT+7" to "%Y-%m-%d %H:%M:%S"
            posted_date = time.strftime("%Y-%m-%d %H:%M:%S", time.strptime(posted_date, "%d/%m/%Y %H:%M GMT+7"))
        except:
            pass

        # Additional scraping for content
        content = articles.text if articles.text else ''
        # try:
        #     content_element = article_soup.find("div", class_="detail-content afcbc-body")
        #     if content_element:
        #         paragraphs = content_element.find_all("p")
        #         content = " ".join(clean_text(p.get_text()) for p in paragraphs)
        # except Exception as e:
        #     print(f"Error extracting content: {e}")

        entry = {
            "id": 0,  # Placeholder for id
            "title": title,
            "link": link,
            "summary": summary,
            "posted_date": posted_date,
            "content": content,
        }
        data_list.append(entry)

    return data_list

# Read URLs and extract data
base_url = "https://tuoitre.vn/timeline/79/trang-{}.htm"
all_data = []

# Loop through the API URLs
for page_num in range(1, 56):
    
    url = base_url.format(page_num)
    data = extract_data_from_url(url)
    all_data.extend(data)

# Add id to each entry in the list
for i, entry in enumerate(all_data, start=1):
    entry["id"] = i

# Export the data to JSON format
output_file = "tt_TuVanPhapLuat1.json"
with open(output_file, "w", encoding="utf-8") as json_file:
    json.dump(all_data, json_file, ensure_ascii=False, indent=2)

print(f"Data exported to '{output_file}' successfully.")
