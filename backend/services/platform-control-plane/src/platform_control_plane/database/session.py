from collections.abc import Iterator

from sqlalchemy.orm import Session, sessionmaker


def session_scope(factory: sessionmaker[Session]) -> Iterator[Session]:
    with factory() as session:
        try:
            yield session
        except Exception:
            session.rollback()
            raise
