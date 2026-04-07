import asyncio
import random
import re
from curl_cffi.requests import AsyncSession
from bs4 import BeautifulSoup
from yarl import URL

class EISParser:
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36",
            "Referer": "https://zakupki.gov.ru",
        }

    async def get_soup(self, url: str):
        async with AsyncSession(impersonate="chrome120") as s:
            try:
                await asyncio.sleep(random.uniform(1, 3))
                resp = await s.get(url, headers=self.headers, timeout=30)
                return BeautifulSoup(resp.text, "lxml") if resp.status_code == 200 else None
            except Exception as e:
                print(f"Ошибка запроса: {e}")
                return None

    def update_url(self, path, **kwargs):
        """Обновляет параметры в ссылке ЕИС"""
        if not path.startswith("http"):
            path = "https://zakupki.gov.ru" + path

        url = URL(path)
        return str(url.update_query(kwargs))

    def get_text_by_label(self, soup, label):
        """Ищет текст в следующем элементе после метки (label)"""
        node = soup.find(string=re.compile(label))
        if node and node.parent:
            # Находим следующий сестринский элемент с текстом
            sibling = node.parent.find_next_sibling()
            return sibling.get_text("\n", strip=True) if sibling else "Не найдено"
        return "Не найдено"

    def get_ids(self, card):
        """Извлекает конкретные ID для 223-ФЗ и 44-ФЗ из атрибута onclick"""
        link_node = card.find("a", onclick=re.compile(r"getInformation"))
        if not link_node:
            return {"fz223": None, "fz44": None}

        onclick_text = link_node.get("onclick", "")

        # Ищем agencyId (223-ФЗ) и organizationId (44-ФЗ)
        fz223_id = re.search(r"agencyId=(\d+)", onclick_text)
        fz44_id = re.search(r"organizationId=(\d+)", onclick_text)

        return {
            "fz223": fz223_id.group(1) if fz223_id else None,
            "fz44": fz44_id.group(1) if fz44_id else None
        }


async def main():
    parser = EISParser()
    inn = "7707083893"
    # 1. Сбор информации о компании по ИНН
    search_url = f"https://zakupki.gov.ru/epz/organization/search/results.html?searchString={inn}"

    soup = await parser.get_soup(search_url)
    card = soup.find("div", class_="search-registry-entry-block") if soup else None

    if not card:
        print("Организация не найдена")
        return
    ids = parser.get_ids(card)
    fz223 = ids["fz223"]
    fz44 = ids["fz44"]
    data = {
        "Название": card.find("a").get_text(strip=True),
        "ИНН": parser.get_text_by_label(card, "ИНН"),
        "КПП": parser.get_text_by_label(card, "КПП"),
        "ОГРН": parser.get_text_by_label(card, "ОГРН"),
        "Местонахождение": parser.get_text_by_label(card, "Местонахождение"),
        "IDs": [fz223, fz44],
        "zakupki223_link": None,
        "zakupki44_link": None,
        "contracts44_link": None,
    }

    # Собираем ОКВЭДы по всем найденным ID (и 223, и 44)

    for org_id in data['IDs']:
        for path in ["view223/info.html?agencyId=", "view/info.html?organizationId="]:
            url = f"https://zakupki.gov.ru/epz/organization/{path}{org_id}"
            s = await parser.get_soup(url)
            if s:
                okved = parser.get_text_by_label(s, "ОКВЭД|Коды основного вида деятельности")
                if okved != "Не найдено":
                    print(f"ОКВЭД по ссылке {org_id}: {okved}")

                right_block = s.find("div", class_="search-results")
                if "view223" in path:
                    data["zakupki223_link"] = right_block.find(string=re.compile("Закупки")).find_parent("a").get("href")
                else:
                    data["zakupki44_link"] = right_block.find(string=re.compile("Закупки")).find_parent("a").get("href")
                    data["contracts44_link"] = right_block.find(string=re.compile("Контракты")).find_parent("a").get("href")
    print(data)

    # 2. Сбор всех тендеров/контрактов
    links = [data["zakupki223_link"]] #, data["zakupki44_link"], data["contracts44_link"]]
    for link in links:
        if link:
            url = parser.update_url(link, recordsPerPage="_50", pageNumber="1")
            s = await parser.get_soup(url)
            for i in range(1, 20):
                url = parser.update_url(link, recordsPerPage="_50", pageNumber=i)
                soup = await parser.get_soup(url)
                cards = soup.find_all("div", class_="search-registry-entry-block box-shadow-search-input")
                for card in cards:
                    price = parser.get_text_by_label(card, "Начальная цена")
                    # id = re.search(r"№\s\d{19}", card)

                    header = card.find("div", class_="registry-entry__header").get_text("--|--", strip=True)
                    parts = header.split("--|--")
                    contract_id = parts[0].replace("№", "").strip()
                    stage = parts[1].strip() if len(parts) > 1 else "Стадия не указана"

                    placed = parser.get_text_by_label(card, "Размещено")
                    ended = parser.get_text_by_label(card, "Окончание подачи заявок")
                    object = parser.get_text_by_label(card, "Объект закупки")
                    client = parser.get_text_by_label(card, "Заказчик")
                    print(client, object, placed+ended, stage, contract_id, price)
                    # lots = []
                    # for i in range(1, 10):
                    #     lot = parser.get_text_by_label(card, f"Лот № {i}.")
                    #     if not lot:
                    #         break
                    #     lots.append(lot)
                    # price = parser.get_text_by_label(card, "Цена контракта")
                    # price = parser.get_text_by_label(card, "Цена контракта")
                    # price = parser.get_text_by_label(card, "Цена контракта")
                    # price = parser.get_text_by_label(card, "Цена контракта")



if __name__ == "__main__":
    asyncio.run(main())
