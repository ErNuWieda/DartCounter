import sys
from logging.config import fileConfig
from pathlib import Path

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# 1. WICHTIG: Projekt-Root zum Pfad hinzufügen, damit die Imports funktionieren
sys.path.append(str(Path(__file__).resolve().parent.parent))

# 2. WICHTIG: Importiere die Base deiner Modelle für Autogenerate
from core.db_models import Base

# Das Alembic Config Objekt
config = context.config

# Logging konfigurieren (liest aus alembic.ini)
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 3. WICHTIG: Setze target_metadata für Autogenerate
# Hier greift Alembic auf alle Modelle zu, die von Base erben (Highscore, GameRecord, etc.)
target_metadata = Base.metadata

def run_migrations_offline() -> None:
    """Migrationen im 'Offline'-Modus ausführen.

    Hier wird lediglich ein SQL-Skript generiert, anstatt die DB direkt zu ändern.
    Die URL wird aus der Config (gesetzt durch den DatabaseManager) gelesen.
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
    """Migrationen im 'Online'-Modus ausführen.

    Hier wird eine Engine erstellt und die Migrationen direkt auf der DB ausgeführt.
    """
    # Erstelle die Konfiguration für die Engine.
    # Wir nutzen die Sektion aus alembic.ini, aber die URL wurde 
    # dynamisch vom DatabaseManager via alembic_cfg.set_main_option gesetzt.
    configuration = config.get_section(config.config_ini_section, {})
    
    # Falls die URL nicht in der Sektion steht (weil sie dynamisch gesetzt wurde),
    # ziehen wir sie explizit aus dem Haupt-Optionen-Pool.
    if "sqlalchemy.url" not in configuration:
        configuration["sqlalchemy.url"] = config.get_main_option("sqlalchemy.url")

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, 
            target_metadata=target_metadata,
            # Verhindert, dass Alembic versucht, System-Tabellen zu löschen
            compare_type=True 
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()