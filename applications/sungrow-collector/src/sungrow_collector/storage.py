import uuid
from collections.abc import Mapping, Sequence
from typing import Any

from sqlalchemy import Column, Engine, MetaData, Table, Uuid, create_engine, inspect
from sqlalchemy.dialects import postgresql, sqlite

from sungrow_collector.mapping import MEASUREMENT_COLUMNS

TABLE_NAME = "inverter_readings"
CONFLICT_COLUMNS = ["system_id", "recorded_at", "source"]
INSERT_CHUNK_SIZE = 1000


class StorageError(Exception):
    pass


def create_db_engine(database_url: str) -> Engine:
    if database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+psycopg://", 1)
    return create_engine(database_url)


def reflect_readings_table(engine: Engine) -> Table:
    if not inspect(engine).has_table(TABLE_NAME):
        raise StorageError(
            f"table {TABLE_NAME!r} not found: run 'alembic upgrade head' in the SolarSense backend"
        )
    return Table(
        TABLE_NAME,
        MetaData(),
        Column("id", Uuid, primary_key=True),
        Column("system_id", Uuid),
        autoload_with=engine,
    )


def upsert_readings(
    engine: Engine,
    table: Table,
    *,
    system_id: uuid.UUID,
    source: str,
    readings: Sequence[Mapping[str, Any]],
) -> int:
    if not readings:
        return 0
    insert = sqlite.insert if engine.dialect.name == "sqlite" else postgresql.insert
    with engine.begin() as connection:
        for start in range(0, len(readings), INSERT_CHUNK_SIZE):
            rows = [
                {"id": uuid.uuid4(), "system_id": system_id, "source": source, **reading}
                for reading in readings[start : start + INSERT_CHUNK_SIZE]
            ]
            statement = insert(table).values(rows)
            statement = statement.on_conflict_do_update(
                index_elements=CONFLICT_COLUMNS,
                set_={column: statement.excluded[column] for column in MEASUREMENT_COLUMNS},
            )
            connection.execute(statement)
    return len(readings)
