import asyncio
import random
import re
from curl_cffi.requests import AsyncSession
from bs4 import BeautifulSoup


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

    def get_text_by_label(self, soup, label):
        """Ищет текст в следующем элементе после метки (label)"""
        node = soup.find(string=re.compile(label))
        if node and node.parent:
            # Находим следующий сестринский элемент с текстом
            sibling = node.parent.find_next_sibling()
            return sibling.get_text("\n", strip=True) if sibling else "Не найдено"
        return "Не найдено"

    def get_ids(self, card):
        """Извлекает ID для ФЗ-223 и ФЗ-44 из ссылок/onclick"""
        links = re.findall(r"Id=([a-fA-F0-9-]+|\d+)", str(card))
        # Обычно первый ID — 223, второй — 44 (или наоборот, зависит от разметки)
        return list(set(links))


async def main():
    parser = EISParser()
    inn = "7707083893"
    search_url = f"https://zakupki.gov.ru/epz/organization/search/results.html?searchString={inn}"

    soup = await parser.get_soup(search_url)
    card = soup.find("div", class_="search-registry-entry-block") if soup else None

    if not card:
        print("Организация не найдена")
        return

    data = {
        "Название": card.find("a").get_text(strip=True),
        "ИНН": parser.get_text_by_label(card, "ИНН"),
        "КПП": parser.get_text_by_label(card, "КПП"),
        "ОГРН": parser.get_text_by_label(card, "ОГРН"),
        "Местонахождение": parser.get_text_by_label(card, "Местонахождение"),
        "IDs": parser.get_ids(card),
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
if __name__ == "__main__":
    asyncio.run(main())
