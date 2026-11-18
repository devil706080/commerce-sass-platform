from catalogue.infrastructure.extended_repository import ExtendedRepository

class ExtendedService:
    def __init__(self, repository: ExtendedRepository): self.repository = repository
    def list_images(self, product_id): return self.repository.images(product_id)
    def add_image(self, product_id, payload): return self.repository.add_image(product_id, payload)
    def update_image(self, product_id, image_id, payload): return self.repository.update_image(product_id, image_id, payload)
    def delete_image(self, product_id, image_id): return self.repository.delete_image(product_id, image_id)
    def list_variants(self, product_id): return self.repository.variants(product_id)
    def add_variant(self, product_id, payload): return self.repository.add_variant(product_id, payload)
    def update_variant(self, product_id, variant_id, payload): return self.repository.update_variant(product_id, variant_id, payload)
    def delete_variant(self, product_id, variant_id): return self.repository.delete_variant(product_id, variant_id)
    def list_prices(self, product_id): return self.repository.prices(product_id)
    def add_price(self, product_id, payload): return self.repository.add_price(product_id, payload)
    def update_price(self, product_id, price_id, payload): return self.repository.update_price(product_id, price_id, payload)
    def delete_price(self, product_id, price_id): return self.repository.delete_price(product_id, price_id)
    def public_images(self, product_id): return self.repository.public_images(product_id)
