from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from accounts.models import User
from books.models import Book
from borrowings.models import BorrowRecord
from reviews.models import Review


class Command(BaseCommand):
    """Create repeatable sample data for local API and Postman testing."""

    help = "Create E-Library demo users, books, borrowings, and reviews."

    USERS = (
        {
            "email": "member@elibrary.demo",
            "contact_number": "9000000101",
            "role": User.Role.MEMBER,
            "first_name": "Maya",
            "last_name": "Sharma",
        },
        {
            "email": "reader2@elibrary.demo",
            "contact_number": "9000000102",
            "role": User.Role.MEMBER,
            "first_name": "Arjun",
            "last_name": "Mehta",
        },
        {
            "email": "reader3@elibrary.demo",
            "contact_number": "9000000103",
            "role": User.Role.MEMBER,
            "first_name": "Priya",
            "last_name": "Nair",
        },
        {
            "email": "librarian@elibrary.demo",
            "contact_number": "9000000104",
            "role": User.Role.LIBRARIAN,
            "first_name": "Rohan",
            "last_name": "Verma",
        },
        {
            "email": "admin@elibrary.demo",
            "contact_number": "9000000105",
            "role": User.Role.ADMIN,
            "first_name": "Neha",
            "last_name": "Kapoor",
        },
    )

    BOOKS = (
        ("Clean Code", "Robert C. Martin", "demo-9780132350884", "Programming", 4.6, 42, 5, 4),
        ("The Pragmatic Programmer", "Andrew Hunt and David Thomas", "demo-9780135957059", "Programming", 4.8, 55, 4, 3),
        ("Design Patterns", "Erich Gamma et al.", "demo-9780201633610", "Programming", 4.7, 48, 3, 3),
        ("Refactoring", "Martin Fowler", "demo-9780134757599", "Programming", 4.5, 36, 4, 4),
        ("Atomic Habits", "James Clear", "demo-9780735211292", "Self Help", 4.7, 60, 6, 5),
        ("Deep Work", "Cal Newport", "demo-9781455586691", "Self Help", 4.4, 31, 4, 4),
        ("Sapiens", "Yuval Noah Harari", "demo-9780062316097", "History", 4.6, 51, 5, 5),
        ("The Psychology of Money", "Morgan Housel", "demo-9780857197689", "Finance", 4.7, 58, 5, 5),
        ("Dune", "Frank Herbert", "demo-9780441172719", "Science Fiction", 4.5, 47, 4, 3),
        ("Project Hail Mary", "Andy Weir", "demo-9780593135204", "Science Fiction", 4.8, 63, 4, 4),
        ("The Hobbit", "J. R. R. Tolkien", "demo-9780547928227", "Fantasy", 4.7, 65, 3, 0),
        ("Educated", "Tara Westover", "demo-9780399590504", "Biography", 4.6, 29, 3, 3),
    )

    def handle(self, *args, **options):
        with transaction.atomic():
            users = self._create_users()
            books = self._create_books()
            self._create_borrowings(users, books)
            self._create_reviews(users, books)

        self.stdout.write(self.style.SUCCESS(
            "Demo data is ready. All demo account passwords are DemoPass123."
        ))

    def _create_users(self):
        users = {}
        for data in self.USERS:
            defaults = {
                **data,
                "street": "1 Library Road",
                "city": "Mumbai",
                "state": "Maharashtra",
                "country": "India",
                "postal_code": "400001",
            }
            user, created = User.objects.get_or_create(
                email=data["email"], defaults=defaults
            )
            if created:
                user.set_password("DemoPass123")
                user.save(update_fields=["password"])
            users[data["email"]] = user
        return users

    def _create_books(self):
        books = {}
        for title, author, isbn, genre, rating, borrows, total, available in self.BOOKS:
            book, _ = Book.objects.update_or_create(
                isbn=isbn,
                defaults={
                    "title": title,
                    "author": author,
                    "description": f"A demo description for {title}.",
                    "genre": genre,
                    "publisher": "E-Library Demo Press",
                    "published_year": 2024,
                    "language": "English",
                    "total_copies": total,
                    "available_copies": available,
                    "borrow_count": borrows,
                    "average_rating": rating,
                    "status": Book.Status.AVAILABLE if available else Book.Status.OUT_OF_STOCK,
                },
            )
            books[title] = book
        return books

    def _create_borrowings(self, users, books):
        # Shared reading history powers the collaborative recommendations API.
        history = {
            "member@elibrary.demo": ["Clean Code", "Design Patterns", "Refactoring"],
            "reader2@elibrary.demo": ["Clean Code", "Design Patterns", "The Pragmatic Programmer"],
            "reader3@elibrary.demo": ["Clean Code", "Refactoring", "Atomic Habits"],
        }
        now = timezone.now()
        for email, titles in history.items():
            for index, title in enumerate(titles):
                record, created = BorrowRecord.objects.get_or_create(
                    user=users[email],
                    book=books[title],
                    status=BorrowRecord.Status.RETURNED,
                    defaults={"returned_at": now - timedelta(days=index + 1)},
                )
                if created:
                    record.borrowed_at = now - timedelta(days=index + 15)
                    record.due_date = now - timedelta(days=index + 1)
                    record.save(update_fields=["borrowed_at", "due_date"])

    def _create_reviews(self, users, books):
        reviews = (
            ("member@elibrary.demo", "Clean Code", 5, "Clear and practical guidance for developers."),
            ("reader2@elibrary.demo", "Design Patterns", 5, "A useful reference for software design."),
            ("reader3@elibrary.demo", "Atomic Habits", 4, "Simple ideas that are easy to apply."),
        )
        for email, title, rating, review_text in reviews:
            Review.objects.get_or_create(
                user=users[email],
                book=books[title],
                defaults={"rating": rating, "review_text": review_text},
            )
