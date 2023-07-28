import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
import time

def scrape_article_details(link):
    try:
        response = requests.get(link, timeout=10)
        if response.status_code == 403:
            # Retry up to 10 times with exponential backoff if we encounter a 403 error
            retry_attempts = 10
            for attempt in range(1, retry_attempts + 1):
                print(f"Retrying {link} - Attempt {attempt}/{retry_attempts}")
                response = requests.get(link, timeout=15)
                if response.status_code == 200:
                    break
                time.sleep(10 * attempt)  # Sleep for 5 seconds with exponential backoff
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        posted_date = ''
        summary = ''
        content = ''

        time_elem = soup.find('time', class_='time')
        if time_elem and 'datetime' in time_elem.attrs:
            posted_date = time_elem['datetime'].strip()
            try:
                # Convert datetime string to the desired format
                dt_obj = datetime.strptime(posted_date, '%Y-%m-%dT%H:%M:%S%z')
                posted_date = dt_obj.strftime('%Y-%m-%d %H:%M:%S')
            except ValueError:
                posted_date = ''

        summary_elem = soup.find('div', class_='article__sapo cms-desc')
        if summary_elem:
            summary = summary_elem.text.strip()

        article_body = soup.find('div', class_='article__body cms-body')
        if article_body:
            paragraphs = article_body.find_all('p')
            if paragraphs:
                content = '\n'.join(p.get_text() for p in paragraphs)
            else:
                div_texts = article_body.find_all('div', style='text-align: justify;')
                content = '\n'.join(div_text.get_text() for div_text in div_texts)


        return posted_date, summary, content

    except requests.exceptions.Timeout:
        print(f"Timeout occurred for URL: {link}. Skipping this article.")
        return '', '', ''
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred for URL: {link}. Skipping this article.")
        return '', '', ''
    except Exception as e:
        print(f"Error occurred for URL: {link}. {e}")
        return '', '', ''
def get_article_data(article_div, starting_id):
    # Existing code remains the same
    title_elem = article_div.find(['h3', 'h2'], class_='story__heading')
    title = title_elem.text.strip() if title_elem else ''
    link = title_elem.a['href'].strip() if title_elem and title_elem.a else ''
    time_elem = article_div.find('time', class_='story__time')
    posted_date = time_elem['datetime'].strip() if time_elem and 'datetime' in time_elem.attrs else ''
    try:
        # Convert datetime string to the desired format
        dt_obj = datetime.strptime(posted_date, '%Y-%m-%dT%H:%M:%S%z')
        posted_date = dt_obj.strftime('%Y-%m-%d %H:%M:%S')
    except ValueError:
        posted_date = ''
    summary_elem = article_div.find('div', class_='story__summary')
    summary = summary_elem.text.strip() if summary_elem else ''
    content = ''
    article_data = {
        'id': starting_id,
        'title': title,
        'link': link,
        'posted_date': posted_date,
        'summary': summary,
        'content': content,
    }
    starting_id += 1 if title else 0

    return article_data, starting_id

def get_articles(url, starting_id):
    # Existing code remains the same
    try:
        response = requests.get(url)
        response.raise_for_status()  # Check if there was any error with the request
        soup = BeautifulSoup(response.content, 'html.parser')
        articles = []

        if url == 'https://plo.vn/ban-doc/toi-muon-hoi/':
            highlight_div = soup.find('div', class_='hightlight')
            if highlight_div:
                highlight_articles = highlight_div.find_all('article', class_='story')
                for article_div in highlight_articles:
                    article_data, starting_id = get_article_data(article_div, starting_id)
                    if article_data['title'] and article_data['link']:  # Skip articles with empty title or link
                        articles.append(article_data)

        box_style_divs = soup.find_all('div', class_='box-style-12')
        for box_style_div in box_style_divs:
            box_style_articles = box_style_div.find_all('article', class_='story')
            for article_div in box_style_articles:
                article_data, starting_id = get_article_data(article_div, starting_id)
                if article_data['title'] and article_data['link']:  # Skip articles with empty title or link
                    articles.append(article_data)

        return articles, starting_id

    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred for URL: {url}. Skipping this page.")
        return [], starting_id
    except Exception as e:
        print(f"Error occurred for URL: {url}. {e}")
        return [], starting_id

def main():
    # change total_pages if after have more  law paper
    total_pages = 91
    all_articles = []
    starting_id = 1

    # Read url1
    url1 = 'https://plo.vn/ban-doc/toi-muon-hoi/'
    articles, starting_id = get_articles(url1, starting_id)
    all_articles.extend(articles)

    # Read url2
    for page in range(2, total_pages + 1):
        url = f'https://plo.vn/ban-doc/toi-muon-hoi/?trang={page}'
        articles, starting_id = get_articles(url, starting_id)
        all_articles.extend(articles)

    # Export articles with non-empty titles to plo.json
    filtered_articles = [article for article in all_articles if article['title']]
    for article in filtered_articles:
        link = article['link']
        posted_date = article['posted_date']
        summary = article['summary']
        content = article['content']
        id = article['id']
        if not posted_date:
            posted_date, _, _ = scrape_article_details(link)
            if posted_date:
                article['posted_date'] = posted_date
                print(f"{id} Updated posted_date for {link}: {posted_date}")

        if not summary:
            _, summary, _ = scrape_article_details(link)
            if summary:
                article['summary'] = summary
                print(f"{id} Updated summary for {link}: {summary}")

        if not content:
            _, _, content = scrape_article_details(link)
            if content:
                article['content'] = content
                print(f"{id} Updated content for {link}")
            else: 
                print(f"content null {id} , {link}")

    # Export the final list of articles to plo.json
    with open('plo.json', 'w', encoding='utf-8') as f:
        json.dump(filtered_articles, f, ensure_ascii=False, indent=2)

if __name__ == '__main__':
    main()

