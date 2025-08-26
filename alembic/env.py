import os
import sys
from logging.config import fileConfig
import configparser
from pathlib import Path

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# --- Alembic/Projekt-Integration START ---

# Füge das Hauptverzeichnis des Projekts zum Python-Pfad hinzu,
# damit wir die 'core'-Module importieren können.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Importiere die 'Base' Metadaten aus deinen DB-Modellen.
# Alembic benötigt dies, um die Struktur deiner Modelle zu kennen.
from core.db_models import Base

# --- Alembic/Projekt-Integration END ---

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# --- Alembic/Projekt-Integration START ---
# Funktion zum dynamischen Laden der Datenbank-URL aus der config.ini des Projekts.
def get_project_db_url():
    """
    Liest die config.ini robust und gibt die SQLAlchemy-URL zurück.
    Spiegelt das Suchverhalten des DatabaseManagers wider und gibt klare Fehlermeldungen.
    """
    from core.settings_manager import get_app_data_dir, get_application_root_dir

    parser = configparser.ConfigParser()

    # Suche an den gleichen Orten wie der DatabaseManager, bevorzuge aber die
    # Konfiguration im Projekt-Root, was für die Entwicklung typisch ist.
    app_root_path = get_application_root_dir()
    root_config_path = app_root_path / 'config.ini'
    user_config_path = get_app_data_dir() / 'config.ini'

    config_path_to_use = None
    if root_config_path.exists():
        config_path_to_use = root_config_path
    elif user_config_path.exists():
        config_path_to_use = user_config_path

    if not config_path_to_use:
        example_path = app_root_path / 'config.ini.example'
        # Gib eine klare, hilfreiche Fehlermeldung aus.
        raise FileNotFoundError(
            f"Konfigurationsdatei 'config.ini' nicht gefunden.\n"
            f"Alembic hat an folgenden Orten gesucht:\n"
            f"1. {root_config_path}\n"
            f"2. {user_config_path}\n\n"
            f"Bitte erstellen Sie die Datei, z.B. durch Kopieren von '{example_path}' nach '{root_config_path}'."
        )

    parser.read(config_path_to_use)

    if 'postgresql' not in parser:
        raise configparser.NoSectionError(
            'postgresql',
            f"Der Abschnitt [postgresql] fehlt in der Konfigurationsdatei '{config_path_to_use}'."
        )

    db_config = parser['postgresql']
    required_keys = ['user', 'password', 'host', 'database']
    if not all(key in db_config for key in required_keys):
        raise KeyError(f"Ein oder mehrere benötigte Schlüssel ({', '.join(required_keys)}) fehlen im [postgresql] Abschnitt von '{config_path_to_use}'.")

    return f"postgresql+psycopg2://{db_config['user']}:{db_config['password']}@{db_config['host']}/{db_config['database']}"

# Setze die dynamisch geladene URL in der Alembic-Konfiguration.
config.set_main_option('sqlalchemy.url', get_project_db_url())
# --- Alembic/Projekt-Integration END ---

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# --- Alembic/Projekt-Integration START ---
# Hier weisen wir Alembic an, unsere Modelle für den autogenerate-Prozess zu verwenden.
target_metadata = Base.metadata
# --- Alembic/Projekt-Integration END ---

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
