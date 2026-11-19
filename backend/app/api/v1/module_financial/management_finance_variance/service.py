"""管报与财报差异分析聚合服务。"""

import json
from collections.abc import Iterable
from decimal import Decimal
from typing import Any

from sqlalchemy import and_, case, false, func, or_, select

from app.api.v1.module_dimension.accounting_subject.model import AccountingSubjectModel
from app.api.v1.module_dimension.cost_center.model import CostCenterModel
from app.api.v1.module_financial.accounting_voucher_detail.model import (
    AccountingVoucherDetailModel,
)
from app.api.v1.module_system.auth.schema import AuthSchema
from app.api.v1.module_system.dept.model import DeptModel
from app.api.v1.module_system.dept.service import DeptService
from app.core.permission import Permission

from .schema import (
    MANAGEMENT_FINANCE_DATA_SOURCE_CATEGORIES,
    ManagementFinanceVarianceQuerySchema,
    ManagementFinanceVarianceResponseSchema,
)


ZERO = Decimal("0")


class ManagementFinanceVarianceService:
    """按管理分类和会计科目生成管报、财报及差额。"""

    SUBJECT_CATEGORY_FIELDS = (
        AccountingSubjectModel.management_category_level1,
        AccountingSubjectModel.management_category_level2,
        AccountingSubjectModel.management_category_level3,
    )

    @classmethod
    async def get_department_options_service(cls, auth: AuthSchema) -> list[dict[str, Any]]:
        """获取差异分析可用的部门树。"""
        return await DeptService.get_dept_tree_service(
            auth=auth,
            order_by=[{"order": "asc"}],
        )

    @classmethod
    async def query_service(
        cls, auth: AuthSchema, query: ManagementFinanceVarianceQuerySchema
    ) -> dict[str, Any]:
        department_ids = await cls._expand_department_ids(auth, query.department_ids)
        rows = await cls._aggregate_fact(auth=auth, query=query, department_ids=department_ids)
        data = cls._collect_metrics(rows)
        subject_rows, subject_total = cls._build_subject_tree(data, query.month)

        result = {
            "currency": "RMB",
            "amount_unit": "元",
            "available_data_source_categories": list(
                MANAGEMENT_FINANCE_DATA_SOURCE_CATEGORIES
            ),
            "subject": {"rows": subject_rows, "total": subject_total},
        }
        return ManagementFinanceVarianceResponseSchema.model_validate(result).model_dump()

    @classmethod
    async def _aggregate_fact(
        cls,
        auth: AuthSchema,
        query: ManagementFinanceVarianceQuerySchema,
        department_ids: set[int] | None,
    ) -> list[dict[str, Any]]:
        model = AccountingVoucherDetailModel
        dimension_columns = [
            model.belonging_month.label("month"),
            AccountingSubjectModel.id.label("subject_id"),
            AccountingSubjectModel.code.label("subject_code"),
            AccountingSubjectModel.name.label("subject_name"),
            AccountingSubjectModel.management_category_level1.label("category_level1"),
            AccountingSubjectModel.management_category_level2.label("category_level2"),
            AccountingSubjectModel.management_category_level3.label("category_level3"),
        ]

        management_amount = cls._sum_for_categories(
            model, query.management_data_source_categories
        ).label("management_amount")
        financial_amount = cls._sum_for_categories(
            model, query.financial_data_source_categories
        ).label("financial_amount")
        stmt = (
            select(*dimension_columns, management_amount, financial_amount)
            .select_from(model)
            .join(
                AccountingSubjectModel,
                model.accounting_subject_id == AccountingSubjectModel.id,
            )
            .outerjoin(CostCenterModel, model.cost_center_id == CostCenterModel.id)
            .outerjoin(DeptModel, CostCenterModel.dept_id == DeptModel.id)
            .where(
                model.is_deleted.is_(False),
                model.year == query.year,
                model.currency == "RMB",
            )
        )

        if query.company_ids:
            stmt = stmt.where(model.company_id.in_(query.company_ids))
        if department_ids is not None:
            stmt = stmt.where(DeptModel.id.in_(department_ids))
        if query.function_scopes:
            stmt = stmt.where(CostCenterModel.function_scope.in_(query.function_scopes))

        category_condition = cls._category_condition(query.management_category_paths)
        if category_condition is not None:
            stmt = stmt.where(category_condition)

        stmt = stmt.group_by(*dimension_columns)
        stmt = await Permission(model=model, auth=auth).filter_query(stmt)
        result = await auth.db.execute(stmt)
        return [dict(row) for row in result.mappings().all()]

    @staticmethod
    def _sum_for_categories(model: type[AccountingVoucherDetailModel], categories: list[str]) -> Any:
        if not categories:
            return func.coalesce(func.sum(model.amount), ZERO)
        return func.coalesce(
            func.sum(
                case(
                    (model.data_source_category.in_(categories), model.amount),
                    else_=ZERO,
                )
            ),
            ZERO,
        )

    @classmethod
    def _category_condition(cls, paths: list[list[str]]) -> Any:
        if not paths:
            return None
        conditions = []
        for path in paths:
            if not 1 <= len(path) <= len(cls.SUBJECT_CATEGORY_FIELDS):
                continue
            conditions.append(
                and_(*[field == value for field, value in zip(cls.SUBJECT_CATEGORY_FIELDS, path)])
            )
        return or_(*conditions) if conditions else false()

    @classmethod
    async def _expand_department_ids(
        cls, auth: AuthSchema, selected_ids: list[int]
    ) -> set[int] | None:
        if not selected_ids:
            return None
        result = await auth.db.execute(select(DeptModel.id, DeptModel.parent_id))
        parent_map = {int(row.id): row.parent_id for row in result}
        children_map: dict[int, set[int]] = {}
        for dept_id, parent_id in parent_map.items():
            if parent_id is not None:
                children_map.setdefault(int(parent_id), set()).add(dept_id)

        expanded = {item for item in selected_ids if item in parent_map}
        pending = list(expanded)
        while pending:
            current = pending.pop()
            for child_id in children_map.get(current, set()):
                if child_id not in expanded:
                    expanded.add(child_id)
                    pending.append(child_id)
        return expanded or set(selected_ids)

    @classmethod
    def _collect_metrics(cls, rows: Iterable[dict[str, Any]]) -> dict[int, dict[str, Any]]:
        data: dict[int, dict[str, Any]] = {}
        for row in rows:
            subject_id = int(row["subject_id"])
            item = data.setdefault(
                subject_id,
                {
                    "meta": row,
                    "management_months": [ZERO for _ in range(12)],
                    "financial_months": [ZERO for _ in range(12)],
                },
            )
            index = int(row["month"]) - 1
            item["management_months"][index] += cls._decimal(row["management_amount"])
            item["financial_months"][index] += cls._decimal(row["financial_amount"])
        return data

    @classmethod
    def _build_subject_tree(
        cls, data: dict[int, dict[str, Any]], month: int
    ) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        roots: list[dict[str, Any]] = []
        nodes: dict[tuple[str, ...], dict[str, Any]] = {}

        def ensure_category(path: list[str]) -> dict[str, Any]:
            parent: dict[str, Any] | None = None
            for index, label in enumerate(path, start=1):
                key = tuple(path[:index])
                node = nodes.get(key)
                if node is None:
                    node = cls._node(
                        id=f"category:{json.dumps(key, ensure_ascii=False)}",
                        label=label,
                        code=None,
                        node_type="category",
                        level=index,
                    )
                    nodes[key] = node
                    if parent is None:
                        roots.append(node)
                    else:
                        parent["children"].append(node)
                parent = node
            assert parent is not None
            return parent

        for subject_id, item in data.items():
            meta = item["meta"]
            path = [
                str(meta.get("category_level1") or "未分类"),
                str(meta.get("category_level2") or "未分类"),
                str(meta.get("category_level3") or "未分类"),
            ]
            parent = ensure_category(path)
            subject_node = cls._node(
                id=f"accounting-subject:{subject_id}",
                label=str(meta.get("subject_name") or "未命名科目"),
                code=meta.get("subject_code"),
                node_type="accounting_subject",
                level=4,
            )
            subject_node.update(
                cls._metric_fields(
                    item["management_months"], item["financial_months"], month
                )
            )
            parent["children"].append(subject_node)

        for node in roots:
            cls._finalize_tree(node, month)
            cls._sort_tree(node)
        return roots, cls._total_node(roots, month)

    @staticmethod
    def _node(
        id: str, label: str, code: str | None, node_type: str, level: int
    ) -> dict[str, Any]:
        return {
            "id": id,
            "label": label,
            "code": code,
            "node_type": node_type,
            "level": level,
            "children": [],
        }

    @classmethod
    def _finalize_tree(cls, node: dict[str, Any], month: int) -> None:
        children = node["children"]
        if not children:
            return
        for child in children:
            cls._finalize_tree(child, month)
        management_months = [
            sum((child["management_months"][index] for child in children), ZERO)
            for index in range(12)
        ]
        financial_months = [
            sum((child["financial_months"][index] for child in children), ZERO)
            for index in range(12)
        ]
        node.update(cls._metric_fields(management_months, financial_months, month))

    @staticmethod
    def _sort_tree(node: dict[str, Any]) -> None:
        node["children"].sort(
            key=lambda item: (item["node_type"] == "accounting_subject", item["label"])
        )
        for child in node["children"]:
            ManagementFinanceVarianceService._sort_tree(child)

    @classmethod
    def _total_node(cls, roots: list[dict[str, Any]], month: int) -> dict[str, Any]:
        management_months = [
            sum((node["management_months"][index] for node in roots), ZERO)
            for index in range(12)
        ]
        financial_months = [
            sum((node["financial_months"][index] for node in roots), ZERO)
            for index in range(12)
        ]
        node = cls._node("total", "合计", None, "category", 0)
        node.update(cls._metric_fields(management_months, financial_months, month))
        return node

    @staticmethod
    def _metric_fields(
        management_months: list[Decimal], financial_months: list[Decimal], month: int
    ) -> dict[str, Any]:
        current_index = month - 1
        current_management = management_months[current_index]
        current_financial = financial_months[current_index]
        ytd_management = sum(management_months[:month], ZERO)
        ytd_financial = sum(financial_months[:month], ZERO)
        return {
            "management_months": management_months,
            "financial_months": financial_months,
            "current_management_report": current_management,
            "current_financial_report": current_financial,
            "current_variance": current_management - current_financial,
            "ytd_management_report": ytd_management,
            "ytd_financial_report": ytd_financial,
            "ytd_variance": ytd_management - ytd_financial,
        }

    @staticmethod
    def _decimal(value: Any) -> Decimal:
        if isinstance(value, Decimal):
            return value
        return Decimal(str(value or 0))
