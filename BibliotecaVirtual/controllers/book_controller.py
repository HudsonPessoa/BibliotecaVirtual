import logging
import re
import sqlite3
from urllib.parse import parse_qs

from models.book import Book
from models.book_repository import BookRepository


class BookController:
    FIELDS = {"title", "author", "genre", "year", "isbn", "description", "status"}
    STATUSES = {"available", "borrowed"}

    def __init__(self, repository: BookRepository):
        self.repository = repository

    def handle(self, method, path, query="", payload=None):
        match = re.fullmatch(r"/api/books(?:/([1-9]\d*))?", path)
        if not match:
            return 404, {"error": "Rota não encontrada."}

        book_id = int(match.group(1)) if match.group(1) else None
        try:
            if method == "GET":
                return self._get(book_id, query)
            if method == "POST" and book_id is None:
                return self._create(payload)
            if method == "PUT" and book_id is not None:
                return self._update(book_id, payload)
            if method == "DELETE" and book_id is not None:
                return self._delete(book_id)
            return 405, {"error": "Método não permitido para esta rota."}
        except sqlite3.IntegrityError:
            return 409, {"error": "Este ISBN já está cadastrado na biblioteca."}
        except sqlite3.Error:
            logging.exception("Erro ao acessar o banco de dados da biblioteca.")
            return 500, {"error": "Não foi possível acessar os dados da biblioteca."}

    def _get(self, book_id, query):
        if book_id is not None:
            book = self.repository.get_by_id(book_id)
            return (200, book.to_dict()) if book else (404, {"error": "Livro não encontrado."})

        books = self.repository.list_all()
        filters = parse_qs(query, keep_blank_values=False)
        search = filters.get("search", [""])[0].strip().casefold()
        genre = filters.get("genre", [""])[0].strip().casefold()
        status = filters.get("status", [""])[0].strip()
        if status and status not in self.STATUSES:
            return 400, {"error": "Filtro de disponibilidade inválido."}

        if search:
            books = [
                book
                for book in books
                if search in book.title.casefold()
                or search in book.author.casefold()
                or search in book.genre.casefold()
            ]
        if genre:
            books = [book for book in books if book.genre.casefold() == genre]
        if status:
            books = [book for book in books if book.status == status]
        return 200, {"books": [book.to_dict() for book in books], "total": len(books)}

    def _create(self, payload):
        book, error = self._parse_book(payload)
        if error:
            return 400, {"error": error}
        return 201, self.repository.create(book).to_dict()

    def _update(self, book_id, payload):
        book, error = self._parse_book(payload)
        if error:
            return 400, {"error": error}
        updated = self.repository.update(book_id, book)
        return (200, updated.to_dict()) if updated else (404, {"error": "Livro não encontrado."})

    def _delete(self, book_id):
        if not self.repository.delete(book_id):
            return 404, {"error": "Livro não encontrado."}
        return 200, {"message": "Livro removido com sucesso."}

    def _parse_book(self, payload):
        if not isinstance(payload, dict):
            return None, "O corpo da solicitação deve ser um objeto JSON."

        missing = {"title", "author", "genre", "year", "status"} - payload.keys()
        if missing:
            return None, "Preencha título, autor, gênero, ano e disponibilidade."

        text_fields = {
            "title": ("título", 150, True),
            "author": ("autor", 120, True),
            "genre": ("gênero", 60, True),
            "isbn": ("ISBN", 20, False),
            "description": ("descrição", 2000, False),
        }
        values = {}
        for field, (label, limit, required) in text_fields.items():
            value = payload.get(field, "")
            if not isinstance(value, str):
                return None, f"O campo {label} deve ser um texto."
            value = value.strip()
            if required and not value:
                return None, f"O campo {label} é obrigatório."
            if len(value) > limit:
                return None, f"O campo {label} deve ter no máximo {limit} caracteres."
            values[field] = value or None if field == "isbn" else value

        year = payload["year"]
        if isinstance(year, bool) or not isinstance(year, int) or not 1 <= year <= 9999:
            return None, "Informe um ano válido entre 1 e 9999."

        status = payload["status"]
        if not isinstance(status, str) or status not in self.STATUSES:
            return None, "A disponibilidade deve ser 'available' ou 'borrowed'."

        isbn = values["isbn"]
        if isbn and not re.fullmatch(r"[\dXx-]{8,20}", isbn):
            return None, "Informe um ISBN válido, usando apenas números, hífens ou X."

        return (
            Book(
                id=None,
                title=values["title"],
                author=values["author"],
                genre=values["genre"],
                year=year,
                isbn=isbn,
                description=values["description"],
                status=status,
            ),
            None,
        )
