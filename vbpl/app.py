import json
import time
from bs4 import BeautifulSoup
import requests
import threading

storage = set()
storeValue = set()
id_law = 1

MAX_RETRIES = 20
TIMEOUT_DELAY = 2

storeValueLock = threading.Lock()
idLawLock = threading.Lock()

json_lock = threading.Lock()


def save_to_json(data):
    with json_lock:
        with open('law.json', 'w', encoding='utf-8') as json_file:
            json.dump(data, json_file, ensure_ascii=False, indent=4)
        print(f'\nThêm data vào json:\nid = {data[-1]["id"]}, \ntitle = {data[-1]["title"]}, \ncontent = {data[-1]["content"]},\nlink = {data[-1]["link"]}')

def update_json_data(data, id, title, content, link):
    for entry in data:
        if entry['id'] == id:
            entry['title'] = title
            entry['content'] = content
            entry['link'] = link
            return True
    return False

def Law_loop(path):
    global id_law
    global storage
    global storeValue

    storage.add(path)

    URL = 'https://vbpl.vn' + path

    retries = 0
    while retries < MAX_RETRIES:
        try:
            response = requests.get(URL, timeout=3)
            response.raise_for_status()
            html_content = response.text

            soup = BeautifulSoup(html_content, "html.parser")
            box_traloi = soup.find_all("div", class_="box_traloi")

            id = id_law
            link = 'https://vbpl.vn' + path

            try:
                title_p = box_traloi[0].find("p", class_="title")
                title = title_p.find_next("p").get_text(strip=True)
            except AttributeError:
                title = ""

            try:
                content_non_p = box_traloi[1].find("p", class_=None)
                if content_non_p:
                    send_date_tag = box_traloi[1].find("p", class_="send_date")
                    send_date_tag.extract()

                    find_title_reply = box_traloi[1].find("p", class_="title_reply")
                    find_title_reply.extract()

                    content = box_traloi[1].get_text(separator="\n",strip=True)
            except AttributeError:
                content = ""

            if not title:
                time.sleep(2)
                print(f'\nAPI die at: ID = {id}, Link = {link}')
                continue

            with idLawLock:
                id_law += 1

            entry = {
                "id": id,
                "title": title,
                "content": content,
                "link": link
            }

            with open("law.json", "r", encoding="utf-8") as json_file:
                try:
                    json_data = json.load(json_file)
                except json.JSONDecodeError:
                    json_data = []

            if not update_json_data(json_data, id, title, content, link):
                json_data.append(entry)

            save_to_json(json_data)

            with storeValueLock:
                links_other_question = soup.find_all("div", class_="news-other box-news")
                for div in links_other_question:
                    links = div.find_all("a")
                    for link in links:
                        new_path = link.get("href")
                        if new_path not in storeValue and new_path not in storage:
                            storeValue.add(new_path)

            break

        except requests.exceptions.RequestException as e:
            print("Exception:", e)
            print("Retrying in", TIMEOUT_DELAY, "seconds...")
            retries += 1
            time.sleep(TIMEOUT_DELAY)

def URL_first_crawl(path):
    global id_law
    global storage
    global storeValue

    URL = 'https://vbpl.vn' + path

    retries = 0
    while retries < MAX_RETRIES:
        try:
            response = requests.get(URL, timeout=3)
            response.raise_for_status()
            html_content = response.text

            soup = BeautifulSoup(html_content, "html.parser")
            box_traloi = soup.find_all("div", class_="box_traloi")

            id = id_law
            link = 'https://vbpl.vn' + path

            title_p = box_traloi[0].find("p", class_="title")
            title = title_p.find_next("p").get_text(strip=True) if title_p else None

            if title is None or title.strip() == '':
                retries += 1
                time.sleep(TIMEOUT_DELAY)
                print(f'Retrying due to empty title. Retry attempt: {retries}')
                continue

            with idLawLock:
                id_law += 1
                
            try:
                content_non_p = box_traloi[1].find("p", class_=None)
                if content_non_p:
                    send_date_tag = box_traloi[1].find("p", class_="send_date")
                    send_date_tag.extract()

                    find_title_reply = box_traloi[1].find("p", class_="title_reply")
                    find_title_reply.extract()

                    content = box_traloi[1].get_text(separator="\n",strip=True)
            except AttributeError:
                content = ""

            entry = {
                "id": id,
                "title": title,
                "content": content,
                "link": link
            }

            json_data = [entry]
            save_to_json(json_data)

            with storeValueLock:
                paths_list = []
                links_other_question = soup.find_all("div", class_="news-other box-news")
                for div in links_other_question:
                    links = div.find_all("a")
                    for link in links:
                        path = link.get("href")
                        paths_list.append(path)
                storeValue.update(paths_list)

            break

        except requests.exceptions.RequestException as e:
            print("Exception:", e)
            print("Retrying in", TIMEOUT_DELAY, "seconds...")
            retries += 1
            time.sleep(TIMEOUT_DELAY)

def main():
    global storage
    global storeValue
    path = '/Pages/chitiethoidap.aspx?ItemID=87573'

    storage.add(path)

    URL_first_crawl(path)

    threads = []
    while storeValue:
        path = storeValue.pop()
        if path not in storage:
            Law_loop(path)
            # thread = threading.Thread(target=Law_loop, args=(path,))
            # thread.start()
            # threads.append(thread)

    # for thread in threads:
    #     thread.join()

if __name__ == "__main__":
    main()
