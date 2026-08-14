# E-Library Management System

**E-Library Management System** is a modern, AI-powered digital library platform designed to enhance the way readers discover, understand, and engage with books. The system enables users to explore a rich catalogue of titles, access books through a controlled borrowing model, rate books, generate AI-powered summaries, create AI-assisted reviews, and discover relevant content through personalized recommendations.

Beyond the reader experience, the platform provides librarians and administrators with comprehensive tools for catalogue management, digital inventory control, user activity monitoring, analytics, and operational insights. By combining traditional library workflows with AI-driven features and data-driven decision making, E-Library delivers an intelligent, scalable, and engaging digital reading ecosystem.


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

## Architecture Overview

```text
                          ┌─────────────────────┐
                          │       Client        │
                          │ Postman / Frontend  │
                          └──────────┬──────────┘
                                     │
                                     ▼
                        ┌────────────────────────┐
                        │ Django REST Framework  │
                        │      REST APIs         │
                        └──────────┬─────────────┘
                                   │
      ┌────────────┬───────────────┼───────────────┬─────────────┬──────────────┐
      ▼            ▼               ▼               ▼             ▼              ▼
 ┌────────┐   ┌────────┐     ┌────────────┐   ┌────────┐   ┌────────────┐ ┌──────────┐
 │Accounts│   │ Books  │     │Borrowings │   │Reviews │   │Analytics   │ │Recommend.│
 └────────┘   └────────┘     └────────────┘   └────────┘   └────────────┘ └──────────┘
      │            │               │               │             │              │
      └────────────┴───────────────┴───────────────┴─────────────┴──────────────┘
                                   │
                                   ▼
                           ┌──────────────┐
                           │ PostgreSQL   │
                           │   Database   │
                           └──────┬───────┘
                                  │
                 ┌────────────────┴────────────────┐
                 ▼                                 ▼
        ┌─────────────────┐              ┌─────────────────┐
        │  AI Summary &   │              │  Redis Cache    │
        │ Review Services │              │ (AI Responses)  │
        └────────┬────────┘              └─────────────────┘
                 │
                 ▼
       ┌───────────────────────┐
       │  UserFacet AI API     │
       └───────────────────────┘
```


## Implemented Features

- **Secure user authentication** — register with an email address and use JWT tokens to securely access private features.
- **Advanced book discovery** — search by title, author, or ISBN; filter, sort, and paginate results.
- **Robust catalogue management** — librarians and administrators can create, update, and manage books while ensuring inventory accuracy through automatic copy tracking.
- **Reliable borrowing system** — users can borrow and return books, with a 14-day due date and a private borrowing history.
- **Controlled inventory access** — borrowing is limited by available copies, mirroring real-world library circulation and preventing the same limited copy from being borrowed concurrently.
- **Book Ratings** — readers can rate books on a 1–5 scale and automatically update aggregate ratings.
- **AI-Assisted Review Generation** — readers can provide simple notes, thoughts, or impressions about a book, and AI transforms them into polished, well-structured, professional-quality reviews.
- **AI-Powered Book Summaries** — integrates AI to generate multiple summary formats (short and detailed) of the book.
- **Redis-Based Summary Caching** — previously generated summaries are cached and reused, preventing duplicate AI requests, reducing token consumption, and delivering significantly faster response times.
- **Analytics & Insights Dashboard** — staff can see dashboard totals, popular books, top-rated books, active readers, and genre distribution.

- **Personalized Recommendation Engine** - readers receive suggestions based on borrowing history, related-reader behaviour, and current library popularity.


## Code Structure & Maintainability

The project is designed with a strong focus on modularity, maintainability, and separation of concerns. Each core business domain is implemented as an independent Django application, allowing features to evolve without impacting unrelated parts of the system.

Key architectural principles followed throughout the project include:

- **Modular Design** — functionality is organized into dedicated apps such as Accounts, Books, Borrowings, Reviews, AI Services, Recommendations, and Analytics.
- **Separation of Concerns** — business logic is isolated from API views through reusable service layers and utility modules.
- **Reusable Components** — serializers, permissions, validators, and services are designed to be reused across multiple endpoints.
- **Role-Based Access Control** — authorization rules are centralized to ensure consistent and secure access management.
- **Scalable Architecture** — new features can be added with minimal changes to existing modules.
- **Performance-Oriented Design** — Redis caching is used to reduce redundant AI requests and improve response times.
- **Maintainable Codebase** — clear project structure, consistent coding standards, meaningful naming conventions, and comprehensive documentation improve long-term maintainability.

This approach ensures that the system remains easy to understand, extend, test, and maintain as the application grows.


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

### Reviews

- `POST /api/reviews/create/` - Publish your rating and written review.
- `GET /api/reviews/book/<book_id>/` - Read public reviews for one book.
- `POST /api/reviews/ai-review/<book_id>/` - Generate an AI-assisted review draft.

### AI summaries

- `POST /api/ai/generate/<book_id>/?type=short` - Generate or retrieve short summary.
- `POST /api/ai/generate/<book_id>/?type=detailed` - Generate or retrieve detailed summary.

The `type` parameter accepts `short` or `detailed`; it defaults to `short`. The first successful request returns `cached: false`. Repeat requests return the persisted summary with `cached: true` when available.

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

## Setup Instructions

### 1. Clone the repository and create a virtual environment

```bash
git clone <repository-url>
cd e-library

python -m venv venv
```

**Windows (PowerShell)**

```powershell
.\venv\Scripts\Activate.ps1
```

**macOS/Linux**

```bash
source venv/bin/activate
```

---

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

---

### 3. Configure environment variables

Create a `.env` file in the project root:

```env
# PostgreSQL Configuration
DATABASE_URL=postgresql://postgres:your_password@127.0.0.1:5432/e_library

# UserFacet AI API
AI_API_TOKEN=your-userfacet-api-token

# Redis is configured for redis://127.0.0.1:6379/1
```

The application reads `DATABASE_URL`. If it is omitted, Django falls back to the local `db.sqlite3` file. Redis is configured at `redis://127.0.0.1:6379/1`; cache failures are ignored so the API remains usable.

URL-encode special characters in PostgreSQL passwords. For example, `@` becomes `%40` inside `DATABASE_URL`.

---

### 4. Create the PostgreSQL database

```sql
CREATE DATABASE e_library;
```

---

### 5. Apply database migrations

```bash
python manage.py migrate
```

To add repeatable local demo data for Postman testing:

```bash
python manage.py seed_demo_data
```

---

### 6. Create an administrator account

```bash
python manage.py createsuperuser
```

---

### 7. Start the development server

```bash
python manage.py runserver
```

The API will be available at:

```text
http://127.0.0.1:8000/
```

---

### 8. Configure Redis (Recommended)

Redis is used for caching AI-generated summaries to reduce API calls, improve response times, and optimize token usage.

Default Redis endpoint:

```text
127.0.0.1:6379
```

If Redis is unavailable, the application will continue to function normally, but AI-generated summaries will not be cached.

---

### 9. Verify the project

```bash
python manage.py check
python manage.py test
```



## Important Assumptions

- `available_copies` represents physical copies or concurrent e-book licences and can never be greater than `total_copies`.

- Every borrow is assigned a 14-day due date. Automatic overdue detection and status updates are planned as a future enhancement and are not currently enforced by a background scheduler.

- The registration API currently accepts a user role for demonstration and testing purposes.

- In a production environment, privileged roles such as Librarian and Administrator would only be assigned by an authorized Administrator through protected management endpoints.

- AI-generated summaries and review drafts are intended to assist readers and may not perfectly reflect the original book content. Users should treat AI output as supplementary information.

- AI-generated summaries are cached using Redis to improve performance, reduce response times, and avoid unnecessary repeated API calls for the same book and summary type.

- Recommendation results are generated from available borrowing activity and user interactions. Recommendation quality is expected to improve as the library accumulates more usage data.

- Borrowing and return operations are protected using database transactions, ensuring accurate inventory tracking and preventing inconsistent copy counts during concurrent requests.

- Analytics and reporting endpoints are based on transactional library data available at the time of the request and are intended for operational insights rather than formal business reporting.

- The system assumes that book metadata (title, author, ISBN, description, etc.) is entered and maintained accurately by librarians or administrators.


### AI-Assisted Development

During development, AI tools were used for implementation assistance, testing support, bug fixing, code reviews, and architecture/design discussions.

- **OpenAI Codex**
- **ChatGPT**
- **Claude**


## Documentation

The detailed guide includes every feature and every API endpoint with ready-to-use request and response JSON:

- [Complete project documentation](PROJECT_DOCUMENTATION.md)
