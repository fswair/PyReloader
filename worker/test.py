import asyncio
from datetime import datetime
from .utils import File, Reloader
worker = Reloader()
@worker.on_file_edited
async def edited(file: File, date: datetime):
    worker.responses = await worker.call_triggers(file=file, date=date)
    await asyncio.sleep(2)
    file.logger.error("[EDITED] {} edited and reloaded.".format(file.name))
