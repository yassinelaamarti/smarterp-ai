from sqlalchemy import create_engine, inspect
from app.config import settings
import sys

engine = create_engine(settings.database_url)
inspector = inspect(engine)

print("Tables in smarterp_ai inside container:")
for table_name in inspector.get_table_names():
    print(f"\nTable: {table_name}")
    for column in inspector.get_columns(table_name):
        col_type = str(column["type"])
        nullable = column["nullable"]
        default = column.get("default", None)
        print(f"  Column: {column['name']} ({col_type}) - Nullable: {nullable} - Default: {default}")
