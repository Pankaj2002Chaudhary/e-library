# E-Library Management System

E-Library is a thoughtfully designed REST API for a modern library. It gives readers a simple way to discover books, borrow available copies, share reviews, and get AI-powered reading support. It also gives library teams the controls and insight they need to manage a catalogue with confidence.

Built with Django and Django REST Framework, the project focuses on the details that make an API dependable in the real world: clear access rules, protected inventory updates, useful validation, reusable business logic, caching, and test coverage.

## What this project delivers

- **Easy account access** — register with an email address and use JWT tokens to securely access private features.
- **Smart catalogue browsing** — search by title, author, or ISBN; filter, sort, and paginate results.
- **Library inventory management** — staff can add, edit, and remove books while the API protects copy-count consistency.
- **Safe borrowing workflow** — users can borrow and return books, with a 14-day due date and a private borrowing history.
- **Reader feedback** — supports one review and rating per user per book, ensuring authentic feedback while maintaining accurate, automatically updated aggregate ratings.
- **AI reading assistance** — integrates AI to generate multiple summary formats (short and detailed) and assist readers in crafting professional-quality reviews from simple notes and impressions.
- **Useful library analytics** — staff can see dashboard totals, popular books, top-rated books, active readers, and genre distribution.

- **Personalised discovery** - readers receive suggestions based on borrowing history, related-reader behaviour, and current library popularity.

## Why it is structured this way

The codebase is organised by business area instead of placing all logic in one application. Each domain—accounts, books, borrowing, reviews, AI summaries, and analytics—owns its models, API views, validation, and tests. This keeps the code easy to understand today and practical to extend tomorrow.

```text
Client -> API route -> Authentication and role check -> View
       -> Validation / business service -> Database or external service -> JSON response
```

For example, borrowing uses a database transaction and row lock so two people cannot accidentally claim the same final copy at once. AI summaries are stored permanently in the database and cached in Redis, which keeps repeat requests fast while avoiding unnecessary AI calls.



## API endpoints

### Accounts

- `POST /api/auth/register/` - Create a new reader account.
- `POST /api/auth/login/` - Sign in and receive JWT tokens.
- `POST /api/auth/refresh/` - Refresh an expired access token.

### Books

- `GET /api/books/` - Browse searchable, filterable book catalogue.
- `POST /api/books/` - Add a book to catalogue.
- `GET /api/books/<id>/` - View complete details for one book.
- `PUT /api/books/<id>/` - Replace all details for one book.
- `PATCH /api/books/<id>/` - Update selected details for one book.
- `DELETE /api/books/<id>/` - Remove a book from catalogue.

### Borrowings

- `POST /api/borrowings/borrow/<book_id>/` - Borrow one available book copy.
- `POST /api/borrowings/return/<book_id>/` - Return your currently borrowed book.
- `GET /api/borrowings/history/` - View your complete borrowing history.

### Reviews and AI

- `POST /api/reviews/create/` - Publish your rating and written review.
- `GET /api/reviews/book/<book_id>/` - Read public reviews for one book.
- `POST /api/reviews/ai-review/<book_id>/` - Generate an AI-assisted review draft.
- `POST /api/ai/generate/<book_id>/` - Generate or retrieve AI book summary.

### Analytics

- `GET /api/analytics/dashboard/` - View overall library activity totals.
- `GET /api/analytics/most-borrowed/` - See ten most borrowed books.
- `GET /api/analytics/top-rated/` - See ten highest rated books.
- `GET /api/analytics/active-users/` - See ten most active readers.
- `GET /api/analytics/genre-distribution/` - View books grouped by genre.

### Recommendations

- `GET /api/recommendations/personalized/` - Receive suggestions matching your borrowing genres.
- `GET /api/recommendations/also-borrowed/<book_id>/` - Discover books similar readers borrowed.
- `GET /api/recommendations/trending/` - Browse currently popular library books.

## Quick start

### 1. Create and activate a virtual environment

```bash
git clone <repository-url>
cd e-library
python -m venv venv
```

Windows PowerShell:

```powershell
.\venv\Scripts\Activate.ps1
```

macOS/Linux:

```bash
source venv/bin/activate
```

### 2. Install packages and configure the AI token

```bash
pip install -r requirements.txt
```

Create a `.env` file in the project root:

```env
AI_API_TOKEN=your-userfacet-api-token
```

### 3. Prepare the database and start the API

```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

The API starts at `http://127.0.0.1:8000/`.

Redis at `127.0.0.1:6379` is recommended for AI-summary caching. The application still works if Redis is temporarily unavailable; it simply skips the cache.

### 4. Verify the project

```bash
python manage.py check
python manage.py test
```

## Technology

Python, Django, Django REST Framework, Simple JWT, SQLite, Redis, `django-filter`, `drf-spectacular`, and the UserFacet AI API.

## Important assumptions

- `available_copies` represents physical copies or concurrent e-book licences and can never be greater than `total_copies`.
- Every borrow is given a 14-day due date. The `OVERDUE` status is ready in the data model, but automatically marking overdue records is a planned scheduled-job feature.
- SQLite is the local development database. PostgreSQL, managed Redis, HTTPS, secret management, and production Django settings should be used for a public deployment.
- The current registration API accepts a requested role. In a public product, privileged roles should only be assigned by an authorised administrator.

## Documentation

The detailed guide includes every feature and every API endpoint with ready-to-use request and response JSON:

- [Complete project documentation](PROJECT_DOCUMENTATION.md)
