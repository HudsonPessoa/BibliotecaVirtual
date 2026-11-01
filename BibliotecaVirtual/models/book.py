from dataclasses import asdict, dataclass
from typing import Optional


@dataclass(frozen=True)
class Book:
    id: Optional[int]
    title: str
    author: str
    genre: str
    year: int
    isbn: Optional[str]
    description: str
    status: str

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_row(cls, row):
        return cls(
            id=row["id"],
            title=row["title"],
            author=row["author"],
            genre=row["genre"],
            year=row["year"],
            isbn=row["isbn"],
            description=row["description"],
            status=row["status"],
        )
