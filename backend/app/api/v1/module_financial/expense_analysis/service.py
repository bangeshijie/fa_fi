"""费用分析聚合服务。"""

from collections.abc import Iterable
from decimal import Decimal
from typing import Any

from sqlalchemy import func, select

from app.api.v1.module_budget.budget_detail.model import BudgetDetailModel
from app.api.v1.module_dimension.accounting_subject.model import AccountingSubjectModel
from app.api.v1.module_dimension.cost_center.model import CostCenterModel
from app.api.v1.module_dimension.subject_control_department_mapping.model import (
    SubjectControlDepartmentMappingModel,
)
from app.api.v1.module_financial.accounting_voucher_detail.model import (
    AccountingVoucherDetailModel,
)
from app.api.v1.module_system.auth.schema import AuthSchema
from app.api.v1.module_system.dept.model import DeptModel
from app.api.v1.module_system.dept.service import DeptService
from app.core.permission import Permission

from .schema import (
    EXPENSE_ANALYSIS_DATA_SOURCE_CATEGORIES,
    ExpenseAnalysisQuerySchema,
    ExpenseAnalysisResponseSchema,
)


ZERO = Decimal("0")


class ExpenseAnalysisService:
    """按部门、会计科目和主控部门生成费用分析结果。"""

    @classmethod
    async def get_department_options_service(cls, auth: AuthSchema) -> list[dict[str, Any]]:
        """获取费用分析可用的部门树。"""
        return await DeptService.get_dept_tree_service(
            auth=auth,
            order_by=[{"order": "asc"}],
        )

    @classmethod
    async def query_service(
        cls, auth: AuthSchema, query: ExpenseAnalysisQuerySchema
    ) -> dict[str, Any]:
        comparison_year = query.year - 1
        department_ids = await cls._expand_department_ids(auth, query.department_ids)
        department_lookup = await cls._get_department_lookup(auth)
        control_mapping_lookup = await cls._get_control_mapping_lookup(auth)

        actual_rows = await cls._aggregate_fact(
            auth=auth,
            query=query,
            model=AccountingVoucherDetailModel,
            department_ids=department_ids,
            is_actual=True,
            years=(query.year, comparison_year),
        )
        budget_rows = await cls._aggregate_fact(
            auth=auth,
            query=query,
            model=BudgetDetailModel,
            department_ids=department_ids,
            is_actual=False,
            years=(query.year, comparison_year),
        )
        cls._attach_control_mapping(
            rows=actual_rows,
            department_lookup=department_lookup,
            mapping_lookup=control_mapping_lookup,
        )
        cls._attach_control_mapping(
            rows=budget_rows,
            department_lookup=department_lookup,
            mapping_lookup=control_mapping_lookup,
        )

        department_data = cls._collect_metrics(
            actual_rows=actual_rows,
            budget_rows=budget_rows,
            dimension="department",
            current_year=query.year,
        )
        subject_data = cls._collect_metrics(
            actual_rows=actual_rows,
            budget_rows=budget_rows,
            dimension="subject",
            current_year=query.year,
        )
        control_department_data = cls._collect_metrics(
            actual_rows=actual_rows,
            budget_rows=budget_rows,
            dimension="control_department",
            current_year=query.year,
        )

        department_rows, department_total = cls._build_department_tree(
            department_data, department_lookup, query.month
        )
        subject_rows, subject_total = cls._build_subject_rows(subject_data, query.month)
        control_department_rows, control_department_total = (
            cls._build_control_department_rows(control_department_data, query.month)
        )

        result = {
            "currency": "RMB",
            "amount_unit": "元",
            "available_data_source_categories": list(
                EXPENSE_ANALYSIS_DATA_SOURCE_CATEGORIES
            ),
            "department": {"rows": department_rows, "total": department_total},
            "subject": {"rows": subject_rows, "total": subject_total},
            "control_department": {
                "rows": control_department_rows,
                "total": control_department_total,
            },
        }
        return ExpenseAnalysisResponseSchema.model_validate(result).model_dump()

    @classmethod
    async def _aggregate_fact(
        cls,
        auth: AuthSchema,
        query: ExpenseAnalysisQuerySchema,
        model: type[AccountingVoucherDetailModel] | type[BudgetDetailModel],
        department_ids: set[int] | None,
        is_actual: bool,
        years: tuple[int, int],
    ) -> list[dict[str, Any]]:
        dimension_columns = [
            model.year.label("year"),
            model.belonging_month.label("month"),
            AccountingSubjectModel.id.label("subject_id"),
            AccountingSubjectModel.code.label("subject_code"),
            AccountingSubjectModel.name.label("subject_name"),
            CostCenterModel.id.label("cost_center_id"),
            CostCenterModel.code.label("cost_center_code"),
            CostCenterModel.name.label("cost_center_name"),
            DeptModel.id.label("dept_id"),
            DeptModel.code.label("dept_code"),
            DeptModel.name.label("dept_name"),
            DeptModel.parent_id.label("dept_parent_id"),
        ]
        stmt = (
            select(*dimension_columns, func.coalesce(func.sum(model.amount), ZERO).label("amount"))
            .select_from(model)
            .join(
                AccountingSubjectModel,
                model.accounting_subject_id == AccountingSubjectModel.id,
            )
            .outerjoin(CostCenterModel, model.cost_center_id == CostCenterModel.id)
            .outerjoin(DeptModel, CostCenterModel.dept_id == DeptModel.id)
            .where(
                model.is_deleted.is_(False),
                model.year.in_(years),
                model.currency == "RMB",
            )
        )

        if is_actual:
            if query.data_source_categories:
                stmt = stmt.where(
                    model.data_source_category.in_(list(query.data_source_categories))
                )
        else:
            stmt = stmt.where(model.budget_version == query.budget_version)

        if query.company_ids:
            stmt = stmt.where(model.company_id.in_(query.company_ids))
        if department_ids is not None:
            stmt = stmt.where(DeptModel.id.in_(department_ids))
        if query.function_scopes:
            stmt = stmt.where(CostCenterModel.function_scope.in_(query.function_scopes))

        stmt = stmt.group_by(*dimension_columns)
        stmt = await Permission(model=model, auth=auth).filter_query(stmt)
        result = await auth.db.execute(stmt)
        return [dict(row) for row in result.mappings().all()]

    @classmethod
    async def _get_control_mapping_lookup(
        cls, auth: AuthSchema
    ) -> dict[tuple[int, int], tuple[str, str]]:
        result = await auth.db.execute(
            select(
                SubjectControlDepartmentMappingModel.accounting_subject_id,
                SubjectControlDepartmentMappingModel.dept_id,
                SubjectControlDepartmentMappingModel.control_department,
                SubjectControlDepartmentMappingModel.control_person,
            ).where(
                SubjectControlDepartmentMappingModel.status == "0",
                SubjectControlDepartmentMappingModel.is_deleted.is_(False),
            )
        )
        return {
            (int(row.accounting_subject_id), int(row.dept_id)): (
                str(row.control_department),
                str(row.control_person),
            )
            for row in result
        }

    @classmethod
    def _attach_control_mapping(
        cls,
        rows: list[dict[str, Any]],
        department_lookup: dict[int, dict[str, Any]],
        mapping_lookup: dict[tuple[int, int], tuple[str, str]],
    ) -> None:
        for row in rows:
            dept_id = row.get("dept_id")
            organization_id = cls._get_level_two_department_id(
                int(dept_id) if dept_id is not None else None,
                department_lookup,
            )
            mapped = (
                mapping_lookup.get((int(row["subject_id"]), organization_id))
                if organization_id is not None
                else None
            )
            row["control_department"], row["control_person"] = mapped or (
                "未配置主控部门",
                "未配置",
            )

    @staticmethod
    def _get_level_two_department_id(
        dept_id: int | None, department_lookup: dict[int, dict[str, Any]]
    ) -> int | None:
        """将实际部门归属到集团树的第二级组织（事业部）。"""
        if dept_id is None:
            return None
        current_id = dept_id
        visited: set[int] = set()
        while current_id not in visited:
            visited.add(current_id)
            current = department_lookup.get(current_id)
            if not current:
                return None
            parent_id = current.get("parent_id")
            if parent_id is None:
                return current_id
            parent = department_lookup.get(int(parent_id))
            if not parent or parent.get("parent_id") is None:
                return current_id
            current_id = int(parent_id)
        return current_id

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
    async def _get_department_lookup(cls, auth: AuthSchema) -> dict[int, dict[str, Any]]:
        result = await auth.db.execute(
            select(
                DeptModel.id,
                DeptModel.code,
                DeptModel.name,
                DeptModel.parent_id,
                DeptModel.order,
            ).order_by(DeptModel.order.asc(), DeptModel.id.asc())
        )
        return {int(row.id): dict(row._mapping) for row in result}

    @classmethod
    def _collect_metrics(
        cls,
        actual_rows: Iterable[dict[str, Any]],
        budget_rows: Iterable[dict[str, Any]],
        dimension: str,
        current_year: int,
    ) -> dict[tuple[Any, ...], dict[str, Any]]:
        data: dict[tuple[Any, ...], dict[str, Any]] = {}

        def add_rows(
            rows: Iterable[dict[str, Any]], field: str, prior_field: str
        ) -> None:
            for row in rows:
                if dimension == "department":
                    key = (int(row["dept_id"] or 0),)
                elif dimension == "control_department":
                    key = (
                        str(row["control_department"] or "未配置主控部门"),
                        str(row["control_person"] or "未配置"),
                        int(row["subject_id"] or 0),
                    )
                else:
                    key = (int(row["subject_id"]),)
                item = data.setdefault(
                    key,
                    {
                        "meta": row,
                        "actual_months": [ZERO for _ in range(12)],
                        "budget_months": [ZERO for _ in range(12)],
                        "prior_actual_months": [ZERO for _ in range(12)],
                        "prior_budget_months": [ZERO for _ in range(12)],
                    },
                )
                target_field = field if int(row["year"]) == current_year else prior_field
                item[target_field][int(row["month"]) - 1] += cls._decimal(row["amount"])

        add_rows(actual_rows, "actual_months", "prior_actual_months")
        add_rows(budget_rows, "budget_months", "prior_budget_months")
        return data

    @classmethod
    def _build_department_tree(
        cls,
        data: dict[tuple[Any, ...], dict[str, Any]],
        department_lookup: dict[int, dict[str, Any]],
        month: int,
    ) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        roots: list[dict[str, Any]] = []
        nodes: dict[str, dict[str, Any]] = {}

        def ensure_department(dept_id: int) -> dict[str, Any]:
            if dept_id == 0:
                node_id = "department:unassigned"
                if node_id not in nodes:
                    nodes[node_id] = cls._node(
                        id=node_id,
                        label="未分配部门",
                        code=None,
                        node_type="department",
                        level=1,
                    )
                    roots.append(nodes[node_id])
                return nodes[node_id]

            node_id = f"department:{dept_id}"
            if node_id in nodes:
                return nodes[node_id]
            info = department_lookup.get(dept_id, {})
            node = cls._node(
                id=node_id,
                label=str(info.get("name") or f"部门 {dept_id}"),
                code=info.get("code"),
                node_type="department",
                level=1,
            )
            nodes[node_id] = node
            parent_id = info.get("parent_id")
            if parent_id and int(parent_id) != dept_id:
                ensure_department(int(parent_id))["children"].append(node)
            else:
                roots.append(node)
            return node

        for key, item in data.items():
            dept_id = key[0]
            department = ensure_department(dept_id)
            cls._set_metrics(
                department,
                item["actual_months"],
                item["budget_months"],
                month,
                item["prior_actual_months"],
                item["prior_budget_months"],
            )

        for node in roots:
            cls._finalize_tree(node, month)
            cls._sort_tree(node)
        total = cls._total_node(roots, "department", month)
        return roots, total

    @classmethod
    def _build_subject_rows(
        cls, data: dict[tuple[Any, ...], dict[str, Any]], month: int
    ) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for key, item in data.items():
            meta = item["meta"]
            subject_row = cls._node(
                id=f"accounting-subject:{key[0]}",
                label=str(meta.get("subject_name") or "未命名科目"),
                code=meta.get("subject_code"),
                node_type="accounting_subject",
                level=1,
            )
            cls._set_metrics(
                subject_row,
                item["actual_months"],
                item["budget_months"],
                month,
                item["prior_actual_months"],
                item["prior_budget_months"],
            )
            rows.append(subject_row)

        rows.sort(key=lambda item: (item["label"], item.get("code") or ""))
        total = cls._total_node(rows, "accounting_subject", month)
        return rows, total

    @classmethod
    def _build_control_department_rows(
        cls,
        data: dict[tuple[Any, ...], dict[str, Any]],
        month: int,
    ) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        grouped: dict[tuple[str, str], dict[int, dict[str, Any]]] = {}
        for item in data.values():
            meta = item["meta"]
            control_key = (
                str(meta.get("control_department") or "未配置主控部门"),
                str(meta.get("control_person") or "未配置"),
            )
            subject_id = int(meta.get("subject_id") or 0)
            grouped.setdefault(control_key, {})[subject_id] = item

        rows: list[dict[str, Any]] = []
        for (control_department, control_person), subject_items in grouped.items():
            row = cls._node(
                id=f"control-department:{control_department}:{control_person}",
                label=control_department,
                code=None,
                node_type="control_department",
                level=1,
                control_person=control_person,
            )
            for subject_id, item in subject_items.items():
                meta = item["meta"]
                subject_row = cls._node(
                    id=f"control-department:{control_department}:{control_person}:subject:{subject_id}",
                    label=str(meta.get("subject_name") or "未命名科目"),
                    code=meta.get("subject_code"),
                    node_type="accounting_subject",
                    level=2,
                    control_person=control_person,
                )
                cls._set_metrics(
                    subject_row,
                    item["actual_months"],
                    item["budget_months"],
                    month,
                    item["prior_actual_months"],
                    item["prior_budget_months"],
                )
                row["children"].append(subject_row)
            cls._finalize_tree(row, month)
            cls._sort_tree(row)
            rows.append(row)

        rows.sort(key=lambda item: (item["label"], item.get("control_person") or ""))
        total = cls._total_node(rows, "control_department", month)
        return rows, total

    @classmethod
    def _node(
        cls,
        id: str,
        label: str,
        code: str | None,
        node_type: str,
        level: int,
        control_person: str | None = None,
    ) -> dict[str, Any]:
        return {
            "id": id,
            "label": label,
            "code": code,
            "node_type": node_type,
            "level": level,
            "control_person": control_person,
            "children": [],
        }

    @classmethod
    def _set_metrics(
        cls,
        node: dict[str, Any],
        actual_months: list[Decimal],
        budget_months: list[Decimal],
        month: int,
        prior_actual_months: list[Decimal],
        prior_budget_months: list[Decimal],
    ) -> None:
        node.update(
            cls._metric_fields(
                actual_months,
                budget_months,
                month,
                prior_actual_months,
                prior_budget_months,
            )
        )

    @classmethod
    def _finalize_tree(cls, node: dict[str, Any], month: int) -> None:
        children = node["children"]
        if not children:
            return
        own_actual_months = node.get("actual_months", [ZERO for _ in range(12)])
        own_budget_months = node.get("budget_months", [ZERO for _ in range(12)])
        own_prior_actual_months = node.get(
            "prior_actual_months", [ZERO for _ in range(12)]
        )
        own_prior_budget_months = node.get(
            "prior_budget_months", [ZERO for _ in range(12)]
        )
        for child in children:
            cls._finalize_tree(child, month)
        actual_months = [
            own_actual_months[index]
            + sum((child["actual_months"][index] for child in children), ZERO)
            for index in range(12)
        ]
        budget_months = [
            own_budget_months[index]
            + sum((child["budget_months"][index] for child in children), ZERO)
            for index in range(12)
        ]
        prior_actual_months = [
            own_prior_actual_months[index]
            + sum((child["prior_actual_months"][index] for child in children), ZERO)
            for index in range(12)
        ]
        prior_budget_months = [
            own_prior_budget_months[index]
            + sum((child["prior_budget_months"][index] for child in children), ZERO)
            for index in range(12)
        ]
        node.update(
            cls._metric_fields(
                actual_months,
                budget_months,
                month,
                prior_actual_months,
                prior_budget_months,
            )
        )

    @classmethod
    def _sort_tree(cls, node: dict[str, Any]) -> None:
        node["children"].sort(key=lambda item: (item["node_type"] == "accounting_subject", item["label"]))
        for child in node["children"]:
            cls._sort_tree(child)

    @classmethod
    def _total_node(
        cls, roots: list[dict[str, Any]], node_type: str, month: int
    ) -> dict[str, Any]:
        actual_months = [
            sum((node["actual_months"][index] for node in roots), ZERO)
            for index in range(12)
        ]
        budget_months = [
            sum((node["budget_months"][index] for node in roots), ZERO)
            for index in range(12)
        ]
        prior_actual_months = [
            sum((node["prior_actual_months"][index] for node in roots), ZERO)
            for index in range(12)
        ]
        prior_budget_months = [
            sum((node["prior_budget_months"][index] for node in roots), ZERO)
            for index in range(12)
        ]
        node = cls._node("total", "合计", None, node_type, 0)
        node.update(
            cls._metric_fields(
                actual_months,
                budget_months,
                month,
                prior_actual_months,
                prior_budget_months,
            )
        )
        return node

    @classmethod
    def _metric_fields(
        cls,
        actual_months: list[Decimal],
        budget_months: list[Decimal],
        month: int,
        prior_actual_months: list[Decimal],
        prior_budget_months: list[Decimal],
    ) -> dict[str, Any]:
        current_actual = actual_months[month - 1]
        current_budget = budget_months[month - 1]
        ytd_actual = sum(actual_months[:month], ZERO)
        ytd_budget = sum(budget_months[:month], ZERO)
        prior_current_actual = prior_actual_months[month - 1]
        prior_current_budget = prior_budget_months[month - 1]
        prior_ytd_actual = sum(prior_actual_months[:month], ZERO)
        prior_ytd_budget = sum(prior_budget_months[:month], ZERO)
        annual_budget = sum(budget_months, ZERO)
        return {
            "actual_months": actual_months,
            "budget_months": budget_months,
            "prior_actual_months": prior_actual_months,
            "prior_budget_months": prior_budget_months,
            "current_actual": current_actual,
            "current_budget": current_budget,
            "current_variance": current_actual - current_budget,
            "current_completion_rate": cls._rate(current_actual, current_budget),
            "prior_year_current_completion_rate": cls._rate(
                prior_current_actual, prior_current_budget
            ),
            "ytd_actual": ytd_actual,
            "ytd_budget": ytd_budget,
            "ytd_variance": ytd_actual - ytd_budget,
            "ytd_completion_rate": cls._rate(ytd_actual, ytd_budget),
            "prior_year_ytd_completion_rate": cls._rate(
                prior_ytd_actual, prior_ytd_budget
            ),
            "annual_budget": annual_budget,
            "annual_completion_rate": cls._rate(ytd_actual, annual_budget),
        }

    @staticmethod
    def _rate(numerator: Decimal, denominator: Decimal) -> Decimal | None:
        if denominator == ZERO:
            return None
        return numerator / denominator

    @staticmethod
    def _decimal(value: Any) -> Decimal:
        if isinstance(value, Decimal):
            return value
        return Decimal(str(value or 0))
