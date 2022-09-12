import asyncio
from datetime import datetime
from worker.utils import File, Reloader

worker = Reloader(excluded_files=["main.py"])


@worker.on_file_edited
async def edited(file: File, date: datetime):
    ...
    await asyncio.sleep(2)
    print(file.name, " düzenlendi.", "\n")  # çıktı "", 0 (varsayılan değerler)
