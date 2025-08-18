# DOI Management System

Kompletno rešenje za upravljanje DOI registracijama kroz Crossref API, razvijeno kao Flask web aplikacija.

## Kratak opis

DOI Management System omogućava organizacijama da lako upravljaju članovima, publikacijama i kreiraju DOI draft-ove za registraciju kod Crossref-a. Sistem generiše validirane XML fajlove prema Crossref specifikaciji.

## Tehnologije

- **Backend**: Python 3.11+ sa Flask 3.0.x
- **Frontend**: Bootstrap 5.3.x sa Jinja2 template-ima
- **Baza podataka**: MySQL 8.0+
- **Authentication**: Flask-Login
- **Testing**: pytest 7.4.x

## Brzо pokretanje

### 1. Kloniranje i setup

```bash
git clone <repository-url>
cd DOI
```

### 2. Kreiranje virtualnog okruženja

**Windows:**
```bash
setup_env.bat
```

**Linux/Mac:**
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Konfiguracija okruženja

```bash
cp env.example .env
# Urediti .env fajl sa vašim podešavanjima
```

### 4. Pokretanje aplikacije

```bash
python app.py
```

Aplikacija će biti dostupna na: http://localhost:5000

## Struktura projekta

```
DOI/
├── app/                          # Flask aplikacija
│   ├── __init__.py              # Application factory
│   ├── blueprints/              # Flask blueprints
│   ├── templates/               # Jinja2 templates
│   ├── static/                  # Static assets
│   └── models/                  # SQLAlchemy models (future)
├── tests/                       # Test suite
├── config.py                    # Configuration management
├── requirements.txt             # Python dependencies
├── app.py                      # Main application entry point
└── README.md                   # Ova dokumentacija
```

## Testiranje

Pokretanje testova:

```bash
# Aktivirati virtuelno okruženje
source venv/bin/activate  # Linux/Mac
# ili
venv\Scripts\activate.bat  # Windows

# Pokretanje svih testova
pytest

# Pokretanje specifičnih testova
pytest tests/test_app_factory.py

# Pokretanje sa coverage
pytest --cov=app
```

## Funkcionalnosti

### Trenutno implementirano (Story 1.1)

- ✅ Flask application factory pattern
- ✅ Blueprint struktura za modularnu organizaciju
- ✅ Osnovni template sistem sa Bootstrap 5.3.x
- ✅ Osnovne rute za sve module
- ✅ Error handling (404, 500)
- ✅ Osnovni test suite
- ✅ Virtuelno okruženje i dependency management

### Planirano za implementaciju

- 🔄 Database modeli (User, Sponsor, Member, Publication, DOIDraft)
- 🔄 Autentifikacija i autorizacija
- 🔄 CRUD operacije za sve entitete
- 🔄 Crossref XML generisanje
- 🔄 Validacija DOI format-a
- 🔄 File upload i storage management

## Development

### Dodavanje novih funcionalnosti

1. Kreiraj novi branch za feature
2. Implementiraj funkcionalnost sa testovima
3. Pokreni svih testove: `pytest`
4. Kreiraj pull request

### Code style

Projekat sledi Flask best practices definisane u `docs/references/flask-best-practices.md`.

## Configuration

Projekat koristi environment varijable za konfiguraciju. Pogledaj `env.example` za kompletan spisak dostupnih opcija.

### Ključne konfiguracije

- `SECRET_KEY`: Flask secret key za sesije
- `DATABASE_URL`: MySQL connection string
- `UPLOAD_FOLDER`: Direktorijum za upload XML fajlova
- `FLASK_ENV`: development/production environment

## Troubleshooting

### Česti problemi

1. **ModuleNotFoundError**: Proveriti da li je virtuelno okruženje aktivirano
2. **Template not found**: Proveriti da li su template fajlovi na ispravnim lokacijama
3. **Static files 404**: Proveriti Flask static folder konfiguraciju

## License

[License informacije će biti dodati]

## Contributors

- [Informacije o kontributorima će biti dodati]