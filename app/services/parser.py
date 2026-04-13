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
        async with AsyncSession(impersonate="chrome120") as s:
            try:
                await asyncio.sleep(random.uniform(1, 2))
                resp = await s.get(url, headers=self.headers, timeout=30)
                if resp.status_code == 200:
                    return BeautifulSoup(resp.text, "lxml")
                return None
            except Exception:
                return None

    def _get_text(self, soup, label):
        node = soup.find(string=re.compile(label, re.IGNORECASE))
        if node and node.parent:
            sibling = node.parent.find_next_sibling()
            return sibling.get_text(" ", strip=True) if sibling else None
        return None

    def _extract_ids(self, card):
        link_node = card.find("a", onclick=re.compile(r"getInformation"))
        if not link_node:
            return None, None

        onclick = link_node.get("onclick", "")
        fz223 = re.search(r"agencyId=(\d+)", onclick)
        fz44 = re.search(r"organizationId=(\d+)", onclick)

        return (
            fz223.group(1) if fz223 else None,
            fz44.group(1) if fz44 else None
        )

    async def get_company_info(self, inn: str):
        search_url = f"{self.BASE_URL}/epz/organization/search/results.html?searchString={inn}"
        soup = await self.get_soup(search_url)

        if not soup:
            return None

        card = soup.find("div", class_="search-registry-entry-block")
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

        for org_id, path in [(fz223_id, "view223"), (fz44_id, "view")]:
            if not org_id:
                continue

            detail_url = f"{self.BASE_URL}/epz/organization/{path}/info.html?{'agencyId' if '223' in path else 'organizationId'}={org_id}"
            dsoup = await self.get_soup(detail_url)

            if not dsoup:
                continue

            res_block = dsoup.find("div", class_="search-results")
            if not res_block:
                continue

            for link in res_block.find_all("a"):
                text = link.text.strip()

                if "Закупки" in text:
                    key = "zakupki223" if "223" in path else "zakupki44"
                    info["links"][key] = link.get("href")

                elif "Контракты" in text:
                    info["links"]["contracts44"] = link.get("href")

        return info

    async def parse_cards(self, base_link: str, pages=1):
        all_results = []

        for p in range(1, pages + 1):
            url = str(
                URL(f"{self.BASE_URL}{base_link}").update_query(
                    recordsPerPage="_50",
                    pageNumber=str(p)
                )
            )

            soup = await self.get_soup(url)
            if not soup:
                break

            cards = soup.find_all("div", class_="search-registry-entry-block")

            for card in cards:
                header = card.find("div", class_="registry-entry__header")
                header_text = header.get_text(" ", strip=True) if header else ""

                id_match = re.search(r"(\d{11,19})", header_text)
                contract_id = id_match.group(1) if id_match else None

                obj_node = card.find("div", class_="registry-entry__body-value")
                obj_text = obj_node.get_text(strip=True) if obj_node else None

                price = self._get_text(card, r"(Начальная цена|Цена контракта)")
                if price:
                    price = price.replace("₽", "").replace("руб.", "").strip()

                all_results.append({
                    "id": contract_id,
                    "price": price,
                    "object": obj_text,
                    "customer": self._get_text(card, "Заказчик"),
                    "date": self._get_text(card, "Размещено")
                })

        return all_results