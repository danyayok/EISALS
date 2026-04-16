import asyncio
import logging
import random
import re
from datetime import datetime
from typing import Any

from bs4 import BeautifulSoup
from curl_cffi.requests import AsyncSession
from yarl import URL

logger = logging.getLogger(__name__)


class EISParser:
    BASE_URL = "https://zakupki.gov.ru"

    def __init__(self, min_delay: float = 1.0, max_delay: float = 2.0):
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                          "(KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
            "Referer": self.BASE_URL,
            "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
        }

    async def get_soup(self, url: str) -> BeautifulSoup | None:
        async with AsyncSession(impersonate="chrome120") as session:
            try:
                await asyncio.sleep(random.uniform(self.min_delay, self.max_delay))
                response = await session.get(url, headers=self.headers, timeout=30)
                if response.status_code != 200:
                    logger.warning("EIS status code %s for %s", response.status_code, url)
                    return None
                return BeautifulSoup(response.text, "lxml")
            except Exception as exc:
                logger.exception("Network error while parsing %s: %s", url, exc)
                return None

    @staticmethod
    def _clean_text(value: str | None) -> str | None:
        if not value:
            return None
        cleaned = value.replace("\xa0", " ")
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        return cleaned or None

    @staticmethod
    def _to_float(raw_value: str | None) -> float | None:
        if not raw_value:
            return None
        text = raw_value.replace("\xa0", " ")
        text = text.replace("₽", "").replace("руб.", "")
        text = re.sub(r"[^\d,\.\s]", "", text)
        text = text.replace(" ", "")
        if text.count(",") == 1 and text.count(".") == 0:
            text = text.replace(",", ".")
        elif text.count(",") > 1 and text.count(".") == 0:
            text = text.replace(",", "")
        try:
            return float(text)
        except ValueError:
            return None

    @staticmethod
    def _to_datetime(value: str | None) -> datetime | None:
        if not value:
            return None

        normalized = value.strip().replace("\xa0", " ")
        for fmt in ("%d.%m.%Y", "%d.%m.%Y %H:%M"):
            try:
                return datetime.strptime(normalized, fmt)
            except ValueError:
                continue
        return None

    @staticmethod
    def _extract_first_code(value: str | None) -> str | None:
        if not value:
            return None
        match = re.search(r"\b\d{2}(?:\.\d{2}){0,4}\b", value)
        return match.group(0) if match else None

    @staticmethod
    def _extract_inn(value: str | None) -> str | None:
        if not value:
            return None
        match = re.search(r"\b\d{10}|\d{12}\b", value)
        return match.group(0) if match else None

    def _get_text_by_label(self, node: BeautifulSoup, label_pattern: str) -> str | None:
        label = node.find(string=re.compile(label_pattern, re.IGNORECASE))
        if not label:
            return None

        parent = label.parent
        if not parent:
            return None

        sibling = parent.find_next_sibling()
        if sibling:
            return self._clean_text(sibling.get_text(" ", strip=True))

        row = parent.find_parent()
        if row:
            value_cell = row.find(class_=re.compile("(value|col|data)", re.IGNORECASE))
            if value_cell:
                return self._clean_text(value_cell.get_text(" ", strip=True))
        return None

    @staticmethod
    def _extract_ids(card: BeautifulSoup) -> tuple[str | None, str | None]:
        link_node = card.find("a", onclick=re.compile(r"getInformation"))
        if not link_node:
            return None, None

        onclick = link_node.get("onclick", "")
        fz223 = re.search(r"agencyId=(\d+)", onclick)
        fz44 = re.search(r"organizationId=(\d+)", onclick)

        return (fz223.group(1) if fz223 else None, fz44.group(1) if fz44 else None)

    async def get_company_info(self, inn: str) -> dict[str, Any] | None:
        search_url = f"{self.BASE_URL}/epz/organization/search/results.html?searchString={inn}"
        soup = await self.get_soup(search_url)
        card = soup.find("div", class_="search-registry-entry-block") if soup else None

        if not card:
            return None

        fz223_id, fz44_id = self._extract_ids(card)

        title_link = card.find("a")
        company_info: dict[str, Any] = {
            "name": self._clean_text(title_link.get_text(strip=True) if title_link else None),
            "inn": self._get_text_by_label(card, "ИНН") or inn,
            "kpp": self._get_text_by_label(card, "КПП"),
            "ogrn": self._get_text_by_label(card, "ОГРН"),
            "address": self._get_text_by_label(card, "Местонахождение"),
            "fz223_id": fz223_id,
            "fz44_id": fz44_id,
            "links": {},
        }

        for org_id, path, param in [
            (fz223_id, "view223", "agencyId"),
            (fz44_id, "view", "organizationId"),
        ]:
            if not org_id:
                continue

            detail_url = f"{self.BASE_URL}/epz/organization/{path}/info.html?{param}={org_id}"
            detail_soup = await self.get_soup(detail_url)
            if not detail_soup:
                continue

            for link in detail_soup.find_all("a"):
                text = self._clean_text(link.get_text(" ", strip=True))
                href = link.get("href")
                if not text or not href:
                    continue

                if "Закупки" in text:
                    key = "zakupki223" if path == "view223" else "zakupki44"
                    company_info["links"][key] = href
                elif "Контракты" in text:
                    company_info["links"]["contracts44"] = href

        return company_info

    async def parse_cards(self, base_link: str, pages: int = 1) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []

        for page in range(1, pages + 1):
            url = str(
                URL(f"{self.BASE_URL}{base_link}").update_query(
                    recordsPerPage="_50",
                    pageNumber=str(page),
                )
            )
            soup = await self.get_soup(url)
            if not soup:
                break

            cards = soup.find_all("div", class_="search-registry-entry-block")
            if not cards:
                break

            for card in cards:
                header_text = self._clean_text(
                    card.find("div", class_="registry-entry__header").get_text(" ", strip=True)
                    if card.find("div", class_="registry-entry__header") else None
                )
                id_match = re.search(r"\b\d{11,19}\b", header_text or "")

                object_node = card.find("div", class_="registry-entry__body-value")
                object_text = self._clean_text(object_node.get_text(" ", strip=True) if object_node else None)

                price_raw = self._get_text_by_label(card, r"(Начальная цена|Цена контракта|НМЦК)")
                price_value = self._to_float(price_raw)

                customer_text = self._get_text_by_label(card, "Заказчик")
                publication_text = self._get_text_by_label(card, "Размещено")
                submission_text = self._get_text_by_label(card, "Окончание подачи заявок")
                okpd2_text = self._get_text_by_label(card, "ОКПД2")
                region_text = self._get_text_by_label(card, "Субъект") or self._get_text_by_label(card, "Регион")
                procedure_type = self._get_text_by_label(card, "Способ определения")

                results.append(
                    {
                        "id": id_match.group(0) if id_match else None,
                        "registry_number": id_match.group(0) if id_match else None,
                        "price": price_value,
                        "price_raw": price_raw,
                        "object": object_text,
                        "customer": customer_text,
                        "customer_inn": self._extract_inn(customer_text),
                        "date": publication_text,
                        "publication_date": self._to_datetime(publication_text),
                        "submission_deadline": self._to_datetime(submission_text),
                        "okpd2_code": self._extract_first_code(okpd2_text),
                        "okpd2_text": okpd2_text,
                        "region": region_text,
                        "procedure_type": procedure_type,
                    }
                )

        return results

    async def parse_latest_tenders(self, pages: int = 4) -> list[dict[str, Any]]:
        latest_path = (
            "/epz/order/extendedsearch/results.html?searchString=&morphology=on"
            "&search-filter=%D0%94%D0%B0%D1%82%D0%B5+%D0%BE%D0%B1%D0%BD%D0%BE%D0%B2%D0%"
            "BB%D0%B5%D0%BD%D0%B8%D1%8F&sortBy=UPDATE_DATE&sortDirection=false"
            "&fz44=on&fz223=on&af=on&ca=on&pc=on&pa=on"
            "&customerIdOrg=&customerFz94id=&customerTitle=&okpd2Ids=&okpd2IdsCodes="
        )
        return await self.parse_cards(latest_path, pages=pages)
