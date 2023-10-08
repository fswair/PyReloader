from MentoDB import Mento, MentoConnection
from .models import FileModel

connection = MentoConnection("./worker/local.db")

db = Mento(connection, check_model=FileModel)
db.create("files", model=FileModel)
