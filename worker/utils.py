from asyncio import iscoroutinefunction
import asyncio
from datetime import datetime
from logging import Logger
import subprocess as cmd
import enum
import os
from random import randint
from time import time
from typing import Callable
from worker.database import db
from worker.models import FileModel
from apscheduler.schedulers.asyncio import AsyncIOScheduler


class NoArgumentSupplied(Exception):
    ...


class File:
    def __init__(
        self,
        id: int = 0,
        size: int = 0,
        directory: str = "",
        name: str = "",
        created_unix: int = 0,
        modified_unix: int = 0,
        status: str = "",
    ):
        self.id: int = id
        self.size: int = size
        self.directory: str = directory
        self.name: str = name
        self.created_unix: int = created_unix
        self.modified_unix: int = modified_unix
        self.status: str = status

    def add(self):
        db.insert(
            "files",
            data=dict(
                id=self.id,
                size=self.size,
                directory=self.directory,
                name=self.name,
                created_unix=self.created_unix,
                modified_unix=self.modified_unix,
                status=self.status,
            ),
            check_model=FileModel,
        )

    def update(self, update_all: bool = True):
        db.delete("files", where=dict(id=self.id))
        db.insert(
            "files",
            data=dict(
                id=self.id,
                size=self.size,
                directory=self.directory,
                name=self.name,
                created_unix=self.created_unix,
                modified_unix=self.modified_unix,
                status=self.status,
            ),
        )

        return db.select("files", where=dict(id=self.id))

    def delete(self):
        db.delete("files", where=dict(id=self.id))

    def get(self, where: dict = dict(), all: bool = True):
        if where:
            datas = db.select("files", where=where)
            if datas:
                data = datas[0]
                return File(**data)
            return File()
        elif all:
            datas = db.select("files")
            if datas:
                datas = [File(**data) for data in datas]
                return datas
            return datas
        raise NoArgumentSupplied("Please specify `id` argument or set `all` as true.")

    def reload(self):
        db.drop("files")
        db.create(model=FileModel)

        return "Reloaded."


class FileEnums:
    CREATED: enum.Enum = "created"
    DELETED: enum.Enum = "deleted"


class Reloader:
    def __init__(self, excluded_files: list = list()):
        self.funcs = list()
        self.jobs = dict()
        self.excluded_files = excluded_files
        self.coro = lambda func: iscoroutinefunction(func)
        self.new_job = lambda file: cmd.Popen(f"python {file}", shell=True)
        self.loop = True
        self.logger = Logger(__name__)

    async def on(self):
        while self.loop:
            await asyncio.sleep(1)
            try:
                files = os.listdir(os.getcwd())
                for f in files:
                    await asyncio.sleep(0.5)
                    if not f.endswith(".py") or f in self.excluded_files:
                        continue
                    file_stat = os.stat(f)

                    file = File()
                    file.created_unix = file_stat.st_ctime
                    file.modified_unix = file_stat.st_mtime
                    file.name = f
                    file.directory = os.getcwd()
                    file.size = file_stat.st_size
                    file.status = FileEnums.CREATED

                    current = file.get(where=dict(name=file.name))
                    if current.id:
                        file.id = current.id
                        file.update()
                    else:
                        file.id = randint(10000, 99999)
                        file.add()

                    file = file.get(
                        where=dict(directory=file.directory, name=file.name)
                    )

                    process = self.new_job(f)
                    self.jobs.update(
                        {
                            file.id: {
                                "process": process,
                                "file": file,
                            }
                        }
                    )

                    file_stat = os.stat(f)

                    if not file.id:
                        continue
                    if not file_stat.st_mtime == file.modified_unix:
                        if self.jobs:
                            process: cmd.Popen = self.jobs[file.id]["process"]
                            process.kill()
                            process = self.new_job(f)
                            self.jobs.update(
                                {file.id: {"process": process, "file": file}}
                            )

                            for func in self.funcs:
                                date = datetime.utcfromtimestamp(time())
                                self.logger.info(
                                    f"{f} dosyası düzenlendi ve çalıştırılıyor.."
                                )
                                if self.coro(func):
                                    await func(file, date)
                                else:
                                    func(file, date)
                    else:
                        continue
            except Exception as e:
                self.logger.warn(f"Error: [{e}]")
                await self.on()

    def on_file_edited(self, func: Callable):
        self.funcs.append(func)

    def run(self):
        self.logger.info("[ACTIVE] RELOADER IS ON!")
        asyncio.get_event_loop().run_until_complete(self.on())
