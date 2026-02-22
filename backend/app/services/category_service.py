from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.rss_models import Category
from app.api.schemas import CategoryCreate, CategoryUpdate


class CategoryService:
    """Service for category management"""

    def __init__(self, db: Session):
        self.db = db

    def get_categories(self) -> List[Category]:
        """Get all categories"""
        return self.db.query(Category).order_by(Category.name).all()

    def get_category(self, category_id: int) -> Optional[Category]:
        """Get category by ID"""
        return self.db.query(Category).filter(Category.id == category_id).first()

    def get_category_by_name(self, name: str) -> Optional[Category]:
        """Get category by name"""
        return self.db.query(Category).filter(Category.name == name).first()

    def create_category(self, category: CategoryCreate) -> Category:
        """Create a new category"""
        # Check if category with same name exists
        existing = self.get_category_by_name(category.name)
        if existing:
            raise ValueError(f"Category '{category.name}' already exists")

        db_category = Category(**category.model_dump())
        self.db.add(db_category)
        self.db.commit()
        self.db.refresh(db_category)
        return db_category

    def update_category(self, category_id: int, category: CategoryUpdate) -> Optional[Category]:
        """Update an existing category"""
        db_category = self.get_category(category_id)
        if not db_category:
            return None

        # Check for duplicate name if name is being changed
        if category.name and category.name != db_category.name:
            existing = self.get_category_by_name(category.name)
            if existing:
                raise ValueError(f"Category '{category.name}' already exists")

        update_data = category.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_category, field, value)

        self.db.commit()
        self.db.refresh(db_category)
        return db_category

    def delete_category(self, category_id: int) -> bool:
        """Delete a category"""
        db_category = self.get_category(category_id)
        if not db_category:
            return False

        self.db.delete(db_category)
        self.db.commit()
        return True

    def initialize_default_categories(self):
        """Initialize default categories"""
        default_categories = [
            {"name": "AI", "description": "AI 产品发布、API/SDK 更新、AI 应用案例", "color": "#6366f1"},
            {"name": "Technology", "description": "科技行业综合资讯、硬件与平台动态", "color": "#3b82f6"},
            {"name": "Internet", "description": "互联网行业新闻、大厂动态、行业趋势", "color": "#f97316"},
            {"name": "Developer", "description": "编程语言、框架更新、开发工具、开源项目", "color": "#14b8a6"},
            {"name": "Cloud & DevOps", "description": "云服务、容器化、CI/CD、基础设施", "color": "#06b6d4"},
            {"name": "Cybersecurity", "description": "安全漏洞通告、安全实践、数据隐私", "color": "#ef4444"},
            {"name": "Startup & Product", "description": "创业融资、新产品发布、产品设计", "color": "#eab308"},
        ]

        for cat_data in default_categories:
            existing = self.get_category_by_name(cat_data["name"])
            if not existing:
                self.db.add(Category(**cat_data))

        self.db.commit()
