from uuid import uuid4
import json
import psycopg
from catalogue.infrastructure.database import connect, quote_identifier
from catalogue.schemas.extended import Image, ImageCreate, Variant, VariantCreate, PriceRule, PriceRuleCreate

class ExtendedRepository:
    def __init__(self, settings):
        self.settings = settings; self.schema = quote_identifier(settings.schema_name)
    def images(self, product_id):
        with connect(self.settings) as db:
            rows=db.execute(f"SELECT id,url,alt_text,sort_order FROM {self.schema}.product_images WHERE product_id=%s ORDER BY sort_order,id",(product_id,)).fetchall()
        return [Image(id=r[0],url=r[1],alt_text=r[2],sort_order=r[3]) for r in rows]
    def add_image(self, product_id, payload: ImageCreate):
        try:
            with connect(self.settings) as db:
                r=db.execute(f"INSERT INTO {self.schema}.product_images(id,product_id,url,alt_text,sort_order) VALUES(%s,%s,%s,%s,%s) RETURNING id,url,alt_text,sort_order",(uuid4(),product_id,payload.url,payload.alt_text,payload.sort_order)).fetchone(); db.commit()
        except psycopg.errors.ForeignKeyViolation as exc: raise LookupError("Product not found") from exc
        return Image(id=r[0],url=r[1],alt_text=r[2],sort_order=r[3])
    def variants(self, product_id):
        with connect(self.settings) as db:
            rows=db.execute(f"SELECT id,product_id,sku,name,price_cents,attributes FROM {self.schema}.product_variants WHERE product_id=%s ORDER BY name",(product_id,)).fetchall()
        return [Variant(id=r[0],product_id=r[1],sku=r[2],name=r[3],price_cents=r[4],attributes=r[5]) for r in rows]
    def add_variant(self, product_id, payload: VariantCreate):
        try:
            with connect(self.settings) as db:
                r=db.execute(f"INSERT INTO {self.schema}.product_variants(id,product_id,sku,name,price_cents,attributes) VALUES(%s,%s,%s,%s,%s,%s) RETURNING id,product_id,sku,name,price_cents,attributes",(uuid4(),product_id,payload.sku,payload.name,payload.price_cents,json.dumps(payload.attributes))).fetchone(); db.commit()
        except psycopg.errors.UniqueViolation as exc: raise ValueError("A variant with this SKU already exists") from exc
        except psycopg.errors.ForeignKeyViolation as exc: raise LookupError("Product not found") from exc
        return Variant(id=r[0],product_id=r[1],sku=r[2],name=r[3],price_cents=r[4],attributes=r[5])
    def prices(self, product_id):
        with connect(self.settings) as db:
            rows=db.execute(f"SELECT id,name,price_cents,currency,active FROM {self.schema}.product_prices WHERE product_id=%s ORDER BY name",(product_id,)).fetchall()
        return [PriceRule(id=r[0],name=r[1],price_cents=r[2],currency=r[3],active=r[4]) for r in rows]
    def add_price(self, product_id, payload: PriceRuleCreate):
        try:
            with connect(self.settings) as db:
                r=db.execute(f"INSERT INTO {self.schema}.product_prices(id,product_id,name,price_cents,currency,active) VALUES(%s,%s,%s,%s,%s,%s) RETURNING id,name,price_cents,currency,active",(uuid4(),product_id,payload.name,payload.price_cents,payload.currency,payload.active)).fetchone(); db.commit()
        except psycopg.errors.ForeignKeyViolation as exc: raise LookupError("Product not found") from exc
        return PriceRule(id=r[0],name=r[1],price_cents=r[2],currency=r[3],active=r[4])
