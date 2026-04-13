import asyncio
import random
import re
from curl_cffi.requests import AsyncSession
from bs4 import BeautifulSoup
from yarl import URL


class EISParser:
    BASE_URL = "https://zakupki.gov.ru"

    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36",
            "Referer": self.BASE_URL,
        }

    async def get_soup(self, url: str):
        """Выполняет запрос и возвращает объект BeautifulSoup."""
        async with AsyncSession(impersonate="chrome120") as s:
            try:
                await asyncio.sleep(random.uniform(1, 2))
                resp = await s.get(url, headers=self.headers, timeout=30)
                if resp.status_code == 200:
                    return BeautifulSoup(resp.text, "lxml")
                return None
            except Exception as e:
                print(f"Ошибка сети: {e}")
                return None

    def _get_text(self, soup, label):
        """Вспомогательный метод для поиска текста по метке."""
        node = soup.find(string=re.compile(label, re.IGNORECASE))
        if node and node.parent:
            sibling = node.parent.find_next_sibling()
            return sibling.get_text(" ", strip=True) if sibling else "Н/Д"
        return "Н/Д"

    def _extract_ids(self, card):
        """Извлекает внутренние ID организации из атрибута onclick."""
        link_node = card.find("a", onclick=re.compile(r"getInformation"))
        if not link_node:
            return None, None

        onclick = link_node.get("onclick", "")
        fz223 = re.search(r"agencyId=(\d+)", onclick)
        fz44 = re.search(r"organizationId=(\d+)", onclick)
        return (fz223.group(1) if fz223 else None,
                fz44.group(1) if fz44 else None)

    async def get_company_info(self, inn: str):
        """Собирает базовую информацию об организации по ИНН."""
        search_url = f"{self.BASE_URL}/epz/organization/search/results.html?searchString={inn}"
        soup = await self.get_soup(search_url)
        card = soup.find("div", class_="search-registry-entry-block") if soup else None

        if not card:
            return None

        fz223_id, fz44_id = self._extract_ids(card)

        info = {
            "name": card.find("a").get_text(strip=True),
            "inn": self._get_text(card, "ИНН"),
            "kpp": self._get_text(card, "КПП"),
            "ogrn": self._get_text(card, "ОГРН"),
            "address": self._get_text(card, "Местонахождение"),
            "fz223_id": fz223_id,
            "fz44_id": fz44_id,
            "links": {}
        }

        # Сбор внутренних ссылок на закупки/контракты
        for org_id, path in [(fz223_id, "view223"), (fz44_id, "view")]:
            if not org_id: continue

            detail_url = f"{self.BASE_URL}/epz/organization/{path}/info.html?{'agencyId' if '223' in path else 'organizationId'}={org_id}"
            dsoup = await self.get_soup(detail_url)
            if dsoup:
                res_block = dsoup.find("div", class_="search-results")
                if res_block:
                    for link in res_block.find_all("a"):
                        text = link.text.strip()
                        if "Закупки" in text:
                            key = "zakupki223" if "223" in path else "zakupki44"
                            info["links"][key] = link.get("href")
                        elif "Контракты" in text:
                            info["links"]["contracts44"] = link.get("href")
        return info

    async def parse_cards(self, base_link: str, pages=1):
        """Парсит список карточек тендеров (223 и 44 ФЗ)."""
        all_results = []
        for p in range(1, pages + 1):
            url = str(URL(f"{self.BASE_URL}{base_link}").update_query(recordsPerPage="_50", pageNumber=str(p)))
            soup = await self.get_soup(url)
            if not soup: break

            cards = soup.find_all("div", class_="search-registry-entry-block")
            for card in cards:
                # Номер (от 11 до 19 цифр)
                header_text = card.find("div", class_="registry-entry__header").get_text(" ", strip=True)
                id_match = re.search(r"(\d{11,19})", header_text)
                contract_id = id_match.group(1) if id_match else "Н/Д"

                # Объект закупки: в закупках он всегда в registry-entry__body-value
                obj_node = card.find("div", class_="registry-entry__body-value")
                obj_text = obj_node.get_text(strip=True) if obj_node else "Н/Д"

                # Цена: убираем лишние символы валют для чистоты
                price = self._get_text(card, r"(Начальная цена|Цена контракта)")
                price = price.replace("₽", "").replace("руб.", "").strip()

                all_results.append({
                    "id": contract_id,
                    "price": price,
                    "object": obj_text,
                    "customer": self._get_text(card, "Заказчик"),
                    "date": self._get_text(card, "Размещено")
                })
        return all_results


async def main():
    parser = EISParser()
    company = await parser.get_company_info("7707083893")

    if company:
        print(f"--- {company['name']} ---")
        for type_key, link in company['links'].items():
            print(f"\nПарсим {type_key}...")
            items = await parser.parse_cards(link, pages=1)
            for it in items[:3]:  # Покажем первые 3 для теста
                print(f"[{it['id']}] {it['price']} руб. | {it['object'][:50]}...")


if __name__ == "__main__":
    asyncio.run(main())
