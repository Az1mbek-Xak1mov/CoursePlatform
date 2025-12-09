# IlmSpace - Educational Course Platform

🎓 A modern educational marketplace connecting students with expert instructors in Uzbekistan.

## Features

- **For Students**
  - Browse and search courses by category
  - Enroll in free and paid courses
  - Track learning progress
  - Earn completion certificates
  - Leave reviews and ratings

- **For Instructors**
  - Create and manage courses
  - Build course curriculum with modules and lessons
  - Track earnings and student enrollment
  - Request payouts

- **For Administrators**
  - Moderate course submissions
  - Manage users and content
  - View platform analytics
  - Handle transactions and refunds

## Tech Stack

- **Backend**: Django 5.1+
- **Database**: SQLite (dev) / PostgreSQL (prod)
- **Admin**: Django Jazzmin
- **Static Files**: WhiteNoise
- **Production Server**: Gunicorn

## Quick Start

### Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) package manager

### Installation

1. Clone the repository:
```bash
git clone https://github.com/Az1mbek-Xak1mov/CoursePlatform.git
cd CoursePlatform
```

2. Create virtual environment and install dependencies:
```bash
uv sync
```

3. Copy environment file and configure:
```bash
cp .env.example .env
# Edit .env with your settings
```

4. Run migrations:
```bash
uv run python manage.py migrate
```

5. Create superuser:
```bash
uv run python manage.py createsuperuser
```

6. Run development server:
```bash
uv run python manage.py runserver
```

Visit http://localhost:8000 to see the application.

## Development

### Install dev dependencies:
```bash
uv sync --all-extras
```

### Run tests:
```bash
uv run pytest
```

### Code formatting:
```bash
uv run ruff check .
uv run ruff format .
```

## Production Deployment

### Environment Variables

Set these in your production environment:

```bash
DEBUG=False
SECRET_KEY=your-super-secret-key
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
DATABASE_URL=postgres://user:pass@host:5432/dbname
```

### Running with Gunicorn:
```bash
uv run gunicorn CoursePlatform.wsgi:application --bind 0.0.0.0:8000
```

### Collect static files:
```bash
uv run python manage.py collectstatic --noinput
```

## Project Structure

```
CoursePlatform/
├── CoursePlatform/     # Django project settings
├── users/              # Custom user model & auth
├── authors/            # Instructor profiles & earnings
├── students/           # Student profiles & progress
├── courses/            # Course management
├── payments/           # Transaction handling
├── moderation/         # Content moderation
├── templates/          # HTML templates
├── static/             # Static assets
└── media/              # User uploads
```

## Payment Gateways

Supports Uzbekistan payment systems:
- Click
- Payme
- Uzum Pay

## License

MIT License - see [LICENSE](LICENSE) for details.

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Support

For support, email support@ilmspace.uz or join our Telegram group.
