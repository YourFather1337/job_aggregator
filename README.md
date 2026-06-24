# Job Aggregator

Веб-приложение для поиска вакансий из нескольких источников с возможностью сохранения вакансий в избранное и создания собственного резюме.

## Возможности

* Поиск вакансий по ключевым словам
* Агрегация вакансий из нескольких источников
* Параллельный сбор данных
* Удаление дубликатов вакансий
* Сохранение вакансий в избранное
* Регистрация и авторизация пользователей
* Создание и редактирование резюме
* Фильтрация вакансий по:

  * зарплате
  * городу
  * типу занятости
* Адаптивный интерфейс

---

## Источники вакансий

| Источник    | Метод получения |
| ----------- | --------------- |
| HH.ru       | Open API        |
| RemoteOK    | JSON API        |
| Habr Career | HTML Parsing    |
| Work-Zilla  | HTML Parsing    |

---

## Технологии

### Backend

* FastAPI
* SQLAlchemy
* PostgreSQL / SQLite
* Alembic
* Passlib + bcrypt

### Парсинг и интеграции

* httpx / requests
* BeautifulSoup
* Selenium

### Frontend

* Jinja2
* HTML5
* CSS3

---

## Структура проекта

```text
app/
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── favorites.html
│   ├── resume.html
│   ├── login.html
│   └── register.html
│
├── static/
│   └── style.css
│
├── routers/
│   ├── auth.py
│   ├── search.py
│   ├── favorites.py
│   └── resume.py
│
├── parsers/
│   ├── base.py
│   ├── hh.py
│   ├── remoteok.py
│   ├── habr.py
│   └── workzilla.py
│
├── models.py
├── schemas.py
├── database.py
├── config.py
└── main.py
```

---

## Модели данных

### User

```python
id
username
email
hashed_password
created_at
```

### Resume

```python
id
user_id
full_name
about
skills
experience
education
city
desired_position
desired_salary
employment_type
contacts
updated_at
```

### SavedVacancy

```python
id
user_id
title
company
salary_from
salary_to
currency
city
skills
employment_type
source
source_url
saved_at
```

---

## Основные маршруты

### Поиск вакансий

| Метод | Путь            |
| ----- | --------------- |
| GET   | `/`             |
| GET   | `/search?q=...` |

### Избранное

| Метод  | Путь              |
| ------ | ----------------- |
| GET    | `/favorites`      |
| POST   | `/favorites/add`  |
| DELETE | `/favorites/{id}` |

### Резюме

| Метод | Путь           |
| ----- | -------------- |
| GET   | `/resume`      |
| GET   | `/resume/edit` |
| POST  | `/resume/edit` |

### Аутентификация

| Метод | Путь        |
| ----- | ----------- |
| GET   | `/register` |
| POST  | `/register` |
| GET   | `/login`    |
| POST  | `/login`    |
| POST  | `/logout`   |

---

## Логика работы

### Поиск вакансий

1. Пользователь вводит поисковый запрос.
2. Сервис параллельно обращается ко всем источникам.
3. Результаты объединяются.
4. Дубликаты удаляются по `source_url`.
5. Итоговый список отображается пользователю.

> Результаты поиска не сохраняются в базе данных и существуют только во время выполнения запроса.

### Избранное

* Доступно только авторизованным пользователям.
* Позволяет сохранять интересующие вакансии.
* Список избранных вакансий хранится в базе данных.

### Резюме

* Создание собственного резюме.
* Редактирование и обновление информации.
* Хранение данных в профиле пользователя.

---

## Запуск проекта

```bash
git clone <repository-url>

cd job-aggregator

python -m venv venv

source venv/bin/activate
# Windows
venv\Scripts\activate

pip install -r requirements.txt

alembic upgrade head

uvicorn app.main:app --reload
```

После запуска приложение будет доступно по адресу:

```text
http://localhost:8000
```

---

## Безопасность

* Хранение паролей в хешированном виде (`bcrypt`)
* Авторизация через сессионные cookies
* Защита закрытых страниц для неавторизованных пользователей

---

## Планы по развитию

* Расширение списка источников вакансий
* Умная сортировка результатов
* Telegram-уведомления
* Экспорт резюме в PDF
* Кэширование результатов поиска
* Docker-развертывание

Этот вариант выглядит как README реального pet/project-проекта и хорошо смотрится на GitHub.
