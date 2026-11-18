from uuid import uuid4
import psycopg
from catalogue.infrastructure.database import connect, quote_identifier
from catalogue.schemas.product import Product, ProductCreate, ProductUpdate

class ProductRepository:
    def __init__(self, settings):
        self.settings = settings
        self.schema = quote_identifier(settings.schema_name)
        self.table = f"{quote_identifier(settings.schema_name)}.products"

    def list(self, search, published, limit, offset, category_slug=None):
        clauses, params = [], []
        if search:
            clauses.append("(name ILIKE %s OR sku ILIKE %s)"); params.extend([f"%{search}%", f"%{search}%"])
        if published is not None:
            clauses.append("published = %s"); params.append(published)
        if category_slug:
            clauses.append(
                f"EXISTS (SELECT 1 FROM {self.schema}.product_categories pc "
                f"JOIN {self.schema}.categories c ON c.id = pc.category_id "
                f"WHERE pc.product_id = products.id AND c.slug = %s)"
            )
            params.append(category_slug)
        where = " WHERE " + " AND ".join(clauses) if clauses else ""
        with connect(self.settings) as db:
            rows = db.execute(f"SELECT id,sku,name,description,price_cents,published FROM {self.table}{where} ORDER BY name LIMIT %s OFFSET %s", [*params, limit, offset]).fetchall()
        return [Product(id=r[0], sku=r[1], name=r[2], description=r[3], price_cents=r[4], published=r[5]) for r in rows]

    def get(self, product_id) -> Product:
        with connect(self.settings) as db:
            row = db.execute(f"SELECT id,sku,name,description,price_cents,published FROM {self.table} WHERE id = %s", (product_id,)).fetchone()
        if row is None:
            raise LookupError("Product not found")
        return Product(id=row[0], sku=row[1], name=row[2], description=row[3], price_cents=row[4], published=row[5])

    def create(self, payload: ProductCreate) -> Product:
        try:
            with connect(self.settings) as db:
                row = db.execute(f"INSERT INTO {self.table} (id,sku,name,description,price_cents,published) VALUES (%s,%s,%s,%s,%s,%s) RETURNING id,sku,name,description,price_cents,published", (uuid4(), payload.sku, payload.name, payload.description, payload.price_cents, payload.published)).fetchone()
                db.commit()
        except psycopg.errors.UniqueViolation as exc:
            raise ValueError("A product with this SKU already exists") from exc
        return Product(id=row[0], sku=row[1], name=row[2], description=row[3], price_cents=row[4], published=row[5])

    def update(self, product_id, payload: ProductUpdate) -> Product:
        values = payload.model_dump(exclude_unset=True)
        if not values:
            raise ValueError("At least one product field is required")
        assignments = ", ".join(f"{key} = %s" for key in values)
        with connect(self.settings) as db:
            row = db.execute(f"UPDATE {self.table} SET {assignments} WHERE id = %s RETURNING id,sku,name,description,price_cents,published", [*values.values(), product_id]).fetchone()
            if row is None:
                raise LookupError("Product not found")
            db.commit()
        return Product(id=row[0], sku=row[1], name=row[2], description=row[3], price_cents=row[4], published=row[5])

    def delete(self, product_id) -> None:
        with connect(self.settings) as db:
            result = db.execute(f"DELETE FROM {self.table} WHERE id = %s", (product_id,))
            if result.rowcount == 0:
                raise LookupError("Product not found")
            db.commit()

    def categories(self, product_id):
        with connect(self.settings) as db:
            return db.execute(f"SELECT c.id,c.name,c.slug,c.description FROM {self.schema}.categories c JOIN {self.schema}.product_categories pc ON pc.category_id=c.id WHERE pc.product_id=%s ORDER BY c.name", (product_id,)).fetchall()

    def public_categories(self):
        with connect(self.settings) as db:
            rows = db.execute(
                f"SELECT c.id,c.name,c.slug,c.description FROM {self.schema}.categories c "
                f"WHERE EXISTS (SELECT 1 FROM {self.schema}.product_categories pc "
                f"JOIN {self.table} p ON p.id = pc.product_id "
                f"WHERE pc.category_id = c.id AND p.published = TRUE) "
                "ORDER BY c.name"
            ).fetchall()
        return rows

    def attach_category(self, product_id, category_id):
        with connect(self.settings) as db:
            if db.execute(f"SELECT 1 FROM {self.table} WHERE id=%s", (product_id,)).fetchone() is None: raise LookupError("Product not found")
            if db.execute(f"SELECT 1 FROM {self.schema}.categories WHERE id=%s", (category_id,)).fetchone() is None: raise LookupError("Category not found")
            db.execute(f"INSERT INTO {self.schema}.product_categories(product_id,category_id) VALUES(%s,%s) ON CONFLICT DO NOTHING", (product_id, category_id)); db.commit()

    def detach_category(self, product_id, category_id):
        with connect(self.settings) as db:
            result = db.execute(f"DELETE FROM {self.schema}.product_categories WHERE product_id=%s AND category_id=%s", (product_id, category_id))
            if result.rowcount == 0: raise LookupError("Product category assignment not found")
            db.commit()
