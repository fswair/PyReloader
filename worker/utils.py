from asyncio import iscoroutinefunction
import asyncio
from datetime import datetime
from logging import Logger
import subprocess as cmd
import enum
import os
from pathlib import Path
from random import randint
from time import time, sleep
from typing import Callable
from .database import db
from .models import FileModel

EXCEPTION: str = "An exception has occured while trigger is sending.."

class NoArgumentSupplied(Exception):
    ...

class Priotries(enum.Enum):
    HIGH: "Priotries.HIGH" = enum.auto()
    LOW: "Priotries.LOW" = enum.auto()

class File:
    logger: Logger
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
        raise NoArgumentSupplied("Please specify `id` argument or set `all` as true")

    def reload(self):
        db.drop("files")
        db.create("files", model=FileModel)

        return "Reloaded"


class FileEnums:
    CREATED: enum.Enum = "created"
    DELETED: enum.Enum = "deleted"


class Reloader:
    def __init__(self, excluded_files: list = list()):
        self.funcs = list()
        self.jobs = dict()
        self.excluded_files = excluded_files or "main.py"
        self.coro = lambda func: iscoroutinefunction(func)
        self.new_job = lambda file: cmd.Popen(f"python3 {file}", shell=True, stdout=open("stdout","a"))
        self.loop = True
        self.logger = Logger(__name__)
        self.triggers = dict()
        self.responses = dict()
        "The response dict coming from process (for running triggers)"
    def main_file(self, __file: str):
        return __file.split("/")[-1]
    
    def set_files(self, excluded_files: list = []):
        f = File()
        f.reload()
        self.excluded_files = excluded_files
        br = "\n"
        self.logger.error(f"""[FILES_EXCLUDED] The files excluded below:\n{br.join(excluded_files)}""")
        return self.logger.error("[SET_FILES] File and path settings saved")

    def set_trigger(self, target: Callable, priotry: Priotries = None):
        if not priotry == Priotries.HIGH:
            self.triggers.update({len(self.triggers): {"func": target}})
            return self.triggers
        else:
            triggers = {}
            triggers["HIGH"] = {"func": target}
            triggers.update(self.triggers)
            self.triggers = triggers
            return self.triggers
    
    async def call_triggers(self, delay: int = 0.5, *args, **kwargs):
        responses = {}
        for k,v in self.triggers.items():
            if k == "HIGH":
                func = v["func"]
                try:
                    resp = func(*args, **kwargs)
                    responses[k] = {"func": func, "resp": resp}
                    print("[IMPORTANT] The process sent.. (marked as HIGH priotry)")
                except:
                    responses[k] = {"func": func, "resp": EXCEPTION}
                    print("[EXCEPTION] The process can not send.. (marked as HIGH priotry)")
            else:
                try:
                    resp = func(*args, **kwargs)
                    responses[k] = {"func": func, "resp": resp}
                    print(f"[TRIGGER({k})] The process sent..")
                except:
                    responses[k] = {"func": func, "resp": EXCEPTION}
                    print("[EXCEPTION] The process can not send..")
            await asyncio.sleep(delay)
        return responses

    async def on(self):
        while self.loop:
            await asyncio.sleep(1)
            try:
                files = os.listdir(os.getcwd())
                for f in files:
                    IOF = Path(f)
                    if not IOF.is_file():
                        continue
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
                    print(file_stat.st_mtime, current.modified_unix)
                    if file_stat.st_mtime != current.modified_unix:
                        print(714)
                        if current.id:
                            file.update()
                        else:
                            file.id = randint(10000, 99999)
                            file.add()
                        if current.id:
                            file.id = current.id
                            file.update()
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

                        if self.jobs:
                            process: cmd.Popen = self.jobs[file.id]["process"]
                            process.kill()
                            process = self.new_job(f)
                            self.jobs.update(
                                {file.id: {"process": process, "file": file}}
                            )

                            for func in self.funcs:
                                date = datetime.utcfromtimestamp(time())
                                self.logger.error(
                                    f"[EDITED] {f} dosyası düzenlendi ve çalıştırılıyor"
                                )
                                setattr(file, "logger", self.logger)
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
        self.logger.error("[ACTIVE] RELOADER IS ON!")
        asyncio.get_event_loop().run_until_complete(self.on())
