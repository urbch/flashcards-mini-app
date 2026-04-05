import pytest
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from api.database import Base  # подправь путь, если нужно

# Тестовая БД (используем ту же, что и основной сервис)
TEST_DATABASE_URL = os.getenv("DATABASE_URL")  # или отдельный URL для тестов

engine = create_engine(TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db_session():
    """Создаёт сессию и очищает таблицы перед/после каждого теста."""
    # Создаём таблицы один раз (если их ещё нет)
    Base.metadata.create_all(bind=engine)

    db = TestingSessionLocal()
    try:
        # Очистка перед тестом
        for model in [LangCard, Card, Deck, User]:
            db.execute(delete(model))
        db.commit()

        yield db

        # Очистка после теста
        for model in [LangCard, Card, Deck, User]:
            db.execute(delete(model))
        db.commit()
    finally:
        db.close()