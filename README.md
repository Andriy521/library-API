# 📚 Library API

**Library API** is a backend service for managing a library system.  
Users can borrow and return books, and the system automatically generates payments (including overdue fines).  
All interactions happen via a REST API secured with JWT authentication.

## ⚙️ Technologies

- Django 4+
- Django REST Framework
- PostgreSQL
- Celery + Redis
- Docker + docker-compose
- JWT authentication
- Telegram notifications

---

## 🚀 Getting Started

> All services run via Docker.

### 1. Clone the repository

```bash
git clone <your-repo-url>
cd library-API
```

### 2. Create your .env file
```bash
cp .env.sample .env
```
🔐 Fill in the required environment variables.

### 3. Build and start containers
bash
Копіювати
Редагувати
docker-compose up --build
### 4. Apply database migrations
bash
Копіювати
Редагувати
docker-compose exec web python manage.py migrate
### 5. (Optional) Create a superuser
```bash
docker-compose exec web python manage.py createsuperuser
```

### ✅ Useful Commands
Format code with Black
```bash
black .
```
Or via Docker (if you don’t have Black installed locally):

```bash
docker run --rm -v $(pwd):/app -w /app python:3.11 bash -c "pip install black && black ."
```

### 📬 Telegram Notifications
After a new borrowing is created, a message is sent to Telegram.
Make sure TELEGRAM_TOKEN and TELEGRAM_CHAT_ID are properly set in your .env file.# library-API
