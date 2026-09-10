import os
from openpyxl import load_workbook
from openpyxl.utils import column_index_from_string, get_column_letter

# ====== 你的 31 个省份文件名（不带扩展名）======
PROVINCES = ['北京', '天津', '河北', '山西', '辽宁', '吉林', '黑龙江', '上海', '江苏', '浙江', '安徽', '福建', '江西', '山东', '河南', '湖北', '湖南', '广东', '广西', '海南', '重庆', '四川', '贵州', '云南', '陕西', '甘肃', '青海', '宁夏', '新疆', '内蒙古']

# ====== 路径与表名配置 ======
BASE_DIR = r"D:\BaiduNetdiskDownload\投入产出表\31省市区42部门投入产出表1997-2017年\2017年各省份投入产出表"
SRC_SHEET = "Sheet1"      # 你的源工作表
DST_SHEET = "A_matrix"    # 输出工作表

# ====== 数据区参数（按你前面说明）======
COL_START = "D"
COL_END   = "AS"          # 注意：这是中间投入块的最右列
ROW_START = 9
ROW_END   = 50
DENOM_ROW = 57

# ====== 列/行标题填充（名称来自 B9:B50；列标题覆盖 B1..AQ1 共 42 列）======
NAME_COL = "B"
NAME_ROW_START = 9
NAME_ROW_END   = 50
ROW_HEADER_COL = "A"
ROW_HEADER_START_ROW = 2
COL_HEADER_START_COL = "B"
COL_HEADER_END_COL   = "AQ"  # ★ 与 42 列宽匹配（B..AQ = 42 列）
COL_HEADER_ROW = 1

def build_A_from_block(file_path: str,
                       src_sheet: str,
                       dst_sheet: str = "A_matrix",
                       col_start: str = "D",
                       col_end: str = "AS",
                       row_start: int = 9,
                       row_end: int = 50,
                       denom_row: int = 57):
    """
    将 [col_start:col_end] × [row_start:row_end] 的中间投入矩阵按列除以 denom_row 的对应单元，
    结果写入同工作簿中新建的 sheet `dst_sheet`（若已存在则覆盖）。
    """
    wb = load_workbook(file_path, data_only=True)
    if src_sheet not in wb.sheetnames:
        raise ValueError(f"找不到源工作表: {src_sheet}")
    ws = wb[src_sheet]

    c0 = column_index_from_string(col_start)
    c1 = column_index_from_string(col_end)

    # 每列的分母（第 denom_row 行）
    denominators = {}
    for col in range(c0, c1 + 1):
        v = ws.cell(row=denom_row, column=col).value
        try:
            denominators[col] = float(v)
        except (TypeError, ValueError):
            denominators[col] = 0.0

    # 计算：逐列相除
    A = []
    for r in range(row_start, row_end + 1):
        row_vals = []
        for col in range(c0, c1 + 1):
            num = ws.cell(row=r, column=col).value
            try:
                num = float(num)
            except (TypeError, ValueError):
                num = 0.0
            den = denominators[col]
            val = (num / den) if (den not in (None, 0, 0.0)) else 0.0
            row_vals.append(val)
        A.append(row_vals)

    # 写入目标 Sheet（存在则删除重建）
    if dst_sheet in wb.sheetnames:
        del wb[dst_sheet]
    wdst = wb.create_sheet(dst_sheet)

    # 写标题：首列行号、首行列字母；数据从 B2 开始
    wdst.cell(row=1, column=1, value="row")
    for j, col in enumerate(range(c0, c1 + 1), start=2):
        wdst.cell(row=1, column=j, value=get_column_letter(col))
    for i, r in enumerate(range(row_start, row_end + 1), start=2):
        wdst.cell(row=i, column=1, value=r)
        for j, col in enumerate(range(c0, c1 + 1), start=2):
            wdst.cell(row=i, column=j, value=A[i-2][j-2])

    wb.save(file_path)

def apply_names_to_A_matrix(file_path: str,
                            src_sheet: str,
                            dst_sheet: str = "A_matrix",
                            name_col: str = "B",
                            name_row_start: int = 9,
                            name_row_end: int = 50,
                            row_header_col: str = "A",
                            row_header_start_row: int = 2,
                            col_header_start_col: str = "B",
                            col_header_end_col: str = "AQ",
                            col_header_row: int = 1):
    """
    将源表 name_col[name_row_start:name_row_end] 的行业名称写入 A_matrix：
    - 行名：A{row_header_start_row}:A{row_header_start_row+len-1}
    - 列名：{col_header_start_col}{col_header_row}:{col_header_end_col}{col_header_row}
    """
    wb = load_workbook(file_path)
    if src_sheet not in wb.sheetnames:
        raise ValueError(f"找不到源工作表：{src_sheet}")
    if dst_sheet not in wb.sheetnames:
        raise ValueError(f"找不到目标工作表：{dst_sheet}（请先生成 A_matrix）")

    ws_src = wb[src_sheet]
    ws_dst = wb[dst_sheet]

    # 读取名称列表
    names = []
    for r in range(name_row_start, name_row_end + 1):
        v = ws_src[f"{name_col}{r}"].value
        names.append("" if v is None else str(v).strip())

    # 列范围长度
    c0 = column_index_from_string(col_header_start_col)
    c1 = column_index_from_string(col_header_end_col)
    expected_len = c1 - c0 + 1
    if len(names) != expected_len:
        raise ValueError(
            f"名称数量（{len(names)}）与列数（{expected_len}，{col_header_start_col}..{col_header_end_col}）不一致。"
        )

    # 行名
    ws_dst[f"{row_header_col}1"].value = "sector"
    for i, nm in enumerate(names, start=row_header_start_row):
        ws_dst[f"{row_header_col}{i}"].value = nm

    # 列名
    for j, nm in enumerate(names, start=c0):
        ws_dst.cell(row=col_header_row, column=j, value=nm)

    wb.save(file_path)

def process_one(file_path: str,
                src_sheet: str = SRC_SHEET,
                dst_sheet: str = DST_SHEET):
    # 1) 生成 A_matrix（按列除以第 57 行）
    build_A_from_block(
        file_path=file_path,
        src_sheet=src_sheet,
        dst_sheet=dst_sheet,
        col_start=COL_START, col_end=COL_END,
        row_start=ROW_START, row_end=ROW_END, denom_row=DENOM_ROW
    )
    # 2) 写入行业名称（B9:B50 → 行列标题）
    apply_names_to_A_matrix(
        file_path=file_path,
        src_sheet=src_sheet,
        dst_sheet=dst_sheet,
        name_col=NAME_COL, name_row_start=NAME_ROW_START, name_row_end=NAME_ROW_END,
        row_header_col=ROW_HEADER_COL, row_header_start_row=ROW_HEADER_START_ROW,
        col_header_start_col=COL_HEADER_START_COL, col_header_end_col=COL_HEADER_END_COL, col_header_row=COL_HEADER_ROW
    )

# ========== 批量遍历：方案 A（文件名 = “省名.xlsx”）==========
ok, fail = [], []
for prov in PROVINCES:
    path = os.path.join(BASE_DIR, f"{prov}.xlsx")
    try:
        process_one(path, src_sheet=SRC_SHEET, dst_sheet=DST_SHEET)
        ok.append(prov)
        print(f"[OK] {prov}")
    except Exception as e:
        fail.append((prov, str(e)))
        print(f"[FAIL] {prov} -> {e}")

print("\n====== 完成 ======")
print("成功：", ok)
print("失败：", fail)

# ========== 如你的实际文件是 “01-北京.xlsx, 02-天津.xlsx, …” 用方案 B ==========
#ok, fail = [], []
#for idx, prov in enumerate(PROVINCES, start=1):
#     fn = f"{idx:02d}-{prov}.xlsx"
#     path = os.path.join(BASE_DIR, fn)
#     try:
#         process_one(path, src_sheet=SRC_SHEET, dst_sheet=DST_SHEET)
#         ok.append(fn)
#         print(f"[OK] {fn}")
#     except Exception as e:
#         fail.append((fn, str(e)))
#         print(f"[FAIL] {fn} -> {e}")
#print("\n====== 完成(编号文件名) ======")
#print("成功：", ok)
#print("失败：", fail)
