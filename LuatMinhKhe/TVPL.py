from selenium import webdriver
from selenium.webdriver.common.by import By
from newspaper import Article
import os
import json
import threading

error_links = []

# Hàm để kiểm tra xem một liên kết đã tồn tại trong tệp JSON hay chưa
def is_link_duplicate(link):
    if os.path.exists("TuVanPhapLuatMinhKhe.json"):
        with open("TuVanPhapLuatMinhKhe.json", "r", encoding="utf-8") as json_file:
            data = json.load(json_file)
            for entry in data:
                if entry.get("link") == link:
                    return True
    return False

# Hàm để lấy dữ liệu từ một URL cụ thể
def scrape_url(url, semaphore):
    global id_counter
    driver = webdriver.Chrome()

    try:
        print('--------------------------------------------------------------------------')
        print(url)
        driver.get(url)

        # Tìm element chứa danh sách tin tức
        list_news_element = driver.find_element(By.CLASS_NAME, "list-news")

        # Tìm danh sách các tin tức trong element trên
        item_news_elements = list_news_element.find_elements(By.CLASS_NAME, "item-news")

        # Duyệt qua từng tin tức và trích xuất thông tin
        for item_news in item_news_elements:
            h2_element = item_news.find_element(By.TAG_NAME, "h2")
            a_element = h2_element.find_element(By.TAG_NAME, "a")
            link = a_element.get_attribute("href")

            if is_link_duplicate(link):
                print(f"Skipping duplicate link: {link}")
                continue

            driverInfo = webdriver.Chrome()

            # Sử dụng newspaper3k để trích xuất thông tin
            driverInfo.get(link)
            article = Article(link)
            article.set_html(driverInfo.page_source)
            article.parse()

            # Lấy tiêu đề và nội dung bài viết
            title = article.title

            # Xóa các đoạn văn bản không phù hợp
            paragraphs = article.text.split('\n')
            filtered_paragraphs = []
            for paragraph in paragraphs:
                if '>>' not in paragraph and '19006162' not in paragraph and '1900 6162' not in paragraph and '1900.6162' not in paragraph:
                    filtered_paragraphs.append(paragraph)

            # Ghi nội dung đã lọc vào biến text
            text = '\n'.join(filtered_paragraphs)

            # Tạo một mục dữ liệu mới
            entry = {
                "id": id_counter,
                "link": link,
                "title": title,
                "text": text
            }

            # Tăng ID cho lần lặp tiếp theo
            id_counter += 1

            # Lưu dữ liệu vào danh sách data
            data.append(entry)

            # Save the entire list of data to the JSON file
            with open("TuVanPhapLuatMinhKhe.json", "w", encoding="utf-8") as json_file:
                json.dump(data, json_file, ensure_ascii=False, indent=4)

            print(f'\nid: {id_counter}\n link: {link}\n')

    except Exception as e:
        print(f"Error: {str(e)}")
        print(f"Error at link: {link}\n")
        error_links.append(link)
        
        # Lưu danh sách các URL gây lỗi vào tệp JSON ngay sau khi có lỗi
        with open("error_links.json", "w", encoding="utf-8") as error_file:
            json.dump(error_links, error_file, ensure_ascii=False, indent=4)

    finally:
        # Đóng trình duyệt sau khi hoàn thành
        driver.quit()
        # Giải phóng Semaphore
        semaphore.release()

# Khởi tạo trình duyệt (ví dụ: Chrome)
driver = webdriver.Chrome()

# Khai báo URL gốc
base_url = "https://luatminhkhue.vn/tu-van-phap-luat.aspx"

# Tạo danh sách URL cần duyệt
# urls = [f"{base_url}?page={page}" for page in range(1, 2600)]
urls = [f"{base_url}?page={page}" for page in range(2, 5)]

# urls = [f"{base_url}?page={page}" for page in range(7, 20)]

# Khởi tạo danh sách để lưu thông tin
data = []

# ID ban đầu
id_counter = 23

# Giới hạn số lượng luồng tối đa là 3
max_threads = 3
semaphore = threading.Semaphore(max_threads)

# Sử dụng threading để thực thi đa luồng
threads = []
dem = 1

# Check if the JSON file already exists
if os.path.exists("TuVanPhapLuatMinhKhe.json"):
    with open("TuVanPhapLuatMinhKhe.json", "r", encoding="utf-8") as json_file:
        data = json.load(json_file)

for url in urls:
    print(f'Threading số thứ {dem}')
    print(url)
    thread = threading.Thread(target=scrape_url, args=(url, semaphore))
    threads.append(thread)
    thread.start()
    semaphore.acquire()  # Chặn cho đến khi có một luồng được phép tiếp tục
    dem += 1

# Chờ cho tất cả các luồng hoàn thành
for thread in threads:
    thread.join()

# Đóng trình duyệt sau khi hoàn thành
driver.quit()

# Lưu dữ liệu vào tệp JSON sau khi đã thu thập hết
with open("TuVanPhapLuatMinhKhe.json", "w", encoding="utf-8") as json_file:
    json.dump(data, json_file, ensure_ascii=False, indent=4)
