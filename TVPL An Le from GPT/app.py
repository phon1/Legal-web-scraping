import requests
from bs4 import BeautifulSoup
from datetime import datetime
import json

def scrape_and_save_to_json():
    base_url = "https://thuvienphapluat.vn/chinh-sach-phap-luat-moi/vn/an-le/?p={}"
    all_data = []
    current_id = 1

    for page_number in range(1, 8):
        url = base_url.format(page_number)
        response = requests.get(url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, "html.parser")
            ul_elements = soup.find_all("ul", class_="ulTinList")
            
            for ul in ul_elements:
                data = {}
                data["id"] = current_id
                
                li_tt = ul.find("li", class_="tt")
                if li_tt:
                    title = li_tt.find("a").text.strip()
                    posted_date = li_tt.find("span").text.strip()
                    link = 'https://thuvienphapluat.vn' + li_tt.find("a")["href"]
                    data["title"] = title
                    data["link"] = link

                    # Parse the posted_date in desired format (from "h:m | d/m/y" to "Y-m-d H:m:s")
                    try:
                        dt_object = datetime.strptime(posted_date, "%H:%M | %d/%m/%Y")
                        data["posted_date"] = dt_object.strftime("%Y-%m-%d %H:%M:%S")
                    except ValueError:
                        print(f"Failed to parse posted_date: {posted_date}")

                li_it = ul.find("li", class_="it")
                if li_it:
                    summary = li_it.text.strip()
                    data["summary"] = summary

                # Additional functionality to extract content from detail page
                if link:
                    content = get_content_from_detail_page(link)
                    data["content"] = content

                all_data.append(data)
                current_id += 1

    with open("tvpl_AnLe.json", "w", encoding="utf-8") as json_file:
        json.dump(all_data, json_file, ensure_ascii=False, indent=4)

def get_content_from_detail_page(url):
    response = requests.get(url)
    if response.status_code == 200:
        detail_soup = BeautifulSoup(response.content, "html.parser")
        div_model_detail = detail_soup.find("div", class_="divModelDetail")
        if div_model_detail:
            p_tags = div_model_detail.find_all("p")
            content = "\n".join(p.get_text() for p in p_tags)
            return content.strip()
        else:
            print(f"Failed to fetch detail page content for URL: {url}")
    else:
        print(f"Failed to fetch detail page: {url}")
    return ""

if __name__ == "__main__":
    scrape_and_save_to_json()
