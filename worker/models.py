from MentoDB import BaseModel, PrimaryKey, UniqueMatch
from dataclasses import dataclass

@dataclass
class FileModel:
    id: int
    size: int
    directory: str
    name: PrimaryKey(str)
    created_unix: int
    modified_unix: int
    status: str
    # unique constraint
    unique_match: UniqueMatch("name", "id")
