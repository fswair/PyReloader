from MentoDB import BaseModel, dataclass, PrimaryKey, UniqueMatch


@dataclass
class FileModel(BaseModel):
    id: int
    size: int
    directory: str
    name: PrimaryKey(str).set_primary()
    created_unix: int
    modified_unix: int
    status: str
    # unique constraint
    unique_match: UniqueMatch("name", "id").set_match()
