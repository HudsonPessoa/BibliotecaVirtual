from contextlib import contextmanager
import sqlite3
from pathlib import Path
from typing import Optional

from models.book import Book


class BookRepository:
    def __init__(self, database_path: Path, seed: bool = True):
        self.database_path = Path(database_path)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize(seed)

    @contextmanager
    def _connect(self):
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    def _initialize(self, seed):
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS books (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    author TEXT NOT NULL,
                    genre TEXT NOT NULL,
                    year INTEGER NOT NULL,
                    isbn TEXT UNIQUE,
                    description TEXT NOT NULL DEFAULT '',
                    status TEXT NOT NULL CHECK (status IN ('available', 'borrowed'))
                )
                """
            )
            count = connection.execute("SELECT COUNT(*) FROM books").fetchone()[0]
            if seed and count == 0:
                connection.executemany(
                    """
                    INSERT INTO books (title, author, genre, year, isbn, description, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    [
                        (
                            "Dom Casmurro",
                            "Machado de Assis",
                            "Romance",
                            1899,
                            "978-85-359-0277-5",
                            "Um clássico da literatura brasileira sobre memória, ciúme e as versões de uma mesma história.",
                            "available",
                        ),
                        (
                            "O Alienista",
                            "Machado de Assis",
                            "Ficção",
                            1882,
                            "978-85-359-0276-8",
                            "Uma sátira sobre ciência, poder e os limites entre razão e loucura.",
                            "available",
                        ),
                        (
                            "A Hora da Estrela",
                            "Clarice Lispector",
                            "Romance",
                            1977,
                            "978-85-7164-731-1",
                            "A trajetória de Macabéa, uma jovem que tenta encontrar seu lugar no mundo.",
                            "borrowed",
                        ),
                        (
                            "O Hobbit",
                            "J. R. R. Tolkien",
                            "Fantasia",
                            1937,
                            "978-85-336-2277-5",
                            "Uma viagem inesperada transforma a vida tranquila de um hobbit.",
                            "available",
                        ),
                        (
                            "A Revolução dos Bichos",
                            "George Orwell",
                            "Ficção",
                            1945,
                            "978-85-359-0288-1",
                            "Uma fábula sobre revolução, poder e os rumos de uma comunidade.",
                            "borrowed",
                        ),
                        (
                            "Quarto de Despejo",
                            "Carolina Maria de Jesus",
                            "Biografia",
                            1960,
                            "978-85-359-0279-9",
                            "Registros do cotidiano e das observações de uma escritora brasileira.",
                            "available",
                        ),
                    ],
                )

    def list_all(self):
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT * FROM books ORDER BY title COLLATE NOCASE, id"
            ).fetchall()
        return [Book.from_row(row) for row in rows]

    def get_by_id(self, book_id: int) -> Optional[Book]:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM books WHERE id = ?", (book_id,)
            ).fetchone()
        return Book.from_row(row) if row else None

    def create(self, book: Book) -> Book:
        with self._connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO books (title, author, genre, year, isbn, description, status)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                self._values(book),
            )
            book_id = cursor.lastrowid
        created = self.get_by_id(book_id)
        if created is None:
            raise RuntimeError("O livro criado não foi encontrado.")
        return created

    def update(self, book_id: int, book: Book) -> Optional[Book]:
        with self._connect() as connection:
            cursor = connection.execute(
                """
                UPDATE books
                SET title = ?, author = ?, genre = ?, year = ?, isbn = ?,
                    description = ?, status = ?
                WHERE id = ?
                """,
                (*self._values(book), book_id),
            )
            if cursor.rowcount == 0:
                return None
        return self.get_by_id(book_id)

    def delete(self, book_id: int) -> bool:
        with self._connect() as connection:
            cursor = connection.execute("DELETE FROM books WHERE id = ?", (book_id,))
        return cursor.rowcount > 0

    @staticmethod
    def _values(book: Book):
        return (
            book.title,
            book.author,
            book.genre,
            book.year,
            book.isbn,
            book.description,
            book.status,
        )
