from sqlalchemy.engine.url import make_url


def inject_psycopg_dialect(db_url: str) -> str:
    parsed_db_url = make_url(db_url)

    if parsed_db_url.drivername == "postgresql":
        return parsed_db_url.set(drivername=parsed_db_url.drivername + "+psycopg")
    return parsed_db_url
