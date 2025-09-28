"""
分类API路由
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from typing import Optional, List
from ...core.database import get_db
from ...schemas.category import (
    CategoryCreate,
    CategoryRead,
    CategoryUpdate,
)
from ...schemas.common import ResponseModel
from ...models.user import User
from ...models.category import Category, TransactionTypeEnum
from ...api.deps import get_current_user
import uuid

router = APIRouter()


@router.post("", response_model=ResponseModel[CategoryRead], summary="创建分类")
async def create_category(
    category_data: CategoryCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """创建新分类"""
    # 检查同级分类名称是否重复
    conditions = [
        Category.user_id == current_user.id,
        Category.name == category_data.name,
        Category.type == category_data.type,
        Category.parent_id == category_data.parent_id,
    ]

    stmt = select(Category).where(and_(*conditions))
    existing_category = await db.execute(stmt)
    if existing_category.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="该分类名称在同级分类中已存在"
        )

    # 如果指定了父分类，验证父分类是否存在且属于当前用户
    if category_data.parent_id:
        parent_stmt = select(Category).where(
            (Category.id == category_data.parent_id)
            & (Category.user_id == current_user.id)
        )
        parent_result = await db.execute(parent_stmt)
        parent_category = parent_result.scalar_one_or_none()
        if not parent_category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="父分类不存在或无权限"
            )

        # 验证父分类和子分类类型一致
        if parent_category.type != category_data.type:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="子分类类型必须与父分类类型一致",
            )

    # 创建分类
    category = Category(user_id=current_user.id, **category_data.dict())
    db.add(category)
    await db.commit()
    await db.refresh(category)

    return ResponseModel(
        data=CategoryRead.model_validate(category), message="分类创建成功"
    )


@router.get(
    "", response_model=ResponseModel[List[CategoryRead]], summary="获取分类列表"
)
async def get_categories(
    type: Optional[TransactionTypeEnum] = Query(None, description="分类类型"),
    parent_id: Optional[uuid.UUID] = Query(None, description="父分类ID"),
    include_children: bool = Query(True, description="是否包含子分类"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取分类列表"""
    # 构建查询条件
    conditions = [Category.user_id == current_user.id]

    if type:
        conditions.append(Category.type == type)

    if parent_id is not None:
        conditions.append(Category.parent_id == parent_id)
    elif not include_children:
        # 如果不包含子分类且没有指定parent_id，则只查询顶级分类
        conditions.append(Category.parent_id.is_(None))

    stmt = select(Category).where(and_(*conditions)).order_by(Category.created_at)
    result = await db.execute(stmt)
    categories = result.scalars().all()

    # 如果需要包含子分类，构建层级结构
    if include_children and parent_id is None:
        category_dict = {}
        category_list = []

        # 先将所有分类转换为字典
        for category in categories:
            category_data = CategoryRead.model_validate(category)
            category_dict[str(category.id)] = category_data
            if category.parent_id is None:
                category_list.append(category_data)

        # 构建父子关系
        for category in categories:
            if category.parent_id:
                parent_id_str = str(category.parent_id)
                if parent_id_str in category_dict:
                    parent = category_dict[parent_id_str]
                    if not parent.children:
                        parent.children = []
                    parent.children.append(category_dict[str(category.id)])

        return ResponseModel(data=category_list)
    else:
        # 直接返回扁平列表
        category_list = [
            CategoryRead.model_validate(category) for category in categories
        ]
        return ResponseModel(data=category_list)


@router.get(
    "/{category_id}", response_model=ResponseModel[CategoryRead], summary="获取分类详情"
)
async def get_category(
    category_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取分类详情"""
    stmt = select(Category).where(
        (Category.id == category_id) & (Category.user_id == current_user.id)
    )
    result = await db.execute(stmt)
    category = result.scalar_one_or_none()

    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="分类不存在或无权限"
        )

    return ResponseModel(data=CategoryRead.model_validate(category))


@router.put(
    "/{category_id}", response_model=ResponseModel[CategoryRead], summary="更新分类"
)
async def update_category(
    category_id: uuid.UUID,
    category_update: CategoryUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """更新分类"""
    # 查找分类
    stmt = select(Category).where(
        (Category.id == category_id) & (Category.user_id == current_user.id)
    )
    result = await db.execute(stmt)
    category = result.scalar_one_or_none()

    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="分类不存在或无权限"
        )

    # 检查系统分类不允许修改
    if category.is_system:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="系统分类不允许修改"
        )

    update_data = category_update.dict(exclude_unset=True)

    # 如果要更新名称，检查同级分类名称是否重复
    if "name" in update_data and update_data["name"] != category.name:
        check_type = update_data.get("type", category.type)
        check_parent_id = update_data.get("parent_id", category.parent_id)

        conditions = [
            Category.user_id == current_user.id,
            Category.name == update_data["name"],
            Category.type == check_type,
            Category.parent_id == check_parent_id,
            Category.id != category_id,
        ]

        check_stmt = select(Category).where(and_(*conditions))
        existing_category = await db.execute(check_stmt)
        if existing_category.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="该分类名称在同级分类中已存在",
            )

    # 如果要更新父分类，进行验证
    if "parent_id" in update_data:
        new_parent_id = update_data["parent_id"]

        # 不能将分类设置为自己的子分类
        if new_parent_id == category_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="不能将分类设置为自己的父分类",
            )

        # 如果指定了新的父分类，验证父分类是否存在
        if new_parent_id:
            parent_stmt = select(Category).where(
                (Category.id == new_parent_id) & (Category.user_id == current_user.id)
            )
            parent_result = await db.execute(parent_stmt)
            parent_category = parent_result.scalar_one_or_none()
            if not parent_category:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="父分类不存在或无权限"
                )

            # 验证类型一致性
            check_type = update_data.get("type", category.type)
            if parent_category.type != check_type:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="子分类类型必须与父分类类型一致",
                )

            # 防止循环引用：检查新父分类不是当前分类的子分类
            async def is_descendant(
                parent_id: uuid.UUID, ancestor_id: uuid.UUID
            ) -> bool:
                check_stmt = select(Category).where(Category.id == parent_id)
                check_result = await db.execute(check_stmt)
                check_category = check_result.scalar_one_or_none()

                if not check_category or not check_category.parent_id:
                    return False

                if check_category.parent_id == ancestor_id:
                    return True

                return await is_descendant(check_category.parent_id, ancestor_id)

            if await is_descendant(new_parent_id, category_id):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="不能将分类设置为其子分类的父分类",
                )

    # 更新分类
    for field, value in update_data.items():
        setattr(category, field, value)

    await db.commit()
    await db.refresh(category)

    return ResponseModel(
        data=CategoryRead.model_validate(category), message="分类更新成功"
    )


@router.delete("/{category_id}", response_model=ResponseModel[dict], summary="删除分类")
async def delete_category(
    category_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """删除分类"""
    # 查找分类
    stmt = select(Category).where(
        (Category.id == category_id) & (Category.user_id == current_user.id)
    )
    result = await db.execute(stmt)
    category = result.scalar_one_or_none()

    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="分类不存在或无权限"
        )

    # 检查系统分类不允许删除
    if category.is_system:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="系统分类不允许删除"
        )

    # 检查是否有子分类
    children_stmt = select(Category).where(Category.parent_id == category_id)
    children_result = await db.execute(children_stmt)
    children = children_result.scalars().all()

    if children:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"该分类下还有{len(children)}个子分类，请先删除子分类",
        )

    # TODO: 检查是否有关联的账单
    # 这里需要导入Bill模型，暂时注释
    # from ...models.bill import Bill
    # bills_stmt = select(Bill).where(Bill.category_id == category_id)
    # bills_result = await db.execute(bills_stmt)
    # bills = bills_result.scalars().all()
    #
    # if bills:
    #     raise HTTPException(
    #         status_code=status.HTTP_400_BAD_REQUEST,
    #         detail=f"该分类下还有{len(bills)}个账单，请先删除或转移这些账单"
    #     )

    # 删除分类
    await db.delete(category)
    await db.commit()

    return ResponseModel(data={"id": str(category_id)}, message="分类删除成功")
