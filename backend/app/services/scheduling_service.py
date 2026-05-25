from ..algorithm import ORToolsScheduler
from ..models.schemas import SchedulingParams, AlgorithmConfig, SchedulingResult
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, Border, Side, PatternFill
from io import BytesIO


class SchedulingService:
    @staticmethod
    def calculate(params: SchedulingParams, config: AlgorithmConfig, holidays: list = None) -> dict:
        holiday_list = holidays or []
        scheduler = ORToolsScheduler(
            initial_inventory=params.initial_inventory,
            safety_stock=params.safety_stock,
            rated_output=params.rated_output,
            total_delivery=params.total_delivery,
            start_date=params.start_date,
            end_date=params.end_date,
            holidays=holiday_list,
            daily_deliveries=params.daily_deliveries,
            max_time_seconds=config.max_time_seconds,
            overtime_shift_weight=config.overtime_shift_weight,
            overtime_day_weight=config.overtime_day_weight,
            rest_day_weight=config.rest_day_weight,
            max_consecutive_work_days=config.max_consecutive_work_days,
        )
        result = scheduler.run()
        return result

    @staticmethod
    def export_excel(result: dict) -> BytesIO:
        wb = Workbook()
        ws = wb.active
        ws.title = "排产计划"

        header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
        header_font_white = Font(bold=True, size=11, color="FFFFFF")
        thin_border = Border(
            left=Side(style="thin"),
            right=Side(style="thin"),
            top=Side(style="thin"),
            bottom=Side(style="thin"),
        )
        center_align = Alignment(horizontal="center", vertical="center")

        ws.merge_cells("A1:H1")
        title_cell = ws["A1"]
        title_cell.value = "智能排产计划"
        title_cell.font = Font(bold=True, size=16)
        title_cell.alignment = center_align

        headers = ["日期", "休息日", "调休上班", "班次", "工时(h)", "当日产量", "当日交货量", "结存库存", "库存异常"]
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=3, column=col, value=header)
            cell.font = header_font_white
            cell.fill = header_fill
            cell.border = thin_border
            cell.alignment = center_align

        for row_idx, dr in enumerate(result["daily_results"], 4):
            date_str = str(dr["date"])
            shift_label = dr.get("shift_label", f"{dr['shift']}班" if dr['shift'] > 0 else "休息")
            rest_label = ""
            if dr.get("is_holiday"):
                rest_label = "法定假"
            elif dr.get("is_rest"):
                rest_label = "周末"
            values = [
                date_str,
                rest_label,
                "是" if dr.get("is_adjusted_workday") else "",
                shift_label,
                dr["work_hours"],
                dr["daily_output"],
                dr["daily_delivery"],
                dr["closing_inventory"],
                "⚠" if dr["inventory_violation"] else "",
            ]
            for col, val in enumerate(values, 1):
                cell = ws.cell(row=row_idx, column=col, value=val)
                cell.border = thin_border
                cell.alignment = center_align
                if dr.get("is_rest"):
                    cell.fill = PatternFill(start_color="FFF2CC", end_color="FFF2CC", fill_type="solid")
                if dr["inventory_violation"]:
                    cell.fill = PatternFill(start_color="FCE4EC", end_color="FCE4EC", fill_type="solid")

        summary_row = len(result["daily_results"]) + 5
        ws.cell(row=summary_row, column=1, value="方案统计").font = Font(bold=True, size=12)
        summary_data = [
            ("总生产天数", result["total_production_days"]),
            ("加班天数(1.5班)", result["overtime_days"]),
            ("休息日生产天数", result["holiday_production_days"]),
            ("库存最小值", result["min_inventory"]),
            ("最终结存库存", result.get("final_inventory", "")),
            ("交货达标", "是" if result["delivery_fulfilled"] else "否"),
        ]
        for i, (label, value) in enumerate(summary_data):
            ws.cell(row=summary_row + 1 + i, column=1, value=label).font = Font(bold=True)
            ws.cell(row=summary_row + 1 + i, column=2, value=value)

        col_widths = [14, 8, 8, 14, 10, 12, 12, 12, 10]
        for i, width in enumerate(col_widths, 1):
            ws.column_dimensions[chr(64 + i)].width = width

        buffer = BytesIO()
        wb.save(buffer)
        buffer.seek(0)
        return buffer
