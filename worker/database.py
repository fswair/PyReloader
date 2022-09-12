from MentoDB import Mento, MentoConnection
from worker.models import FileModel

connection = MentoConnection("./worker/database/local.db")

db = Mento(connection, default_table="files", check_model=FileModel)

db.create(model=FileModel)
#
