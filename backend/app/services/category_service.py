from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.models.rss_models import Category
from app.api.schemas import CategoryCreate, CategoryUpdate


class CategoryService:
    """Service for category management"""

    def __init__(self, db: Session):
        self.db = db

    async def get_categories(self) -> List[Category]:
        """Get all categories"""
        return self.db.query(Category).order_by(Category.name).all()

    async def get_category(self, category_id: int) -> Optional[Category]:
        """Get category by ID"""
        return self.db.query(Category).filter(Category.id == category_id).first()

    async def get_category_by_name(self, name: str) -> Optional[Category]:
        """Get category by name"""
        return self.db.query(Category).filter(Category.name == name).first()

    async def create_category(self, category: CategoryCreate) -> Category:
        """Create a new category"""
        # Check if category with same name exists
        existing = await self.get_category_by_name(category.name)
        if existing:
            raise ValueError(f"Category '{category.name}' already exists")

        db_category = Category(**category.model_dump())
        self.db.add(db_category)
        self.db.commit()
        self.db.refresh(db_category)
        return db_category

    async def update_category(self, category_id: int, category: CategoryUpdate) -> Optional[Category]:
        """Update an existing category"""
        db_category = await self.get_category(category_id)
        if not db_category:
            return None

        # Check for duplicate name if name is being changed
        if category.name and category.name != db_category.name:
            existing = await self.get_category_by_name(category.name)
            if existing:
                raise ValueError(f"Category '{category.name}' already exists")

        update_data = category.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_category, field, value)

        self.db.commit()
        self.db.refresh(db_category)
        return db_category

    async def delete_category(self, category_id: int) -> bool:
        """Delete a category"""
        db_category = await self.get_category(category_id)
        if not db_category:
            return False

        self.db.delete(db_category)
        self.db.commit()
        return True

    async def initialize_default_categories(self):
        """Initialize default categories"""
        default_categories = [
            {"name": "AI", "description": "Artificial Intelligence news", "color": "#6366f1"},
            {"name": "Technology", "description": "Technology news and updates", "color": "#3b82f6"},
            {"name": "Business", "description": "Business and startup news", "color": "#10b981"},
            {"name": "Science", "description": "Scientific discoveries and research", "color": "#8b5cf6"},
            {"name": "Internet", "description": "Internet and social media news", "color": "#f59e0b"},
        ]

        for cat_data in default_categories:
            existing = await self.get_category_by_name(cat_data["name"])
            if not existing:
                self.db.add(Category(**cat_data))

        self.db.commit()