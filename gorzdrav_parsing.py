from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium import webdriver
from selenium.webdriver.common.by import By
# from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time

# chrome_options = Options()
chrome_options = webdriver.ChromeOptions()
chrome_options.binary_location = r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe"
service = Service(ChromeDriverManager().install())
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-infobars")
chrome_options.add_argument(
    "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
# chrome_options.page_load_strategy = 'eager'

URL_SPECILAITY1 = "https://gorzdrav.spb.ru/service-free-schedule#%5B%7B%22district%22:%227%22%7D,%7B%22lpu%22:%22233%22%7D,%7B%22speciality%22:%2252%22%7D%5D"
URL_SPECILAITY2 = "https://gorzdrav.spb.ru/service-free-schedule#%5B%7B%22district%22:%2217%22%7D,%7B%22lpu%22:%22333%22%7D,%7B%22speciality%22:%227741%22%7D%5D"
URL_SPECILAITY3 = "https://gorzdrav.spb.ru/service-free-schedule#%5B%7B%22district%22:%2214%22%7D,%7B%22lpu%22:%221110%22%7D,%7B%22speciality%22:%2249405%22%7D%5D"


def get_med_data(URL):
    # Запускаем таймер
    start_time = time.time()
    med_data = {}

    # Запускаем драйвер
    print("🚀 Запуск драйвера браузера Brave...")
    with webdriver.Chrome(service=service, options=chrome_options) as driver:

        def get_element_text_safe(driver, selector, default="Не указано"):
            try:
                element = driver.find_element(By.CSS_SELECTOR, selector)
                return element.text.strip()
            except:
                return default

        print(f"🌐 Переход на страницу...")
        driver.get(URL)

        wait_time = 20
        print(f"⏳ Ожидаем загрузки расписания (до {wait_time} сек)...")
        wait = WebDriverWait(driver, wait_time)
        doctors = wait.until(
            EC.presence_of_all_elements_located(
                (By.CSS_SELECTOR, ".service-block-1.service-doctor.js-doctor"))
        )

        district = get_element_text_safe(
            driver, '.js-service-edits [data-current-step="1"] .service-edit__title', "Не указан")
        district = district.replace(
            'Район: ', '') if district != "Не указан" else district
        organization = get_element_text_safe(
            driver, '.js-service-edits [data-current-step="2"] .service-edit__title', "Не указана")
        organization = organization.replace(
            'Медорганизация: ', '') if organization != "Не указана" else organization
        specialty = get_element_text_safe(
            driver, '.js-service-edits [data-current-step="4"] .service-edit__title', "Не указана")
        specialty = specialty.replace(
            'Специальность: ', '') if specialty != "Не указана" else specialty

        med_data['med_info'] = f"{district}\n{organization}\n{specialty}"
        med_data['doctors_qty'] = len(doctors)
        doctors_info = []
        for doctor in doctors:
            name = doctor.get_attribute("data-doctor-name")
            # Ищем ВСЕ элементы <li> внутри текущего врача
            li_items = doctor.find_elements(By.TAG_NAME, "li")
            tickets = 0  # по умолчанию
            for li_item in li_items:
                text = li_item.text.strip()
                if text and "Доступных номерков" in text:  # если текст не пустой
                    tickets = int(text.split()[-1])
                    break  # берём первый непустой
            doctors_info.append({"name": name, "tickets": tickets})
        med_data["doctors_info"] = doctors_info

    end_time = time.time()
    total_time = end_time - start_time
    print(f"\n⏱️ Общее время выполнения: {total_time:.2f} секунд")

    # УБРАТЬ!
    # driver.quit()
    print("🚪 Браузер закрыт.")
    return med_data


med_data = get_med_data(URL_SPECILAITY3)

print(f"Медицинское учреждение: {med_data['med_info']}")
print(f"Количество врачей: {med_data['doctors_qty']}")
print("Список врачей:")
for i, doctor in enumerate(med_data['doctors_info'], 1):
    print(f"  {i}. {doctor['name']} - Доступных номерков: {doctor['tickets']}")
