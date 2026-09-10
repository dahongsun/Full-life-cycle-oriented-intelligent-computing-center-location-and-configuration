from openpyxl import load_workbook
from openpyxl.utils import column_index_from_string, get_column_letter

def build_A_from_block(
    file_path: str,
    src_sheet: str,
    dst_sheet: str = "A_matrix",
    col_start: str = "D",
    col_end: str = "AS",
    row_start: int = 9,
    row_end: int = 50,
    denom_row: int = 57,
):
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

    # 写入目标 Sheet
    if dst_sheet in wb.sheetnames:
        del wb[dst_sheet]
    wdst = wb.create_sheet(dst_sheet)

    # 可读的标题（首行列字母、首列原行号），数据从 B2 开始
    wdst.cell(row=1, column=1, value="row")
    for j, col in enumerate(range(c0, c1 + 1), start=2):
        wdst.cell(row=1, column=j, value=get_column_letter(col))
    for i, r in enumerate(range(row_start, row_end + 1), start=2):
        wdst.cell(row=i, column=1, value=r)
        for j, col in enumerate(range(c0, c1 + 1), start=2):
            wdst.cell(row=i, column=j, value=A[i-2][j-2])

    wb.save(file_path)
    print(f"完成：在《{file_path}》生成 Sheet《{dst_sheet}》，尺寸 = {(row_end-row_start+1)} × {(c1-c0+1)}")

# ===== 修改这里为你的文件路径与sheet名 =====
build_A_from_block(
    file_path=r"D:\BaiduNetdiskDownload\投入产出表\31省市区42部门投入产出表1997-2017年\2017年各省份投入产出表\01-北京.xlsx",
    src_sheet="Sheet1",   # 改成你的源工作表名
    dst_sheet="A_matrix",  # 结果sheet名称，可自定义
    col_start="D", col_end="AS",
    row_start=9, row_end=50, denom_row=57
)


from openpyxl import load_workbook
from openpyxl.utils import column_index_from_string, get_column_letter

def apply_names_to_A_matrix(
    file_path: str,
    src_sheet: str,
    dst_sheet: str = "A_matrix",
    # 名称来源：B9:B50
    name_col: str = "B",
    name_row_start: int = 9,
    name_row_end: int = 50,
    # A_matrix 的行/列标题区域
    row_header_col: str = "A",        # A 列：A2..A43
    row_header_start_row: int = 2,
    # 列标题范围：B1..AS1
    col_header_start_col: str = "B",
    col_header_end_col: str = "AS",
    col_header_row: int = 1,
):
    wb = load_workbook(file_path)
    if src_sheet not in wb.sheetnames:
        raise ValueError(f"找不到源工作表：{src_sheet}")
    if dst_sheet not in wb.sheetnames:
        raise ValueError(f"找不到目标工作表：{dst_sheet}（请先运行生成 A_matrix 的步骤）")

    ws_src = wb[src_sheet]
    ws_dst = wb[dst_sheet]

    # 读取名称列表：B9..B50（共 42 个）
    names = []
    for r in range(name_row_start, name_row_end + 1):
        v = ws_src[f"{name_col}{r}"].value
        if v is None:
            v = ""  # 空值用空字符串占位
        names.append(str(v).strip())

    # 计算列标题应该覆盖的列数：B..AS
    c0 = column_index_from_string(col_header_start_col)
    c1 = column_index_from_string(col_header_end_col)
    expected_len = c1 - c0 + 1

    # 基本一致性检查
    if len(names) != expected_len:
        raise ValueError(
            f"名称数量（{len(names)}）与列数（{expected_len}，{col_header_start_col}..{col_header_end_col}）不一致。"
        )

    # 1) 覆盖 A2..A(1+len) 为行名
    ws_dst[f"{row_header_col}1"].value = "sector"  # A1 写个标签（可选）
    for i, nm in enumerate(names, start=row_header_start_row):  # 从 A2 开始
        ws_dst[f"{row_header_col}{i}"].value = nm

    # 2) 覆盖 B1..AS1 为列名（顺序与行名一致）
    for j, nm in enumerate(names, start=c0):  # 列从 B 开始
        ws_dst.cell(row=col_header_row, column=j, value=nm)

    wb.save(file_path)
    print(f"已将 {src_sheet}!{name_col}{name_row_start}:{name_col}{name_row_end} 的名称写入 {dst_sheet}："
          f"{row_header_col}{row_header_start_row}..{row_header_col}{row_header_start_row+len(names)-1} 和 "
          f"{col_header_start_col}{col_header_row}..{col_header_end_col}{col_header_row}。")

# ===== 用法示例：按需修改路径与工作表名 =====
apply_names_to_A_matrix(
     file_path=r"D:\BaiduNetdiskDownload\投入产出表\31省市区42部门投入产出表1997-2017年\2017年各省份投入产出表\01-北京.xlsx",
     src_sheet="Sheet1",  # 改成你的源工作表名
     dst_sheet="A_matrix",
     name_col="B", name_row_start=9, name_row_end=50,
     row_header_col="A", row_header_start_row=2,
     col_header_start_col="B", col_header_end_col="AQ", col_header_row=1
 )
