from uuid import uuid4
import psycopg
from catalogue.infrastructure.database import connect, quote_identifier
from catalogue.schemas.category import Category, CategoryCreate, CategoryUpdate

class CategoryRepository:
    def __init__(self, settings):
        self.settings = settings
        self.table = f"{quote_identifier(settings.schema_name)}.categories"

    def list(self):
        with connect(self.settings) as db:
            rows = db.execute(f"SELECT id,name,slug,description FROM {self.table} ORDER BY name").fetchall()
        return [Category(id=r[0], name=r[1], slug=r[2], description=r[3]) for r in rows]

    def create(self, payload: CategoryCreate):
        try:
            with connect(self.settings) as db:
                row = db.execute(f"INSERT INTO {self.table} (id,name,slug,description) VALUES (%s,%s,%s,%s) RETURNING id,name,slug,description", (uuid4(), payload.name, payload.slug, payload.description)).fetchone()
                db.commit()
        except psycopg.errors.UniqueViolation as exc:
            raise ValueError("A category with this slug already exists") from exc
        return Category(id=row[0], name=row[1], slug=row[2], description=row[3])

    def update(self, category_id, payload: CategoryUpdate):
        values = payload.model_dump(exclude_unset=True)
        if not values: raise ValueError("At least one category field is required")
        assignments = ", ".join(f"{key} = %s" for key in values)
        with connect(self.settings) as db:
            row = db.execute(f"UPDATE {self.table} SET {assignments} WHERE id = %s RETURNING id,name,slug,description", [*values.values(), category_id]).fetchone()
            if row is None: raise LookupError("Category not found")
            db.commit()
        return Category(id=row[0], name=row[1], slug=row[2], description=row[3])

    def delete(self, category_id):
        with connect(self.settings) as db:
            result = db.execute(f"DELETE FROM {self.table} WHERE id = %s", (category_id,))
            if result.rowcount == 0: raise LookupError("Category not found")
            db.commit()
