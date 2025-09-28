"""
基础Service层 - 使用策略模式和模板方法模式
"""

from abc import ABC, abstractmethod
from typing import TypeVar, Generic, Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from ..repositories.base import BaseRepository
from ..core.exceptions import BusinessLogicError, ValidationError

ModelType = TypeVar("ModelType")
CreateSchemaType = TypeVar("CreateSchemaType")
UpdateSchemaType = TypeVar("UpdateSchemaType")
ReadSchemaType = TypeVar("ReadSchemaType")


class IBusinessRule(ABC):
    """业务规则接口"""

    @abstractmethod
    async def validate(self, data: Any, context: Dict[str, Any] = None) -> bool:
        """验证业务规则"""
        pass

    @abstractmethod
    def get_error_message(self) -> str:
        """获取错误消息"""
        pass


class IValidationStrategy(ABC):
    """验证策略接口"""

    @abstractmethod
    async def validate_create(self, data: CreateSchemaType) -> bool:
        """创建验证"""
        pass

    @abstractmethod
    async def validate_update(self, id: UUID, data: UpdateSchemaType) -> bool:
        """更新验证"""
        pass


class IService(
    ABC, Generic[ModelType, CreateSchemaType, UpdateSchemaType, ReadSchemaType]
):
    """Service接口"""

    @abstractmethod
    async def create(self, obj_in: CreateSchemaType) -> ReadSchemaType:
        """创建对象"""
        pass

    @abstractmethod
    async def get(self, id: UUID) -> Optional[ReadSchemaType]:
        """获取对象"""
        pass

    @abstractmethod
    async def get_multi(
        self, skip: int = 0, limit: int = 100, **filters
    ) -> List[ReadSchemaType]:
        """获取多个对象"""
        pass

    @abstractmethod
    async def update(
        self, id: UUID, obj_in: UpdateSchemaType
    ) -> Optional[ReadSchemaType]:
        """更新对象"""
        pass

    @abstractmethod
    async def delete(self, id: UUID) -> bool:
        """删除对象"""
        pass


class BaseService(
    IService[ModelType, CreateSchemaType, UpdateSchemaType, ReadSchemaType]
):
    """基础Service实现 - 模板方法模式"""

    def __init__(
        self,
        repository: BaseRepository,
        read_schema: type[ReadSchemaType],
        validation_strategy: Optional[IValidationStrategy] = None,
        business_rules: Optional[List[IBusinessRule]] = None,
    ):
        self.repository = repository
        self.read_schema = read_schema
        self.validation_strategy = validation_strategy
        self.business_rules = business_rules or []

    async def create(self, obj_in: CreateSchemaType) -> ReadSchemaType:
        """创建对象 - 模板方法"""
        # 1. 前置验证
        await self._validate_create(obj_in)

        # 2. 业务规则验证
        await self._validate_business_rules(obj_in, {"operation": "create"})

        # 3. 执行创建
        db_obj = await self.repository.create(obj_in)

        # 4. 后置处理
        await self._post_create_hook(db_obj)

        # 5. 返回结果
        return self.read_schema.model_validate(db_obj)

    async def get(self, id: UUID) -> Optional[ReadSchemaType]:
        """获取对象"""
        db_obj = await self.repository.get(id)
        if db_obj:
            return self.read_schema.model_validate(db_obj)
        return None

    async def get_multi(
        self, skip: int = 0, limit: int = 100, **filters
    ) -> List[ReadSchemaType]:
        """获取多个对象"""
        db_objs = await self.repository.get_multi(skip=skip, limit=limit, **filters)
        return [self.read_schema.model_validate(obj) for obj in db_objs]

    async def update(
        self, id: UUID, obj_in: UpdateSchemaType
    ) -> Optional[ReadSchemaType]:
        """更新对象 - 模板方法"""
        # 1. 检查对象是否存在
        existing_obj = await self.repository.get(id)
        if not existing_obj:
            return None

        # 2. 前置验证
        await self._validate_update(id, obj_in)

        # 3. 业务规则验证
        await self._validate_business_rules(
            obj_in, {"operation": "update", "existing_obj": existing_obj}
        )

        # 4. 执行更新
        updated_obj = await self.repository.update(id, obj_in)

        # 5. 后置处理
        await self._post_update_hook(updated_obj, existing_obj)

        # 6. 返回结果
        return self.read_schema.model_validate(updated_obj)

    async def delete(self, id: UUID) -> bool:
        """删除对象 - 模板方法"""
        # 1. 检查对象是否存在
        existing_obj = await self.repository.get(id)
        if not existing_obj:
            return False

        # 2. 删除前验证
        await self._validate_delete(id, existing_obj)

        # 3. 执行删除
        result = await self.repository.delete(id)

        # 4. 后置处理
        if result:
            await self._post_delete_hook(existing_obj)

        return result

    async def count(self, **filters) -> int:
        """统计数量"""
        return await self.repository.count(**filters)

    async def exists(self, id: UUID) -> bool:
        """检查对象是否存在"""
        return await self.repository.exists(id)

    # 钩子方法 - 子类可以重写
    async def _validate_create(self, obj_in: CreateSchemaType):
        """创建前验证钩子"""
        if self.validation_strategy:
            is_valid = await self.validation_strategy.validate_create(obj_in)
            if not is_valid:
                raise ValidationError("创建数据验证失败")

    async def _validate_update(self, id: UUID, obj_in: UpdateSchemaType):
        """更新前验证钩子"""
        if self.validation_strategy:
            is_valid = await self.validation_strategy.validate_update(id, obj_in)
            if not is_valid:
                raise ValidationError("更新数据验证失败")

    async def _validate_delete(self, id: UUID, existing_obj: ModelType):
        """删除前验证钩子"""
        # 子类可以重写此方法添加删除验证逻辑
        pass

    async def _validate_business_rules(self, data: Any, context: Dict[str, Any]):
        """业务规则验证"""
        for rule in self.business_rules:
            is_valid = await rule.validate(data, context)
            if not is_valid:
                raise BusinessLogicError(rule.get_error_message())

    async def _post_create_hook(self, created_obj: ModelType):
        """创建后钩子"""
        # 子类可以重写此方法添加创建后逻辑
        pass

    async def _post_update_hook(self, updated_obj: ModelType, original_obj: ModelType):
        """更新后钩子"""
        # 子类可以重写此方法添加更新后逻辑
        pass

    async def _post_delete_hook(self, deleted_obj: ModelType):
        """删除后钩子"""
        # 子类可以重写此方法添加删除后逻辑
        pass


class ServiceFactory:
    """Service工厂类"""

    @staticmethod
    def create_service(
        repository: BaseRepository,
        read_schema: type,
        service_class: type = None,
        validation_strategy: Optional[IValidationStrategy] = None,
        business_rules: Optional[List[IBusinessRule]] = None,
    ) -> BaseService:
        """创建Service实例"""
        if service_class:
            return service_class(
                repository, read_schema, validation_strategy, business_rules
            )
        return BaseService(repository, read_schema, validation_strategy, business_rules)
