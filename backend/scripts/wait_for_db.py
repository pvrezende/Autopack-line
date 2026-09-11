import time
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from app.core.config import settings

MAX_ATTEMPTS = 60
STABLE_SUCCESSES = 3


def main() -> None:
    engine = create_engine(settings.database_url, pool_pre_ping=True)
    stable = 0
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            with engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            stable += 1
            if stable >= STABLE_SUCCESSES:
                print("Banco MySQL disponível e estável.", flush=True)
                return
        except SQLAlchemyError as exc:
            stable = 0
            print(f"Aguardando MySQL ({attempt}/{MAX_ATTEMPTS}): {exc.__class__.__name__}", flush=True)
        time.sleep(1)
    raise SystemExit("MySQL não ficou disponível dentro do tempo esperado.")


if __name__ == "__main__":
    main()
