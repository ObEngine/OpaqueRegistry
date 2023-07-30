import sqlalchemy
from sqlalchemy.schema import DDL

from opaque_registry.database.models import Base

STRING_TO_SHARD_ID_DEFINITION = """CREATE OR REPLACE FUNCTION string_to_shard_id(input_string TEXT, shards_amount INT)
RETURNS INTEGER AS $$
BEGIN
    RETURN (('x' || substr(md5(input_string), 1, 8))::bit(32)::bigint) %% (shards_amount + 1);
END;
$$ LANGUAGE plpgsql;"""

sqlalchemy.event.listen(
    Base.metadata, "before_create", DDL(STRING_TO_SHARD_ID_DEFINITION)
)
string_to_shard_id = sqlalchemy.func.string_to_shard_id
