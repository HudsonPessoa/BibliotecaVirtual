import tempfile
import unittest
from pathlib import Path

from controllers.book_controller import BookController
from models.book_repository import BookRepository


class BookControllerTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        repository = BookRepository(Path(self.temp_dir.name) / "books.db", seed=False)
        self.controller = BookController(repository)
        self.book = {
            "title": "Leituras de teste",
            "author": "Autora Exemplo",
            "genre": "Romance",
            "year": 2024,
            "isbn": "",
            "description": "Uma descrição.",
            "status": "available",
        }

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_create_list_update_and_delete_book(self):
        status, created = self.controller.handle("POST", "/api/books", payload=self.book)
        self.assertEqual(status, 201)
        self.assertGreater(created["id"], 0)

        status, listing = self.controller.handle("GET", "/api/books")
        self.assertEqual(status, 200)
        self.assertEqual(listing["total"], 1)
        self.assertEqual(listing["books"][0]["title"], self.book["title"])

        updated_payload = {**self.book, "title": "Título atualizado", "status": "borrowed"}
        status, updated = self.controller.handle(
            "PUT", f"/api/books/{created['id']}", payload=updated_payload
        )
        self.assertEqual(status, 200)
        self.assertEqual(updated["title"], "Título atualizado")
        self.assertEqual(updated["status"], "borrowed")

        status, deleted = self.controller.handle("DELETE", f"/api/books/{created['id']}")
        self.assertEqual(status, 200)
        self.assertIn("message", deleted)
        status, listing = self.controller.handle("GET", "/api/books")
        self.assertEqual(status, 200)
        self.assertEqual(listing["total"], 0)

    def test_create_rejects_missing_required_fields(self):
        status, result = self.controller.handle(
            "POST", "/api/books", payload={"title": "Sem os demais dados"}
        )
        self.assertEqual(status, 400)
        self.assertIn("Preencha", result["error"])

    def test_create_rejects_invalid_year_and_status(self):
        invalid_year = {**self.book, "year": True}
        status, result = self.controller.handle("POST", "/api/books", payload=invalid_year)
        self.assertEqual(status, 400)
        self.assertIn("ano válido", result["error"])

        invalid_status = {**self.book, "status": "lost"}
        status, result = self.controller.handle("POST", "/api/books", payload=invalid_status)
        self.assertEqual(status, 400)
        self.assertIn("disponibilidade", result["error"])

    def test_duplicate_isbn_returns_conflict(self):
        first = {**self.book, "isbn": "978-85-1234"}
        self.assertEqual(self.controller.handle("POST", "/api/books", payload=first)[0], 201)
        status, result = self.controller.handle("POST", "/api/books", payload=first)
        self.assertEqual(status, 409)
        self.assertIn("ISBN", result["error"])

    def test_list_filters_by_search_and_status(self):
        self.controller.handle("POST", "/api/books", payload=self.book)
        other = {**self.book, "title": "Outro livro", "status": "borrowed"}
        self.controller.handle("POST", "/api/books", payload=other)

        status, result = self.controller.handle(
            "GET", "/api/books", query="search=leituras&status=available"
        )
        self.assertEqual(status, 200)
        self.assertEqual(result["total"], 1)
        self.assertEqual(result["books"][0]["title"], self.book["title"])

    def test_missing_book_and_invalid_route_return_not_found(self):
        self.assertEqual(self.controller.handle("GET", "/api/books/123")[0], 404)
        self.assertEqual(self.controller.handle("GET", "/api/other")[0], 404)


if __name__ == "__main__":
    unittest.main()
