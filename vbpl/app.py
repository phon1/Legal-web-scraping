import json
import re
import time
from urllib.parse import urljoin
from bs4 import BeautifulSoup
import requests

storage = set()
storeValue = set()
id_law = 1

def save_to_json(data):
    with open('law.json', 'w', encoding='utf-8') as json_file:
        json.dump(data, json_file, ensure_ascii=False, indent=4)
    print(f'Thêm data vào json:\nid = {data[0]["id"]}, \ntitle = {data[0]["title"]}, \ncontent = {data[0]["content"]}')

def update_json_data(data, id, title, content, link):
    for entry in data:
        if entry['id'] == id:
            entry['title'] = title
            entry['content'] = content
            entry['link'] = link
            return True
    return False

def Law_recursion(path):
    global id_law
    global storage
    global storeValue

    storage.add(path)
    storeValue.add(path)

    if id_law == 1:
        URL = 'https://vbpl.vn/Pages/chitiethoidap.aspx?ItemID=87573'
    else:
        URL = 'https://vbpl.vn' + path

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

                content = box_traloi[1].get_text(separator="\n").strip()
        except AttributeError:
            content = ""

        if not title or not content:
            time.sleep(2)
            return Law_recursion(path)

        entry = {
            "id": id,
            "title": title,
            "content": content,
            "link": link
        }

        if id_law == 1:
            json_data = [entry]
            save_to_json(json_data)
        else:
            with open("law.json", "r", encoding="utf-8") as json_file:
                try:
                    json_data = json.load(json_file)
                except json.JSONDecodeError:
                    json_data = []
            
            if not update_json_data(json_data, id, title, content, link):
                json_data.append(entry)
            
            save_to_json(json_data)

        paths_list = []
        links_other_question = soup.find_all("div", class_="news-other box-news")
        for div in links_other_question:
            links = div.find_all("a")
            for link in links:
                path = link.get("href")
                paths_list.append(path)
        regex_pattern = re.compile(r'Pages/chitiethoidap\.aspx\?ItemID=\d+')
        
        if id_law == 1:
            storeValue.update(paths_list)
        else:
            for path_dif in paths_list:
                if path_dif not in storeValue:
                    storeValue.add(path_dif)
    
        # tìm phần tử đầu tiên trong tập hợp (storeValue - storage) mà không có trong tập hợp storage.
        path_new = next(iter(storeValue  - {path} - storage), None)

        if path_new == None:
            return
        if path_new:
            id_law += 1
            return Law_recursion(path_new)

    except requests.exceptions.RequestException as e:
        print("Exception:", e)

if __name__ == "__main__":
    storage.add("/Pages/chitiethoidap.aspx?ItemID=87573")
    storeValue.add("/Pages/chitiethoidap.aspx?ItemID=87573")
    Law_recursion("/Pages/chitiethoidap.aspx?ItemID=87573")
