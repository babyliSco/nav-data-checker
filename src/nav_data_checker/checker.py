import csv
import math
import statistics
from collections import Counter
from pathlib import Path


def check_csv(path: Path, time_column: str = "timestamp") -> dict[str, object]:
    """Return a navigation-data quality report."""
    source = Path(path)
    if not source.is_file():
        raise FileNotFoundError(f"输入文件不存在：{source}")

    with source.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, strict=True)
        columns = list(reader.fieldnames or [])
        if not columns:
            raise ValueError("CSV 缺少表头")
        if any(not column.strip() for column in columns):
            raise ValueError("CSV 表头存在空列名")
        duplicate_columns = [
            column for column, count in Counter(columns).items() if count > 1
        ]
        if duplicate_columns:
            raise ValueError(f"CSV 表头存在重复列名：{', '.join(duplicate_columns)}")
        if time_column not in columns:
            raise ValueError(f"未找到时间列：{time_column}")
        rows = list(reader)
        for row_number, row in enumerate(rows, start=2):
            if None in row:
                raise ValueError(f"第 {row_number} 行存在多余字段")

    missing_values = {column: 0 for column in columns}
    non_numeric_values = {column: 0 for column in columns}
    non_finite_values = {column: 0 for column in columns}
    numeric_times: list[float] = []

    for row in rows:
        for column in columns:
            raw_value = (row.get(column) or "").strip()
            if not raw_value:
                missing_values[column] += 1
                continue
            try:
                value = float(raw_value)
            except ValueError:
                non_numeric_values[column] += 1
                continue
            if not math.isfinite(value):
                non_finite_values[column] += 1
                continue
            if column == time_column:
                numeric_times.append(value)

    intervals = [
        current - previous
        for previous, current in zip(numeric_times, numeric_times[1:])
    ]
    duplicate_count = sum(interval == 0 for interval in intervals)
    out_of_order_count = sum(interval < 0 for interval in intervals)
    positive_intervals = [interval for interval in intervals if interval > 0]

    interval_stats: dict[str, float] | None = None
    irregular_interval_count = 0
    if positive_intervals:
        median_interval = statistics.median(positive_intervals)
        lower_bound = median_interval * 0.5
        upper_bound = median_interval * 1.5
        irregular_interval_count = sum(
            interval < lower_bound or interval > upper_bound
            for interval in positive_intervals
        )
        interval_stats = {
            "min": min(positive_intervals),
            "median": median_interval,
            "max": max(positive_intervals),
        }

    warnings: list[str] = []
    if len(numeric_times) < 2:
        warnings.append("有效时间戳少于 2 个，无法计算采样间隔")
    if missing_values[time_column]:
        warnings.append(f"时间列存在 {missing_values[time_column]} 个缺失值")
    if non_numeric_values[time_column]:
        warnings.append(f"时间列存在 {non_numeric_values[time_column]} 个非数字值")
    if non_finite_values[time_column]:
        warnings.append(f"时间列存在 {non_finite_values[time_column]} 个 NaN/Inf")
    if duplicate_count:
        warnings.append(f"发现 {duplicate_count} 个重复时间戳")
    if out_of_order_count:
        warnings.append(f"发现 {out_of_order_count} 个逆序时间戳")
    if irregular_interval_count:
        warnings.append(f"发现 {irregular_interval_count} 个异常采样间隔")

    missing_total = sum(missing_values.values())
    non_numeric_total = sum(non_numeric_values.values())
    non_finite_total = sum(non_finite_values.values())
    if missing_total and not missing_values[time_column]:
        warnings.append(f"其他字段共有 {missing_total} 个缺失值")
    if non_numeric_total and not non_numeric_values[time_column]:
        warnings.append(f"其他字段共有 {non_numeric_total} 个非数字值")
    if non_finite_total and not non_finite_values[time_column]:
        warnings.append(f"其他字段共有 {non_finite_total} 个 NaN/Inf")

    return {
        "source": str(source),
        "row_count": len(rows),
        "columns": columns,
        "timestamp": {
            "column": time_column,
            "valid_count": len(numeric_times),
            "duplicate_count": duplicate_count,
            "out_of_order_count": out_of_order_count,
            "interval_stats": interval_stats,
            "irregular_interval_count": irregular_interval_count,
        },
        "missing_values": missing_values,
        "non_numeric_values": non_numeric_values,
        "non_finite_values": non_finite_values,
        "warnings": warnings,
    }
