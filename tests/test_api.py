import unittest

import httpx

from main import app, books


class BookApiTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        books.clear()
        self.client = httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://test",
        )

    async def asyncTearDown(self) -> None:
        await self.client.aclose()

    async def test_homepage_serves_book_ui(self) -> None:
        response = await self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertIn("My Reading List", response.text)

    async def test_add_list_and_filter_books(self) -> None:
        created = await self.client.post(
            "/books",
            json={"title": "Dune", "author": "Frank Herbert", "status": "to-read"},
        )

        self.assertEqual(created.status_code, 201)
        book = created.json()
        self.assertEqual(book["title"], "Dune")

        all_books = await self.client.get("/books")
        self.assertEqual(all_books.json(), [book])

        filtered = await self.client.get("/books", params={"status": "to-read"})
        self.assertEqual(filtered.json(), [book])

        no_matches = await self.client.get("/books", params={"status": "done"})
        self.assertEqual(no_matches.json(), [])

    async def test_invalid_status_is_rejected(self) -> None:
        response = await self.client.post(
            "/books",
            json={"title": "Dune", "author": "Frank Herbert", "status": "finished"},
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual((await self.client.get("/books")).json(), [])

    async def test_patch_updates_status_and_aggregation(self) -> None:
        created = await self.client.post(
            "/books",
            json={"title": "Dune", "author": "Frank Herbert", "status": "to-read"},
        )
        book_id = created.json()["id"]

        updated = await self.client.patch(
            f"/books/{book_id}", json={"status": "reading"}
        )

        self.assertEqual(updated.status_code, 200)
        self.assertEqual(updated.json()["status"], "reading")
        counts = await self.client.get("/books/count-by-status")
        self.assertEqual(counts.json(), {"to-read": 0, "reading": 1, "done": 0})


if __name__ == "__main__":
    unittest.main()
