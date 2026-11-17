from catalogue.infrastructure.product_repository import ProductRepository
from catalogue.schemas.product import ProductCreate

class ProductService:
    def __init__(self, repository: ProductRepository): self.repository = repository
    def list_products(self, search, published, limit, offset): return self.repository.list(search, published, limit, offset)
    def get_product(self, product_id): return self.repository.get(product_id)
    def create_product(self, payload: ProductCreate): return self.repository.create(payload)
    def update_product(self, product_id, payload): return self.repository.update(product_id, payload)
    def delete_product(self, product_id): return self.repository.delete(product_id)
    def product_categories(self, product_id): return self.repository.categories(product_id)
    def attach_category(self, product_id, category_id): return self.repository.attach_category(product_id, category_id)
    def detach_category(self, product_id, category_id): return self.repository.detach_category(product_id, category_id)
