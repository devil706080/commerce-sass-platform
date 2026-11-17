from catalogue.infrastructure.category_repository import CategoryRepository

class CategoryService:
    def __init__(self, repository: CategoryRepository): self.repository = repository
    def list_categories(self): return self.repository.list()
    def create_category(self, payload): return self.repository.create(payload)
    def update_category(self, category_id, payload): return self.repository.update(category_id, payload)
    def delete_category(self, category_id): return self.repository.delete(category_id)
