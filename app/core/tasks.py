import asyncio


async def hourly_parser():
    while True:
        try:
            print("Запуск парсинга...")
            # await parser.run()
            print("Парсинг окончен.")
        except Exception as e:
            print(f"Ошибка: {e}")

        await asyncio.sleep(3600)