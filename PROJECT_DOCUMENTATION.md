# E-Library Management System

## Complete API and Feature Documentation

## 1. Product overview

E-Library is a backend service for a digital or hybrid library. It is designed around the day-to-day experience of two groups:

- **Readers** can create an account, find books, borrow available titles, review what they read, and request AI help to understand or write about a book.
- **Library teams** can maintain the catalogue and use a protected analytics area to understand collection usage.

The project is API-first. A web, mobile, or desktop client can use the same predictable JSON endpoints. It does not include a frontend by design.

## 2. Main features at a glance

| Feature | Value it provides |
| --- | --- |
| Email-based accounts | A clear, familiar sign-in identity for every user |
| JWT authentication | Stateless, client-friendly access to protected endpoints |
| Roles | Separates reader actions from staff catalogue and analytics operations |
| Book catalogue | Stores rich metadata, stock information, ratings, and cover links |
| Discovery tools | Helps users find relevant titles without downloading the whole catalogue |
| Borrowing lifecycle | Keeps a user's borrowing history and inventory accurate |
| Reviews | Captures reader feedback and maintains each book's rating average |
| AI summaries | Gives quick or deeper reading support without repeated provider calls |
| AI review draft | Helps a reader turn their own notes and rating into a draft review |
| Analytics | Gives staff concise, reliable collection and usage information |
| Recommendations | Helps readers discover personalised, related, and trending books |

## 3. Technology and architecture

### Technology stack

| Layer | Choice |
| --- | --- |
| Framework | Python, Django 6.1, Django REST Framework |
| Authentication | `djangorestframework-simplejwt` |
| Local database | SQLite |
| Cache | Redis through `django-redis` |
| AI provider | UserFacet AI API through `requests` |
| Discovery | `django-filter`, DRF search and ordering filters |
| Schema foundation | `drf-spectacular` |

### Application structure

```text
config/        Project settings and root routes
accounts/      User accounts, registration, login
books/         Catalogue, search, filters, staff CRUD
borrowings/    Borrow, return, and history
reviews/       Ratings, written reviews, AI review drafts
ai_summary/    Generated summaries, cache, generation state
analytics/     Library operational reporting
recommendations/ Personalised, collaborative, and trending discovery
```

### Request lifecycle

```text
Client request
  -> URL routing
  -> JWT authentication and permission check
  -> API view or viewset
  -> serializer validation / service or manager logic
  -> Django ORM database work
  -> optional Redis cache or UserFacet AI call
  -> JSON response
```

This separation is intentional. Views are responsible for HTTP concerns, serializers validate input and shape output, and services/managers contain reusable business or integration logic.

### Reliability choices

- Borrow and return actions are wrapped in transactions and use row locks around inventory data.
- The AI provider is called outside a database transaction, so a slow external request does not keep database rows locked.
- Generated summaries have a durable database record as well as a Redis cache. Redis failures are ignored safely; the database remains the source of truth.
- Ranking queries are limited to ten items and use deterministic secondary sorting for ties.
- Recommendation queries use database aggregation for co-borrow counts and return only compact book-card fields.

## 4. Setup

### Requirements

- Python and `pip`
- Redis on `127.0.0.1:6379` for summary caching (recommended)
- A UserFacet AI API token for live AI features

### Install

```bash
git clone <repository-url>
cd e-library
python -m venv venv
```

Windows PowerShell:

```powershell
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

macOS/Linux:

```bash
source venv/bin/activate
pip install -r requirements.txt
```

Create `.env` in the repository root:

```env
AI_API_TOKEN=your-userfacet-api-token
```

Start Redis, then run:

```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

The local server is `http://127.0.0.1:8000/`.

### Test and validate

```bash
python manage.py check
python manage.py test
python manage.py makemigrations --check
```

## 5. Authentication and roles

### Sending a token

After login, add the access token to every protected request:

```http
Authorization: Bearer <access-token>
Content-Type: application/json
```

### Roles and permissions

| Capability | Public visitor | Member | Librarian | Admin |
| --- | --- | --- | --- | --- |
| Register and login | Yes | Yes | Yes | Yes |
| Browse books and reviews | Yes | Yes | Yes | Yes |
| Borrow, return, view own history | No | Yes | Yes | Yes |
| Create a review / use AI tools | No | Yes | Yes | Yes |
| Receive personalised recommendations | No | Yes | Yes | Yes |
| View related and trending recommendations | Yes | Yes | Yes | Yes |
| Create, edit, delete books | No | No | Yes | Yes |
| View analytics | No | No | Yes | Yes |

### Shared response rules

| Situation | Typical status |
| --- | --- |
| Valid read | `200 OK` |
| Resource created | `201 Created` |
| Invalid fields or business rule | `400 Bad Request` |
| Login/token missing or invalid | `401 Unauthorized` or `403 Forbidden` |
| Valid user lacks role | `403 Forbidden` |
| Resource does not exist | `404 Not Found` |
| Summary is currently generated elsewhere | `202 Accepted` |
| AI provider failed | `502 Bad Gateway` |

## 6. Accounts app

### What this app does

The accounts app owns the custom `User` model. It uses a unique email as the login identity instead of Django's default username. A user also has first, middle, and last names, a unique contact number, address fields, a role, and normal account flags/timestamps.

Roles are `MEMBER`, `LIBRARIAN`, and `ADMIN`. Passwords are hashed by Django and are never returned in API responses.

> Security note: the registration serializer currently accepts `role` in the request. For an internet-facing application, restrict role assignment so only authorised staff can create librarian and admin accounts.

### Register an account

`POST /api/auth/register/` — Public

Required: `first_name`, `last_name`, `email`, `contact_number`, `street`, `city`, `state`, `country`, `postal_code`, and `password`. `middle_name` is optional, and `role` defaults to `MEMBER` when omitted. Password length must be at least six characters.

```json
{
  "first_name": "Ada",
  "middle_name": "",
  "last_name": "Lovelace",
  "email": "ada@example.com",
  "contact_number": "9876543210",
  "street": "12 Example Street",
  "city": "London",
  "state": "Greater London",
  "country": "United Kingdom",
  "postal_code": "SW1A 1AA",
  "role": "MEMBER",
  "password": "safe-pass-123"
}
```

Successful response — `201 Created`:

```json
{
  "id": 1,
  "first_name": "Ada",
  "middle_name": "",
  "last_name": "Lovelace",
  "email": "ada@example.com",
  "contact_number": "9876543210",
  "street": "12 Example Street",
  "city": "London",
  "state": "Greater London",
  "country": "United Kingdom",
  "postal_code": "SW1A 1AA",
  "role": "MEMBER"
}
```

Example validation response — `400 Bad Request`:

```json
{
  "email": ["user with this email already exists."],
  "contact_number": ["user with this contact number already exists."]
}
```

### Login

`POST /api/auth/login/` — Public

```json
{
  "email": "ada@example.com",
  "password": "safe-pass-123"
}
```

Successful response — `200 OK`:

```json
{
  "user": {
    "id": 1,
    "email": "ada@example.com",
    "first_name": "Ada",
    "last_name": "Lovelace",
    "role": "MEMBER"
  },
  "access": "<access-token>",
  "refresh": "<refresh-token>"
}
```

Invalid credentials or an inactive account return `400 Bad Request` with a validation error.

### Refresh an access token

`POST /api/auth/refresh/` — Send a valid refresh token

```json
{ "refresh": "<refresh-token>" }
```

Successful response — `200 OK`:

```json
{ "access": "<new-access-token>" }
```

## 7. Books app

### What this app does

The books app is the catalogue. A `Book` stores title, author, unique ISBN, description, genre, publisher, publication year, language, stock counts, cumulative borrow count, average rating, an optional cover-image URL, status, and timestamps.

The API allows everyone to browse the catalogue. Only librarians and administrators can change it. The serializer prevents impossible inventory input: `available_copies` cannot be greater than `total_copies`.

The app also contains a `Wishlist` model with one unique user/book relationship. It is reserved for future work; no wishlist API endpoint is exposed yet.

### List books

`GET /api/books/` — Public

The response is paginated (10 results by default):

```json
{
  "count": 1,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 7,
      "title": "Clean Code",
      "author": "Robert C. Martin",
      "isbn": "9780132350884",
      "description": "A guide to software craftsmanship.",
      "genre": "Programming",
      "publisher": "Prentice Hall",
      "published_year": 2008,
      "language": "English",
      "total_copies": 4,
      "available_copies": 3,
      "borrow_count": 12,
      "average_rating": 4.5,
      "cover_image": "https://example.com/cover.jpg",
      "status": "AVAILABLE",
      "created_at": "2026-08-14T08:00:00Z",
      "updated_at": "2026-08-14T08:00:00Z"
    }
  ]
}
```

Use these query parameters together as needed:

| Query parameter | Example | Description |
| --- | --- | --- |
| `search` | `?search=clean` | Searches title, author, and ISBN |
| `genre` | `?genre=Programming` | Exact genre filter |
| `language` | `?language=English` | Exact language filter |
| `status` | `?status=AVAILABLE` | Exact status filter |
| `published_year` | `?published_year=2008` | Exact publication-year filter |
| `ordering` | `?ordering=-average_rating` | Sort by `average_rating`, `borrow_count`, `published_year`, or `created_at`; prefix `-` for descending |
| `page` | `?page=2` | Select a page |
| `page_size` | `?page_size=25` | Change page size, up to 100 |

Example: `GET /api/books/?search=python&language=English&ordering=-borrow_count&page_size=20`

### Get one book

`GET /api/books/7/` — Public

Returns the same book JSON object shown in the list result. An unknown id returns:

```json
{ "detail": "Not found." }
```

### Create a book

`POST /api/books/` — Librarian or Admin

```json
{
  "title": "Clean Code",
  "author": "Robert C. Martin",
  "isbn": "9780132350884",
  "description": "A guide to software craftsmanship.",
  "genre": "Programming",
  "publisher": "Prentice Hall",
  "published_year": 2008,
  "language": "English",
  "total_copies": 4,
  "available_copies": 4,
  "borrow_count": 0,
  "average_rating": 0,
  "cover_image": "https://example.com/cover.jpg",
  "status": "AVAILABLE"
}
```

Successful response — `201 Created`: the complete created book object.

Inventory validation example — `400 Bad Request`:

```json
{
  "available_copies": ["Available copies cannot exceed total copies."]
}
```

### Update a book

`PUT /api/books/7/` replaces a book; `PATCH /api/books/7/` updates only supplied fields. Both require a librarian or admin.

```json
PATCH /api/books/7/
{ "available_copies": 2, "status": "AVAILABLE" }
```

Successful response — `200 OK`: the complete updated book object.

### Delete a book

`DELETE /api/books/7/` — Librarian or Admin

Successful response — `204 No Content` with no JSON body.

## 8. Borrowings app

### What this app does

The borrowings app manages circulation through `BorrowRecord`. A record links one user to one book and stores `borrowed_at`, `due_date`, optional `returned_at`, and a status of `BORROWED`, `RETURNED`, or `OVERDUE`.

When a user borrows a book, the API locks the book row, verifies availability, blocks a duplicate active borrow of the same title, creates a record, reduces `available_copies`, and increments `borrow_count`. The due date is automatically set to 14 days from the initial record save.

When a user returns a book, the API locks the active record and inventory row, writes the return time, changes the record to `RETURNED`, and restores one available copy. It refuses a return that would push availability above total copies.

### Borrow a book

`POST /api/borrowings/borrow/7/` — Authenticated

No request body is required.

Successful response — `201 Created`:

```json
{ "message": "Book borrowed successfully" }
```

Common business-rule responses — `400 Bad Request`:

```json
{ "error": "Book already borrowed" }
```

```json
{ "error": "No copies available" }
```

Unknown books return `404 Not Found`:

```json
{ "error": "Book not found" }
```

### Return a book

`POST /api/borrowings/return/7/` — Authenticated

No request body is required.

Successful response — `200 OK`:

```json
{ "message": "Book returned successfully" }
```

If the caller has no active borrowing record for that book:

```json
{ "error": "No active borrow found" }
```

### View personal borrowing history

`GET /api/borrowings/history/` — Authenticated

Only the caller's records are returned, newest first:

```json
[
  {
    "id": 24,
    "book_title": "Clean Code",
    "borrowed_at": "2026-08-14T08:00:00Z",
    "due_date": "2026-08-28T08:00:00Z",
    "returned_at": null,
    "status": "BORROWED",
    "user": 1,
    "book": 7
  }
]
```

`OVERDUE` is available in the model for future scheduled automation. The current application does not include an automatic job that changes `BORROWED` records to `OVERDUE` after the due date.

## 9. Reviews app

### What this app does

The reviews app lets an authenticated reader save one review for a book. A review includes a 1–5 integer rating and review text. The database enforces uniqueness for `(user, book)`, so duplicate reviews cannot be created even in concurrent requests.

After a review is created, the app recalculates the related book's `average_rating` from all saved reviews and rounds it to two decimal places. Book reviews are public so prospective readers can see community feedback.

The app also has an AI review-draft feature. It takes the reader's rating and optional notes, asks UserFacet AI for a polished draft, and returns text only—it does not publish or save a review on the reader's behalf.

### Create a review

`POST /api/reviews/create/` — Authenticated

```json
{
  "book": 7,
  "rating": 5,
  "review_text": "Clear, practical, and full of useful examples."
}
```

Successful response — `201 Created`:

```json
{
  "id": 9,
  "rating": 5,
  "review_text": "Clear, practical, and full of useful examples.",
  "created_at": "2026-08-14T08:30:00Z",
  "updated_at": "2026-08-14T08:30:00Z",
  "user": 1,
  "book": 7
}
```

Invalid rating example — `400 Bad Request`:

```json
{ "rating": ["Ensure this value is less than or equal to 5."] }
```

Duplicate review example — `400 Bad Request`:

```json
{ "non_field_errors": "You have already reviewed this book." }
```

### Read reviews for a book

`GET /api/reviews/book/7/` — Public

```json
[
  {
    "id": 9,
    "rating": 5,
    "review_text": "Clear, practical, and full of useful examples.",
    "created_at": "2026-08-14T08:30:00Z",
    "updated_at": "2026-08-14T08:30:00Z",
    "user": 1,
    "book": 7
  }
]
```

An unknown book returns `404 Not Found`.

### Generate an AI review draft

`POST /api/reviews/ai-review/7/` — Authenticated

```json
{
  "rating": 4,
  "notes": "The examples were useful, although some sections felt dated."
}
```

Successful response — `200 OK`:

```json
{
  "generated_review": "Clean Code offers practical guidance and useful examples for developers..."
}
```

The `rating` field is required and must be an integer from 1 to 5. A provider issue returns `502 Bad Gateway`:

```json
{ "error": "Review service is temporarily unavailable. Please try again." }
```

## 10. AI Summary app

### What this app does

The AI Summary app creates reading assistance from a book's title, author, and description. It supports two independent summary types:

- **SHORT** — prompted for roughly 150–200 words: main idea, core concepts, and intended audience.
- **DETAILED** — prompted for roughly 700–800 words: important concepts, lessons, and practical takeaways.

Each book/type pair has one `BookSummary` record. Its status can be `PENDING`, `PROCESSING`, `COMPLETED`, or `FAILED`.

### Cache and duplicate-generation flow

1. The API checks Redis using `summary:<book_id>:<type>`.
2. On a cache miss, it checks the durable `BookSummary` row.
3. A completed database summary is returned immediately and placed back into Redis.
4. If no completed summary exists, one request claims the row as `PROCESSING` in a short database transaction.
5. Any overlapping request gets `202 Accepted` and is asked to retry after five seconds.
6. The owner calls UserFacet AI outside the transaction.
7. Success is saved as `COMPLETED` and cached for 24 hours; failure becomes `FAILED`, allowing a later retry.

This design avoids duplicate AI cost and does not rely solely on a cache. The Redis configuration uses `IGNORE_EXCEPTIONS=True`, so a cache outage does not stop the feature.

### Generate or retrieve a summary

`POST /api/ai/generate/7/?type=short` — Authenticated

The `type` query parameter is optional and defaults to `SHORT`. It is case-insensitive; only `SHORT` and `DETAILED` are accepted. The request body is not used.

First successful generation — `200 OK`:

```json
{
  "summary_type": "SHORT",
  "cached": false,
  "summary": "Clean Code explains the discipline of writing readable, maintainable software..."
}
```

Later completed response — `200 OK`:

```json
{
  "summary_type": "SHORT",
  "cached": true,
  "summary": "Clean Code explains the discipline of writing readable, maintainable software..."
}
```

If another request is already generating the same book/type pair — `202 Accepted`:

```json
{
  "message": "Summary generation already in progress.",
  "retry_after": 5
}
```

Invalid type — `400 Bad Request`:

```json
{ "error": "type must be SHORT or DETAILED" }
```

Provider failure — `502 Bad Gateway`:

```json
{ "error": "Summary service is temporarily unavailable. Please try again." }
```

## 11. Analytics app

### What this app does

The analytics app provides concise, read-only reporting for librarians and administrators. It moves query logic into `AnalyticsService`, which keeps API views simple and makes report behaviour easy to test.

All results are safe for an empty library. Top-ten queries are capped at ten results; ties are consistently ordered by title/email and then id.

### Dashboard summary

`GET /api/analytics/dashboard/` — Librarian or Admin

```json
{
  "total_books": 42,
  "total_users": 18,
  "total_borrowings": 95,
  "active_borrowings": 7
}
```

`active_borrowings` counts only records with the `BORROWED` status.

### Most borrowed books

`GET /api/analytics/most-borrowed/` — Librarian or Admin

Returns up to ten books ordered by `borrow_count` descending:

```json
[
  {
    "id": 7,
    "title": "Clean Code",
    "author": "Robert C. Martin",
    "average_rating": 4.5,
    "borrow_count": 12
  }
]
```

### Top-rated books

`GET /api/analytics/top-rated/` — Librarian or Admin

Returns up to ten books ordered by `average_rating` descending:

```json
[
  {
    "id": 7,
    "title": "Clean Code",
    "author": "Robert C. Martin",
    "average_rating": 4.5,
    "borrow_count": 12
  }
]
```

### Active users

`GET /api/analytics/active-users/` — Librarian or Admin

Only users with at least one borrow record are included. `borrow_count` is calculated by the query:

```json
[
  {
    "id": 1,
    "email": "ada@example.com",
    "first_name": "Ada",
    "last_name": "Lovelace",
    "borrow_count": 4
  }
]
```

### Genre distribution

`GET /api/analytics/genre-distribution/` — Librarian or Admin

```json
[
  { "genre": "Programming", "total": 12 },
  { "genre": "History", "total": 8 }
]
```

Results are ordered by count descending, then genre name.

## 12. Recommendations app

### What this app does

The recommendations app is a read-only discovery layer. It does not modify books, borrowing records, or reviews. `RecommendationService` contains all ranking logic, while API views only handle access and responses.

Every recommendation endpoint returns a focused book card:

```json
{
  "id": 7,
  "title": "Clean Code",
  "author": "Robert C. Martin",
  "genre": "Programming",
  "average_rating": 4.5,
  "borrow_count": 12
}
```

### Personalised recommendations

`GET /api/recommendations/personalized/` - Authenticated

This endpoint examines the current user's borrowing history, finds their most-read genres, and recommends unborrowed books from those genres. Previously borrowed books are always excluded. The response contains at most ten books, ordered by `average_rating` descending and then `borrow_count` descending. Title and id are stable tie-breakers.

```http
GET /api/recommendations/personalized/
Authorization: Bearer <access-token>
```

Successful response - `200 OK`:

```json
[
  {
    "id": 12,
    "title": "The Pragmatic Programmer",
    "author": "Andrew Hunt and David Thomas",
    "genre": "Programming",
    "average_rating": 4.8,
    "borrow_count": 92
  }
]
```

A new user with no borrowing history receives a valid empty response:

```json
[]
```

### Readers also borrowed

`GET /api/recommendations/also-borrowed/<book_id>/` - Public

This endpoint uses collaborative filtering. It finds every reader who borrowed the selected book and then finds their other borrowed books. The selected book is excluded. The database uses `Count()` to calculate co-borrow frequency, returning up to ten titles ordered by that frequency. Rating, borrow count, title, and id make ties deterministic.

```http
GET /api/recommendations/also-borrowed/7/
```

Successful response - `200 OK`:

```json
[
  {
    "id": 15,
    "title": "Design Patterns",
    "author": "Erich Gamma, Richard Helm, Ralph Johnson, and John Vlissides",
    "genre": "Programming",
    "average_rating": 4.7,
    "borrow_count": 75
  },
  {
    "id": 18,
    "title": "Refactoring",
    "author": "Martin Fowler",
    "genre": "Programming",
    "average_rating": 4.6,
    "borrow_count": 63
  }
]
```

If the selected book exists but has no borrowers, the response is `200 OK` with `[]`. An unknown book returns `404 Not Found`:

```json
{ "detail": "Book not found." }
```

### Trending books

`GET /api/recommendations/trending/` - Public

Trending books are ordered by `borrow_count` descending, then `average_rating` descending. The endpoint returns at most ten books and is safe to call without authentication.

```http
GET /api/recommendations/trending/
```

Successful response - `200 OK`:

```json
[
  {
    "id": 7,
    "title": "Clean Code",
    "author": "Robert C. Martin",
    "genre": "Programming",
    "average_rating": 4.5,
    "borrow_count": 120
  }
]
```

An empty catalogue returns `200 OK` with `[]`.

## 13. Data model and relationships

```text
User 1 --- * BorrowRecord * --- 1 Book
User 1 --- * Review       * --- 1 Book
User 1 --- * Wishlist     * --- 1 Book
Book 1 --- * BookSummary
```

| Model | Key rules |
| --- | --- |
| `User` | Email and contact number are unique; email is the login field |
| `Book` | ISBN is unique; available copies cannot exceed total copies through API validation |
| `BorrowRecord` | Due date is automatically set when first saved; stores borrowing state and timestamps |
| `Review` | One review per user/book; rating is validated by the API from 1 to 5 |
| `BookSummary` | One summary per book/type; keeps durable generation state |
| `Wishlist` | One user/book pair; model exists but its feature endpoints are not implemented yet |

Deleting a book or user cascades to its related records according to the configured foreign keys.

## 14. Testing, quality, and production notes

The test suite includes request-level coverage for registration and login validation, access rules, catalogue searching/filtering/pagination, invalid inventory, borrow/return states, review uniqueness and ratings, summary caching and retry states, AI failures, analytics aggregation/ordering, and recommendations.

Recommendation tests cover authentication, empty borrowing history, borrowed-book exclusion, result limits, personalised ordering, collaborative co-borrow ranking, empty reader cohorts, public access, trending tie-breaks, and unknown-book `404` handling.

```bash
python manage.py test
python manage.py check
```

For production, replace development SQLite with PostgreSQL, use managed Redis, set `DEBUG=False`, configure a secure secret key and `ALLOWED_HOSTS`, enforce HTTPS, protect environment secrets, rate-limit login and AI endpoints, add logs/monitoring/backups, and restrict privileged-role registration.

## 15. Known boundaries and planned enhancements

- Automatic overdue status changes and due-date notifications need a scheduled task or worker.
- Book availability status is stored separately; borrow/return updates copy counts but does not automatically change this field.
- Wishlists are represented in the model but do not yet have API endpoints.
- Review edit/delete, reservations, account administration, AI chat, and advanced trend reporting are natural next features.
- AI output is generated by an external service and should be presented as assistance, not guaranteed factual library metadata.
