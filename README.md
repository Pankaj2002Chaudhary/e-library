# E-Library Management System

E-Library Management System is a modern, AI-enhanced backend platform that bridges traditional library management with intelligent digital experiences. The platform empowers readers to explore books, manage borrowing activities, write reviews, generate AI-powered summaries, and discover new books through personalized recommendations. Simultaneously, it equips librarians and administrators with robust catalogue management, inventory control, analytics, and reporting capabilities, enabling efficient and data-driven library operations.


## Tech Stack

| Category | Technologies |
|-----------|-------------|
| **Backend** | Python, Django, Django REST Framework (DRF) |
| **Database** | PostgreSQL |
| **Authentication** | JWT, Simple JWT |
| **AI Integration** | UserFacet AI API, Requests |
| **Caching** | Redis, django-redis |
| **API Testing** | Postman |
| **Version Control** | Git, GitHub |
| **Architecture** | Service Layer Architecture, RESTful APIs, Role-Based Access Control (RBAC) |
| **Development Environment** | Virtual Environment (venv) |


### AI-Assisted Development

During development, AI tools were used for implementation assistance, testing support, bug fixing, code reviews, and architecture/design discussions.

- **OpenAI Codex**
- **ChatGPT**
- **Claude**


## What this project delivers

- **Secure user authentication** — register with an email address and use JWT tokens to securely access private features.
- **Advanced book discovery** — search by title, author, or ISBN; filter, sort, and paginate results.
- **Robust catalogue management** — librarians and administrators can create, update, and manage books while ensuring inventory accuracy through automatic copy tracking.
- **Reliable borrowing system** — users can borrow and return books, with a 14-day due date and a private borrowing history.
- **Copyright-Aware Access Control** — the platform follows a borrowing-based model that limits access according to available copies, mirroring real-world library operations. This prevents a single licensed copy from being simultaneously accessed by unlimited users, helping protect author and publisher rights while promoting fair content distribution.
- **Book Ratings** — readers can rate books on a 1–5 scale and automatically update aggregate ratings.
- **AI-Assisted Review Generation** — readers can provide simple notes, thoughts, or impressions about a book, and AI transforms them into polished, well-structured, professional-quality reviews.
- **AI-Powered Book Summaries** — integrates AI to generate multiple summary formats (short and detailed) of the book.
- **Redis-Based Summary Caching** — previously generated summaries are cached and reused, preventing duplicate AI requests, reducing token consumption, and delivering significantly faster response times.
- **Analytics & Insights Dashboard** — staff can see dashboard totals, popular books, top-rated books, active readers, and genre distribution.

- **Personalized Recommendation Engine** - readers receive suggestions based on borrowing history, related-reader behaviour, and current library popularity.


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
