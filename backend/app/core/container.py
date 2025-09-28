"""
依赖注入容器 - 使用IoC模式
"""

from typing import Dict, Any, Callable, TypeVar, Type, Optional
from abc import ABC, abstractmethod
from enum import Enum
import asyncio
import inspect
import logging

logger = logging.getLogger(__name__)

T = TypeVar("T")


class LifecycleType(Enum):
    """生命周期类型"""

    SINGLETON = "singleton"  # 单例
    TRANSIENT = "transient"  # 瞬时
    SCOPED = "scoped"  # 作用域


class IDependencyContainer(ABC):
    """依赖容器接口"""

    @abstractmethod
    def register(
        self,
        interface: Type[T],
        implementation: Type[T],
        lifecycle: LifecycleType = LifecycleType.TRANSIENT,
    ):
        """注册依赖"""
        pass

    @abstractmethod
    def register_instance(self, interface: Type[T], instance: T):
        """注册实例"""
        pass

    @abstractmethod
    def register_factory(
        self,
        interface: Type[T],
        factory: Callable[[], T],
        lifecycle: LifecycleType = LifecycleType.TRANSIENT,
    ):
        """注册工厂方法"""
        pass

    @abstractmethod
    async def resolve(self, interface: Type[T]) -> T:
        """解析依赖"""
        pass

    @abstractmethod
    def is_registered(self, interface: Type[T]) -> bool:
        """检查是否已注册"""
        pass


class DependencyRegistration:
    """依赖注册信息"""

    def __init__(
        self,
        interface: Type,
        implementation: Optional[Type] = None,
        instance: Optional[Any] = None,
        factory: Optional[Callable] = None,
        lifecycle: LifecycleType = LifecycleType.TRANSIENT,
    ):
        self.interface = interface
        self.implementation = implementation
        self.instance = instance
        self.factory = factory
        self.lifecycle = lifecycle


class DependencyContainer(IDependencyContainer):
    """依赖注入容器实现"""

    def __init__(self):
        self._registrations: Dict[Type, DependencyRegistration] = {}
        self._singletons: Dict[Type, Any] = {}
        self._scoped_instances: Dict[str, Dict[Type, Any]] = {}
        self._current_scope: Optional[str] = None

    def register(
        self,
        interface: Type[T],
        implementation: Type[T],
        lifecycle: LifecycleType = LifecycleType.TRANSIENT,
    ):
        """注册依赖"""
        registration = DependencyRegistration(
            interface=interface, implementation=implementation, lifecycle=lifecycle
        )
        self._registrations[interface] = registration
        logger.debug(
            f"Registered {interface.__name__} -> {implementation.__name__} ({lifecycle.value})"
        )

    def register_instance(self, interface: Type[T], instance: T):
        """注册实例"""
        registration = DependencyRegistration(
            interface=interface, instance=instance, lifecycle=LifecycleType.SINGLETON
        )
        self._registrations[interface] = registration
        self._singletons[interface] = instance
        logger.debug(f"Registered instance {interface.__name__}")

    def register_factory(
        self,
        interface: Type[T],
        factory: Callable[[], T],
        lifecycle: LifecycleType = LifecycleType.TRANSIENT,
    ):
        """注册工厂方法"""
        registration = DependencyRegistration(
            interface=interface, factory=factory, lifecycle=lifecycle
        )
        self._registrations[interface] = registration
        logger.debug(f"Registered factory for {interface.__name__} ({lifecycle.value})")

    async def resolve(self, interface: Type[T]) -> T:
        """解析依赖"""
        if not self.is_registered(interface):
            raise ValueError(f"Interface {interface.__name__} is not registered")

        registration = self._registrations[interface]

        # 单例模式
        if registration.lifecycle == LifecycleType.SINGLETON:
            if interface in self._singletons:
                return self._singletons[interface]

            instance = await self._create_instance(registration)
            self._singletons[interface] = instance
            return instance

        # 作用域模式
        elif registration.lifecycle == LifecycleType.SCOPED:
            if self._current_scope:
                scope_instances = self._scoped_instances.get(self._current_scope, {})
                if interface in scope_instances:
                    return scope_instances[interface]

                instance = await self._create_instance(registration)
                if self._current_scope not in self._scoped_instances:
                    self._scoped_instances[self._current_scope] = {}
                self._scoped_instances[self._current_scope][interface] = instance
                return instance

        # 瞬时模式（默认）
        return await self._create_instance(registration)

    async def _create_instance(self, registration: DependencyRegistration) -> Any:
        """创建实例"""
        if registration.instance is not None:
            return registration.instance

        if registration.factory is not None:
            if asyncio.iscoroutinefunction(registration.factory):
                return await registration.factory()
            return registration.factory()

        if registration.implementation is not None:
            return await self._inject_dependencies(registration.implementation)

        raise ValueError(
            f"Cannot create instance for {registration.interface.__name__}"
        )

    async def _inject_dependencies(self, cls: Type) -> Any:
        """依赖注入"""
        # 获取构造函数签名
        signature = inspect.signature(cls.__init__)
        kwargs = {}

        for param_name, param in signature.parameters.items():
            if param_name == "self":
                continue

            # 检查参数是否有类型注解
            if param.annotation != inspect.Parameter.empty:
                if self.is_registered(param.annotation):
                    kwargs[param_name] = await self.resolve(param.annotation)
                elif param.default != inspect.Parameter.empty:
                    # 如果有默认值，使用默认值
                    kwargs[param_name] = param.default
                else:
                    logger.warning(
                        f"Cannot resolve dependency {param.annotation} for {cls.__name__}"
                    )

        return cls(**kwargs)

    def is_registered(self, interface: Type[T]) -> bool:
        """检查是否已注册"""
        return interface in self._registrations

    def begin_scope(self, scope_id: str):
        """开始新的作用域"""
        self._current_scope = scope_id
        if scope_id not in self._scoped_instances:
            self._scoped_instances[scope_id] = {}

    def end_scope(self, scope_id: str):
        """结束作用域"""
        if scope_id in self._scoped_instances:
            # 清理作用域实例
            del self._scoped_instances[scope_id]

        if self._current_scope == scope_id:
            self._current_scope = None

    def clear_singletons(self):
        """清除所有单例"""
        self._singletons.clear()

    def get_registrations(self) -> Dict[Type, DependencyRegistration]:
        """获取所有注册信息"""
        return self._registrations.copy()


class ContainerBuilder:
    """容器构建器"""

    def __init__(self):
        self.container = DependencyContainer()

    def add_singleton(
        self, interface: Type[T], implementation: Type[T]
    ) -> "ContainerBuilder":
        """添加单例"""
        self.container.register(interface, implementation, LifecycleType.SINGLETON)
        return self

    def add_transient(
        self, interface: Type[T], implementation: Type[T]
    ) -> "ContainerBuilder":
        """添加瞬时"""
        self.container.register(interface, implementation, LifecycleType.TRANSIENT)
        return self

    def add_scoped(
        self, interface: Type[T], implementation: Type[T]
    ) -> "ContainerBuilder":
        """添加作用域"""
        self.container.register(interface, implementation, LifecycleType.SCOPED)
        return self

    def add_instance(self, interface: Type[T], instance: T) -> "ContainerBuilder":
        """添加实例"""
        self.container.register_instance(interface, instance)
        return self

    def add_factory(
        self,
        interface: Type[T],
        factory: Callable[[], T],
        lifecycle: LifecycleType = LifecycleType.TRANSIENT,
    ) -> "ContainerBuilder":
        """添加工厂"""
        self.container.register_factory(interface, factory, lifecycle)
        return self

    def build(self) -> DependencyContainer:
        """构建容器"""
        return self.container


# 全局容器实例
_global_container: Optional[DependencyContainer] = None


def get_container() -> DependencyContainer:
    """获取全局容器"""
    global _global_container
    if _global_container is None:
        _global_container = DependencyContainer()
    return _global_container


def set_container(container: DependencyContainer):
    """设置全局容器"""
    global _global_container
    _global_container = container


# 装饰器用于依赖注入
def inject(interface: Type[T]):
    """依赖注入装饰器"""

    def decorator(func: Callable):
        async def wrapper(*args, **kwargs):
            container = get_container()
            dependency = await container.resolve(interface)
            return await func(dependency, *args, **kwargs)

        return wrapper

    return decorator
