"""
用户默认数据服务
在用户注册后自动创建默认账本和分类
"""

from sqlalchemy.ext.asyncio import AsyncSession
from ..models.user import User
from ..models.account import Account
from ..models.category import Category
from ..models.asset import Asset
from ..models.category import TransactionTypeEnum
from ..models.asset import AssetTypeEnum
import uuid
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class UserDefaultsService:
    """用户默认数据服务"""

    @staticmethod
    async def create_default_accounts(db: AsyncSession, user_id: uuid.UUID) -> None:
        """为新用户创建默认账本"""
        try:
            default_accounts = [
                {
                    "name": "个人账本",
                    "description": "记录个人日常收支",
                    "currency": "CNY",
                    "is_shared": False,
                },
                {
                    "name": "家庭账本",
                    "description": "记录家庭共同开销",
                    "currency": "CNY",
                    "is_shared": True,
                },
            ]

            for account_data in default_accounts:
                account = Account(
                    id=uuid.uuid4(),
                    user_id=user_id,
                    name=account_data["name"],
                    description=account_data["description"],
                    currency=account_data["currency"],
                    is_shared=account_data["is_shared"],
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                )
                db.add(account)

            await db.commit()
            logger.info(
                f"Created {len(default_accounts)} default accounts for user {user_id}"
            )

        except Exception as e:
            logger.error(f"Failed to create default accounts for user {user_id}: {e}")
            await db.rollback()
            raise

    @staticmethod
    async def create_default_categories(db: AsyncSession, user_id: uuid.UUID) -> None:
        """为新用户创建默认分类"""
        try:
            # 支出分类
            expense_categories = [
                {"name": "餐饮美食", "type": TransactionTypeEnum.EXPENSE, "icon": "🍽️"},
                {"name": "交通出行", "type": TransactionTypeEnum.EXPENSE, "icon": "🚗"},
                {"name": "购物消费", "type": TransactionTypeEnum.EXPENSE, "icon": "🛒"},
                {"name": "居住生活", "type": TransactionTypeEnum.EXPENSE, "icon": "🏠"},
                {"name": "娱乐休闲", "type": TransactionTypeEnum.EXPENSE, "icon": "🎬"},
                {"name": "医疗健康", "type": TransactionTypeEnum.EXPENSE, "icon": "🏥"},
                {"name": "学习教育", "type": TransactionTypeEnum.EXPENSE, "icon": "📚"},
                {"name": "其他支出", "type": TransactionTypeEnum.EXPENSE, "icon": "💸"},
            ]

            # 收入分类
            income_categories = [
                {"name": "工资收入", "type": TransactionTypeEnum.INCOME, "icon": "💰"},
                {"name": "投资收益", "type": TransactionTypeEnum.INCOME, "icon": "📈"},
                {"name": "兼职收入", "type": TransactionTypeEnum.INCOME, "icon": "💼"},
                {"name": "其他收入", "type": TransactionTypeEnum.INCOME, "icon": "💵"},
            ]

            # 创建主分类
            parent_categories = {}
            all_categories = expense_categories + income_categories

            for cat_data in all_categories:
                category = Category(
                    id=uuid.uuid4(),
                    user_id=user_id,
                    name=cat_data["name"],
                    type=cat_data["type"],
                    icon=cat_data["icon"],
                    is_system=True,  # 标记为系统默认分类
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                )
                db.add(category)
                parent_categories[cat_data["name"]] = category.id

            # 提交主分类
            await db.commit()

            # 创建子分类
            sub_categories = [
                # 餐饮美食子分类
                {
                    "name": "正餐",
                    "parent": "餐饮美食",
                    "type": TransactionTypeEnum.EXPENSE,
                },
                {
                    "name": "零食饮料",
                    "parent": "餐饮美食",
                    "type": TransactionTypeEnum.EXPENSE,
                },
                {
                    "name": "咖啡茶饮",
                    "parent": "餐饮美食",
                    "type": TransactionTypeEnum.EXPENSE,
                },
                # 交通出行子分类
                {
                    "name": "公共交通",
                    "parent": "交通出行",
                    "type": TransactionTypeEnum.EXPENSE,
                },
                {
                    "name": "打车费用",
                    "parent": "交通出行",
                    "type": TransactionTypeEnum.EXPENSE,
                },
                {
                    "name": "汽车相关",
                    "parent": "交通出行",
                    "type": TransactionTypeEnum.EXPENSE,
                },
                # 购物消费子分类
                {
                    "name": "服装鞋帽",
                    "parent": "购物消费",
                    "type": TransactionTypeEnum.EXPENSE,
                },
                {
                    "name": "数码电器",
                    "parent": "购物消费",
                    "type": TransactionTypeEnum.EXPENSE,
                },
                {
                    "name": "日用百货",
                    "parent": "购物消费",
                    "type": TransactionTypeEnum.EXPENSE,
                },
                # 居住生活子分类
                {
                    "name": "房租房贷",
                    "parent": "居住生活",
                    "type": TransactionTypeEnum.EXPENSE,
                },
                {
                    "name": "水电煤气",
                    "parent": "居住生活",
                    "type": TransactionTypeEnum.EXPENSE,
                },
                {
                    "name": "物业费用",
                    "parent": "居住生活",
                    "type": TransactionTypeEnum.EXPENSE,
                },
            ]

            for sub_cat in sub_categories:
                parent_id = parent_categories.get(sub_cat["parent"])
                if parent_id:
                    category = Category(
                        id=uuid.uuid4(),
                        user_id=user_id,
                        name=sub_cat["name"],
                        type=sub_cat["type"],
                        parent_id=parent_id,
                        is_system=True,
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow(),
                    )
                    db.add(category)

            await db.commit()
            logger.info(f"Created default categories for user {user_id}")

        except Exception as e:
            logger.error(f"Failed to create default categories for user {user_id}: {e}")
            await db.rollback()
            raise

    @staticmethod
    async def setup_user_defaults(db: AsyncSession, user_id: uuid.UUID) -> None:
        """为新用户设置所有默认数据"""
        try:
            # 创建默认账本
            await UserDefaultsService.create_default_accounts(db, user_id)

            # 创建默认分类
            await UserDefaultsService.create_default_categories(db, user_id)

            logger.info(f"Successfully set up all defaults for user {user_id}")

        except Exception as e:
            logger.error(f"Failed to setup defaults for user {user_id}: {e}")
            # 这里可以选择是否抛出异常，或者只记录日志继续
            # 因为用户注册已经成功，默认数据创建失败不应该影响注册流程
            pass


# 创建服务实例
user_defaults_service = UserDefaultsService()
