import random
import asyncio
from curl_cffi.requests import AsyncSession
from bs4 import BeautifulSoup
import re

class EISFetcher:
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3",
            "Referer": "https://zakupki.gov.ru",
        }

    async def fetch(self, url: str):
        async with AsyncSession(impersonate="chrome120") as s:
            try:
                await asyncio.sleep(random.uniform(2, 5))
                response = await s.get(url, headers=self.headers, timeout=30)
                if response.status_code == 200:
                    return response.text
                else:
                    print(f"Ошибка доступа: {response.status_code}")
                    return None
            except Exception as e:
                print(f"Сетевая ошибка: {e}")
                return None

class EISParser:
    def __init__(self):
        self.placeholder = "let it be here"




    def replace_abbs(self, text):
        abbs = [("ПУБЛИЧНОЕ АКЦИОНЕРНОЕ ОБЩЕСТВО", "ПАО")]
        for old, new in abbs:
            if old in text:
                text = text.replace(old, new)
        return text


    def get_name(self, card):
        return self.replace_abbs(card.find("a").get_text(strip=True))


    def find_brother(self, name: str, card):
        brother = card.find(string=name).parent
        return brother.find_next_sibling().get_text(strip=True)

    def get_links(self, card):
        tag = card.find("a")
        if not tag:
            return []
        url = tag.get("href") or tag.get("onclick") or ""
        if "getInformation" in url or "'" in url:
            return re.findall(r"'(.*?)'", url)
        if not url or url == "#":
            return []
        return [url]



async def main():
    fetcher = EISFetcher()
    parser = EISParser()
    inn = 6163030517
    url = f"https://zakupki.gov.ru/epz/organization/search/results.html?searchString={inn}&morphology=on&fz94=on&fz223=on&F=on&S=on&M=on&NOT_FSM=on&registered94=on&notRegistered=on&sortBy=NAME&pageNumber=1&sortDirection=false&recordsPerPage=_10&showLotsInfoHidden=false"

    html_content = await fetcher.fetch(url)

    if html_content:

        print(f"Успешно получено {len(html_content)} символов")
        # print(html_content)
        soup = BeautifulSoup(html_content, "lxml")
        cards = soup.find_all("div", class_="search-registry-entry-block box-shadow-search-input")
        for card in cards:
            inn = parser.find_brother(name="ИНН", card=card)
            print(inn)
            ogrn = parser.find_brother(name="ОГРН", card=card)
            print(ogrn)
            kpp = parser.find_brother(name="КПП", card=card)
            print(kpp)
            placement = parser.find_brother(name="Местонахождение", card=card)
            print(placement)
            data = parser.get_links(card=card)
            print(data)
            name = parser.get_name(card)
            print(name)

        print("_______________")
    print("Завершено")


if __name__ == "__main__":
    asyncio.run(main())
