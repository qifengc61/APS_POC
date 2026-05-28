from io import BytesIO
from datetime import date
from openpyxl import load_workbook
from openpyxl.styles import Font, PatternFill, Border, Side, Alignment
from ..models.schemas import SchedulingParams, ProductParams, AlgorithmConfig
from ..algorithm.scheduler import TwoProductScheduler


def _clear_cell(cell):
    cell.value = None
    cell.font = Font()
    cell.fill = PatternFill(fill_type=None)
    cell.border = Border()
    cell.alignment = Alignment()
    cell.number_format = "General"


TEMPLATE_PATH = r"d:\Desktop\智能排产\智能排产POC\导出模板.xlsx"

TEMPLATE_BORDER = Border(
    left=Side(style="thin"),
    right=Side(style="thin"),
    top=Side(style="thin"),
    bottom=Side(style="thin"),
)
TEMPLATE_FONT = Font(name="宋体", size=9)
TEMPLATE_ALIGNMENT = Alignment(horizontal="center", vertical="center")

WEEKDAYS = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]

# 模板各行背景色（用于动态列保持一致）
ROW_FILLS = {
    4: PatternFill(start_color="FFCCFFFF", end_color="FFCCFFFF", fill_type="solid"),
    5: PatternFill(start_color="FFCCFFFF", end_color="FFCCFFFF", fill_type="solid"),
    8: PatternFill(start_color="FFBFBFBF", end_color="FFBFBFBF", fill_type="solid"),
    9: PatternFill(start_color="FFCCFFFF", end_color="FFCCFFFF", fill_type="solid"),
    10: PatternFill(start_color="FFCCFFFF", end_color="FFCCFFFF", fill_type="solid"),
    13: PatternFill(start_color="FFBFBFBF", end_color="FFBFBFBF", fill_type="solid"),
}


class SchedulingService:
    @staticmethod
    def calculate(params: SchedulingParams, config: AlgorithmConfig, holidays: list = None) -> dict:
        holiday_list = holidays or []
        scheduler = TwoProductScheduler(
            product_1=params.product_1,
            product_2=params.product_2,
            start_date=params.start_date,
            end_date=params.end_date,
            holidays=holiday_list,
            max_time_seconds=config.max_time_seconds,
            rest_day_weight=config.rest_day_weight,
            max_consecutive_work_days=config.max_consecutive_work_days,
        )
        result = scheduler.run()
        return result

    @staticmethod
    def export_excel(result: dict, plan_info: dict = None) -> BytesIO:
        wb = load_workbook(TEMPLATE_PATH)
        ws = wb.active

        for sheet in wb.worksheets:
            if hasattr(sheet, '_comments') and sheet._comments:
                sheet._comments = []
            for row in sheet.iter_rows():
                for cell in row:
                    if cell.comment:
                        cell.comment = None

        daily_results = result.get("daily_results", [])
        num_days = len(daily_results)
        if num_days == 0:
            buffer = BytesIO()
            wb.save(buffer)
            buffer.seek(0)
            return buffer

        p1 = (plan_info or {}).get("product_1") or {}
        p2 = (plan_info or {}).get("product_2") or {}

        ws.cell(row=4, column=2, value=p1.get("code", ""))
        ws.cell(row=4, column=3, value=p1.get("name", ""))
        ws.cell(row=4, column=4, value=p1.get("initial_inventory", 0))
        ws.cell(row=4, column=5, value=p1.get("safety_stock", 0))
        ws.cell(row=4, column=7, value=p1.get("rated_output", 0))
        total_delivery_1 = p1.get("total_delivery", 0)
        ws.cell(row=7, column=9, value=total_delivery_1)

        ws.cell(row=9, column=2, value=p2.get("code", ""))
        ws.cell(row=9, column=3, value=p2.get("name", ""))
        ws.cell(row=9, column=4, value=p2.get("initial_inventory", 0))
        ws.cell(row=9, column=5, value=p2.get("safety_stock", 0))
        ws.cell(row=9, column=7, value=p2.get("rated_output", 0))
        total_delivery_2 = p2.get("total_delivery", 0)
        ws.cell(row=12, column=9, value=total_delivery_2)

        safety_1 = p1.get("safety_stock", 0)
        init_inv_1 = p1.get("initial_inventory", 0)
        net_demand_1 = total_delivery_1 + safety_1 - init_inv_1
        ws.cell(row=4, column=6, value=net_demand_1)

        safety_2 = p2.get("safety_stock", 0)
        init_inv_2 = p2.get("initial_inventory", 0)
        net_demand_2 = total_delivery_2 + safety_2 - init_inv_2
        ws.cell(row=9, column=6, value=net_demand_2)

        ws.cell(row=4, column=1, value=1)
        ws.cell(row=9, column=1, value=2)

        # ── 清空 J 列之后的所有旧内容（含合并单元格），实现动态天数 ──
        start_col = 10
        for merge_range in list(ws.merged_cells.ranges):
            if merge_range.min_col >= start_col:
                ws.unmerge_cells(str(merge_range))

        for r in range(1, ws.max_row + 1):
            for c in range(start_col, ws.max_column + 1):
                cell = ws.cell(row=r, column=c)
                cell.value = None
                cell.fill = PatternFill(fill_type=None)

        # ── 动态写入每日排产明细 ──
        days_to_write = num_days
        end_col = start_col + days_to_write - 1
        bg_col = end_col + 1

        ab_rows = {4, 5, 9, 10}

        sum_1a = 0
        sum_1b = 0
        sum_1_prod = 0
        sum_2a = 0
        sum_2b = 0
        sum_2_prod = 0
        sum_shift1_1 = 0.0
        sum_shift2_1 = 0.0
        sum_shift1_2 = 0.0
        sum_shift2_2 = 0.0

        for i in range(days_to_write):
            col = start_col + i
            dr = daily_results[i]

            d = dr.get("date", "")
            if d:
                dt = date.fromisoformat(d) if isinstance(d, str) else d
                ws.cell(row=2, column=col, value=dt)
                ws.cell(row=2, column=col).font = TEMPLATE_FONT
                ws.cell(row=2, column=col).border = TEMPLATE_BORDER
                ws.cell(row=2, column=col).alignment = TEMPLATE_ALIGNMENT
                ws.cell(row=2, column=col).number_format = "m/d"
                ws.cell(row=3, column=col, value=WEEKDAYS[dt.weekday()])
                ws.cell(row=3, column=col).font = TEMPLATE_FONT
                ws.cell(row=3, column=col).border = TEMPLATE_BORDER
                ws.cell(row=3, column=col).alignment = TEMPLATE_ALIGNMENT

            is_rest_day = dr.get("is_rest", False)
            if is_rest_day:
                pink_fill = PatternFill(start_color="FFE0E0", end_color="FFE0E0", fill_type="solid")
                ws.cell(row=2, column=col).fill = pink_fill
                ws.cell(row=3, column=col).fill = pink_fill

            prod1_1 = dr.get("prod1_1", 0)
            prod2_1 = dr.get("prod2_1", 0)
            output_1 = dr.get("daily_output_1", 0)
            delivery_1 = dr.get("daily_delivery_1", 0)
            inv_1 = dr.get("closing_inventory_1", 0)

            prod1_2 = dr.get("prod1_2", 0)
            prod2_2 = dr.get("prod2_2", 0)
            output_2 = dr.get("daily_output_2", 0)
            delivery_2 = dr.get("daily_delivery_2", 0)
            inv_2 = dr.get("closing_inventory_2", 0)

            shift1_1 = dr.get("shift1_1", 0)
            shift2_1 = dr.get("shift2_1", 0)
            shift1_2 = dr.get("shift1_2", 0)
            shift2_2 = dr.get("shift2_2", 0)

            day_data = [
                (4, prod1_1), (5, prod2_1),
                (6, output_1), (7, delivery_1), (8, inv_1),
                (9, prod1_2), (10, prod2_2),
                (11, output_2), (12, delivery_2), (13, inv_2),
            ]
            for row, val in day_data:
                cell = ws.cell(row=row, column=col)
                if row in ROW_FILLS:
                    cell.fill = ROW_FILLS[row]
                cell.font = TEMPLATE_FONT
                cell.border = TEMPLATE_BORDER
                cell.alignment = TEMPLATE_ALIGNMENT
                if row in ab_rows and val == 0:
                    cell.value = None
                else:
                    cell.value = val

            sum_1a += prod1_1
            sum_1b += prod2_1
            sum_1_prod += output_1
            sum_2a += prod1_2
            sum_2b += prod2_2
            sum_2_prod += output_2
            sum_shift1_1 += shift1_1
            sum_shift2_1 += shift2_1
            sum_shift1_2 += shift1_2
            sum_shift2_2 += shift2_2

        # ── 合计列（I 列 = 第 9 列，模板固定） ──
        total_data = [
            (4, sum_1a), (5, sum_1b),
            (6, sum_1_prod),
            (9, sum_2a), (10, sum_2b),
            (11, sum_2_prod),
        ]
        for row, val in total_data:
            if row in ab_rows and val == 0:
                ws.cell(row=row, column=9, value=None)
            else:
                ws.cell(row=row, column=9, value=val)

        # ── 班次合计列（紧贴最后一天之后） ──
        ws.cell(row=1, column=bg_col).value = None
        ws.cell(row=2, column=bg_col).border = TEMPLATE_BORDER
        ws.cell(row=3, column=bg_col).border = TEMPLATE_BORDER
        ws.merge_cells(start_row=2, start_column=bg_col, end_row=3, end_column=bg_col)
        ws.cell(row=2, column=bg_col, value="班次")
        ws.cell(row=2, column=bg_col).font = Font(name="宋体", size=9, bold=True)
        ws.cell(row=2, column=bg_col).alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

        for row in range(4, 14):
            cell = ws.cell(row=row, column=bg_col)
            cell.fill = PatternFill(fill_type=None)
            cell.font = TEMPLATE_FONT
            cell.border = TEMPLATE_BORDER
            cell.alignment = TEMPLATE_ALIGNMENT

        bg_data = [
            (4, sum_shift1_1),
            (5, sum_shift2_1),
            (6, sum_shift1_1 + sum_shift2_1),
            (9, sum_shift1_2),
            (10, sum_shift2_2),
            (11, sum_shift1_2 + sum_shift2_2),
        ]
        for row, val in bg_data:
            cell = ws.cell(row=row, column=bg_col)
            if row in ab_rows and val == 0:
                cell.value = None
            else:
                cell.value = val

        # ── 周数合并行（第 1 行） ──
        first_date_str = daily_results[0]["date"]
        first_date = date.fromisoformat(first_date_str) if isinstance(first_date_str, str) else None
        if first_date:
            ws.cell(row=3, column=4, value=f"{first_date.month}/{first_date.day}")
            ws.cell(row=3, column=4).font = Font(name="宋体", size=9, color="666666")

        for week_start in range(0, days_to_write, 7):
            ws_col = start_col + week_start
            ws_end = min(ws_col + 6, end_col)
            ws.merge_cells(start_row=1, start_column=ws_col, end_row=1, end_column=ws_end)
            if first_date:
                cur_date = date.fromordinal(first_date.toordinal() + week_start)
                ws.cell(row=1, column=ws_col, value=f"{cur_date.isocalendar()[1]}周")
            ws.cell(row=1, column=ws_col).font = TEMPLATE_FONT
            ws.cell(row=1, column=ws_col).border = TEMPLATE_BORDER
            ws.cell(row=1, column=ws_col).alignment = TEMPLATE_ALIGNMENT

        ws["A4"].font = Font(name="宋体", size=9)
        ws["A9"].font = Font(name="宋体", size=9)

        # ── 清除实际使用范围之外的残留格式（边框/背景等） ──
        max_used_row = 13
        max_used_col = bg_col
        for r in range(1, ws.max_row + 1):
            for c in range(1, ws.max_column + 1):
                if r > max_used_row or c > max_used_col:
                    _clear_cell(ws.cell(row=r, column=c))

        buffer = BytesIO()
        wb.save(buffer)
        buffer.seek(0)
        return buffer