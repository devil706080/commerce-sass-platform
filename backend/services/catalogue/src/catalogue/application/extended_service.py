from catalogue.infrastructure.extended_repository import ExtendedRepository

class ExtendedService:
    def __init__(self, repository: ExtendedRepository): self.repository = repository
    def list_images(self, product_id): return self.repository.images(product_id)
    def add_image(self, product_id, payload): return self.repository.add_image(product_id, payload)
    def list_variants(self, product_id): return self.repository.variants(product_id)
    def add_variant(self, product_id, payload): return self.repository.add_variant(product_id, payload)
    def list_prices(self, product_id): return self.repository.prices(product_id)
    def add_price(self, product_id, payload): return self.repository.add_price(product_id, payload)
