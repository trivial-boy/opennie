"""
基础Repository模式实现
"""

from abc import ABC, abstractmethod
from typing import TypeVar, Generic, List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func
from sqlalchemy.orm import selectinload
from uuid import UUID

ModelType = TypeVar("ModelType")
CreateSchemaType = TypeVar("CreateSchemaType")
UpdateSchemaType = TypeVar("UpdateSchemaType")


class IRepository(ABC, Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """Repository接口"""

    @abstractmethod
    async def create(self, obj_in: CreateSchemaType) -> ModelType:
        """创建对象"""
        pass

    @abstractmethod
    async def get(self, id: UUID) -> Optional[ModelType]:
        """根据ID获取对象"""
        pass

    @abstractmethod
    async def get_multi(
        self, skip: int = 0, limit: int = 100, **filters
    ) -> List[ModelType]:
        """获取多个对象"""
        pass

    @abstractmethod
    async def update(self, id: UUID, obj_in: UpdateSchemaType) -> Optional[ModelType]:
        """更新对象"""
        pass

    @abstractmethod
    async def delete(self, id: UUID) -> bool:
        """删除对象"""
        pass

    @abstractmethod
    async def count(self, **filters) -> int:
        """统计数量"""
        pass


class BaseRepository(IRepository[ModelType, CreateSchemaType, UpdateSchemaType]):
    """基础Repository实现类"""

    def __init__(self, model: type[ModelType], db_session: AsyncSession):
        self.model = model
        self.db = db_session

    async def create(self, obj_in: CreateSchemaType) -> ModelType:
        """创建对象"""
        obj_data = obj_in.dict() if hasattr(obj_in, "dict") else obj_in
        db_obj = self.model(**obj_data)
        self.db.add(db_obj)
        await self.db.flush()
        await self.db.refresh(db_obj)
        return db_obj

    async def get(self, id: UUID) -> Optional[ModelType]:
        """根据ID获取对象"""
        stmt = select(self.model).where(self.model.id == id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_field(self, field_name: str, value: Any) -> Optional[ModelType]:
        """根据字段获取对象"""
        field = getattr(self.model, field_name)
        stmt = select(self.model).where(field == value)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_multi(
        self, skip: int = 0, limit: int = 100, **filters
    ) -> List[ModelType]:
        """获取多个对象"""
        stmt = select(self.model)

        # 应用过滤条件
        for field_name, value in filters.items():
            if hasattr(self.model, field_name) and value is not None:
                field = getattr(self.model, field_name)
                stmt = stmt.where(field == value)

        stmt = stmt.offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_multi_with_relations(
        self, relations: List[str], skip: int = 0, limit: int = 100, **filters
    ) -> List[ModelType]:
        """获取带关联数据的多个对象"""
        stmt = select(self.model)

        # 预加载关联数据
        for relation in relations:
            if hasattr(self.model, relation):
                stmt = stmt.options(selectinload(getattr(self.model, relation)))

        # 应用过滤条件
        for field_name, value in filters.items():
            if hasattr(self.model, field_name) and value is not None:
                field = getattr(self.model, field_name)
                stmt = stmt.where(field == value)

        stmt = stmt.offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def update(self, id: UUID, obj_in: UpdateSchemaType) -> Optional[ModelType]:
        """更新对象"""
        # 获取要更新的对象
        db_obj = await self.get(id)
        if not db_obj:
            return None

        # 获取更新数据
        if hasattr(obj_in, "dict"):
            update_data = obj_in.dict(exclude_unset=True)
        else:
            update_data = obj_in

        # 更新字段
        for field, value in update_data.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)

        await self.db.flush()
        await self.db.refresh(db_obj)
        return db_obj

    async def delete(self, id: UUID) -> bool:
        """删除对象"""
        db_obj = await self.get(id)
        if not db_obj:
            return False

        await self.db.delete(db_obj)
        await self.db.flush()
        return True

    async def count(self, **filters) -> int:
        """统计数量"""
        stmt = select(func.count(self.model.id))

        # 应用过滤条件
        for field_name, value in filters.items():
            if hasattr(self.model, field_name) and value is not None:
                field = getattr(self.model, field_name)
                stmt = stmt.where(field == value)

        result = await self.db.execute(stmt)
        return result.scalar()

    async def exists(self, id: UUID) -> bool:
        """检查对象是否存在"""
        stmt = select(self.model.id).where(self.model.id == id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def bulk_create(self, objs_in: List[CreateSchemaType]) -> List[ModelType]:
        """批量创建对象"""
        db_objs = []
        for obj_in in objs_in:
            obj_data = obj_in.dict() if hasattr(obj_in, "dict") else obj_in
            db_obj = self.model(**obj_data)
            db_objs.append(db_obj)

        self.db.add_all(db_objs)
        await self.db.flush()

        for db_obj in db_objs:
            await self.db.refresh(db_obj)

        return db_objs

    async def bulk_update(
        self, updates: Dict[UUID, UpdateSchemaType]
    ) -> List[ModelType]:
        """批量更新对象"""
        updated_objs = []

        for obj_id, obj_in in updates.items():
            updated_obj = await self.update(obj_id, obj_in)
            if updated_obj:
                updated_objs.append(updated_obj)

        return updated_objs

    async def search(
        self, search_term: str, search_fields: List[str]
    ) -> List[ModelType]:
        """搜索功能"""
        stmt = select(self.model)

        conditions = []
        for field_name in search_fields:
            if hasattr(self.model, field_name):
                field = getattr(self.model, field_name)
                if hasattr(field.type, "python_type") and field.type.python_type == str:
                    conditions.append(field.ilike(f"%{search_term}%"))

        if conditions:
            from sqlalchemy import or_

            stmt = stmt.where(or_(*conditions))

        result = await self.db.execute(stmt)
        return result.scalars().all()


class RepositoryFactory:
    """Repository工厂类"""

    @staticmethod
    def create_repository(
        model: type[ModelType], db_session: AsyncSession, repository_class: type = None
    ) -> BaseRepository:
        """创建Repository实例"""
        if repository_class:
            return repository_class(model, db_session)
        return BaseRepository(model, db_session)
