import asyncio
import httpx
from bs4 import BeautifulSoup


class AsyncParserZakazi:
    def __init__(self):
        self.zakaz_all = []
        self.fast_zakaz_all = []
        self.second_one = 0
        self.seen_ids = set()

        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/90.0.4430.93 Safari/537.36"
            )
        }

        # ограничение одновременных запросов
        self.semaphore = asyncio.Semaphore(5)

    async def fetch(self, client, url, retries=3):
        for _ in range(retries):
            try:
                async with self.semaphore:
                    response = await client.get(url, timeout=10)
                    if response.status_code == 200:
                        return response.text
            except Exception:
                await asyncio.sleep(1)
        return None

    async def parse_page(self, client, count):
        url = (
            "https://zakupki.gov.ru/epz/order/extendedsearch/results.html?"
            f"pageNumber={count + 1}&sortBy=UPDATE_DATE"
        )

        html = await self.fetch(client, url)
        if not html:
            return []

        soup = BeautifulSoup(html, "html.parser")
        return soup.find_all(
            "div",
            class_="search-registry-entry-block box-shadow-search-input"
        )

    def do_zakaz(self, zakaz):
        try:
            id_stat_block = zakaz.find(
                "div",
                class_="d-flex registry-entry__header-mid align-items-center"
            )
            right_block = zakaz.find(
                "div",
                class_="col col d-flex flex-column registry-entry__right-block b-left"
            )

            if not id_stat_block or not right_block:
                return None

            data_block = right_block.find("div", class_="data-block mt-auto")
            published = data_block.find_all("div", "col-6")

            date_published = published[0].find(
                "div", class_="data-block__value"
            ).get_text(strip=True)

            date_update = published[1].find(
                "div", class_="data-block__value"
            ).get_text(strip=True)

            status = id_stat_block.find(
                "div",
                class_="registry-entry__header-mid__title text-normal"
            ).get_text(strip=True)

            title = zakaz.find(
                "div", class_="registry-entry__body-block"
            ).get_text(strip=True)

            id_element = id_stat_block.find("a")
            id_text = id_element.get_text(strip=True)

            zakazchik_block = zakaz.find(
                "div", class_="registry-entry__body-href"
            )
            zakazchik = zakazchik_block.get_text(strip=True)

            price = right_block.find(
                "div", class_="price-block__value"
            ).get_text(strip=True)

            if id_text in self.seen_ids:
                return None

            self.seen_ids.add(id_text)

            return {
                "date_published": date_published,
                "date_update": date_update,
                "status": status,
                "title": title,
                "id": id_text,
                "zakaz_href": "https://zakupki.gov.ru/" + id_element["href"],
                "zakazchik": zakazchik,
                "price": price,
                "rows": []
            }

        except Exception:
            return None

    async def do_inside_zakaz(self, client, data):
        if not data:
            return None

        html = await self.fetch(client, data["zakaz_href"])
        if not html:
            return data

        soup = BeautifulSoup(html, "html.parser")

        main = soup.find_all("section", class_="blockInfo__section section")
        if not main:
            main = soup.find_all("div", class_="col-9 mr-auto")
            if main:
                self.second_one += 1

        for row in main:
            try:
                title_elem = row.find("span", class_="section__title")
                value_elem = row.find("span", class_="section__info")

                if not title_elem:
                    title_elem = row.find("div", class_="common-text__title")
                    value_elem = row.find("div", class_="common-text__value")

                if title_elem and value_elem:
                    data["rows"].append({
                        title_elem.get_text(strip=True):
                        value_elem.get_text(strip=True)
                    })

            except Exception:
                continue

        return data

    async def process_page(self, client, page):
        zakazi = await self.parse_page(client, page)

        tasks = []
        for z in zakazi:
            data = self.do_zakaz(z)
            if data:
                tasks.append(self.do_inside_zakaz(client, data))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        for r in results:
            if isinstance(r, dict):
                self.zakaz_all.append(r)

    async def run(self, pages=2):
        async with httpx.AsyncClient(headers=self.headers) as client:
            tasks = [self.process_page(client, i) for i in range(pages)]
            await asyncio.gather(*tasks)

        return self.zakaz_all


async def main():
    parser = AsyncParserZakazi()
    data = await parser.run(pages=2)
    return data
if __name__ == "__main__":
    data = asyncio.run(main())
    for i in data:
        print(i)
    if not data:
        print("pusto")
