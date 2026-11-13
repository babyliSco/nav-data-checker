import csv
import math
import sys
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from nav_data_checker.checker import check_csv  # noqa: E402


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def test_regular_navigation_csv_has_clean_summary(tmp_path: Path) -> None:
    source = tmp_path / "regular.csv"
    write_csv(
        source,
        [
            {"timestamp": "0.00", "gyro_z": "0.01", "latitude": "32.0"},
            {"timestamp": "0.01", "gyro_z": "0.02", "latitude": "32.000001"},
            {"timestamp": "0.02", "gyro_z": "0.03", "latitude": "32.000002"},
        ],
    )

    report = check_csv(source)

    assert report["row_count"] == 3
    assert report["columns"] == ["timestamp", "gyro_z", "latitude"]
    assert report["timestamp"]["duplicate_count"] == 0
    assert report["timestamp"]["out_of_order_count"] == 0
    assert report["timestamp"]["interval_stats"]["median"] == pytest.approx(0.01)
    assert report["timestamp"]["irregular_interval_count"] == 0
    assert report["missing_values"] == {"timestamp": 0, "gyro_z": 0, "latitude": 0}
    assert report["non_finite_values"] == {"timestamp": 0, "gyro_z": 0, "latitude": 0}
    assert report["warnings"] == []


def test_missing_time_column_is_rejected(tmp_path: Path) -> None:
    source = tmp_path / "no-time.csv"
    write_csv(source, [{"t": "0.0", "ax": "1.0"}])

    with pytest.raises(ValueError, match="时间列.*timestamp"):
        check_csv(source)


def test_single_row_has_no_interval_statistics(tmp_path: Path) -> None:
    source = tmp_path / "single.csv"
    write_csv(source, [{"timestamp": "1.0", "ax": "0.0"}])

    report = check_csv(source)

    assert report["timestamp"]["interval_stats"] is None
    assert any("少于 2" in warning for warning in report["warnings"])


def test_timestamp_and_value_anomalies_are_counted(tmp_path: Path) -> None:
    source = tmp_path / "anomalies.csv"
    write_csv(
        source,
        [
            {"timestamp": "0.00", "ax": "1.0", "ay": "2.0"},
            {"timestamp": "0.01", "ax": "", "ay": "bad"},
            {"timestamp": "0.01", "ax": "NaN", "ay": "3.0"},
            {"timestamp": "0.005", "ax": "Inf", "ay": "4.0"},
            {"timestamp": "0.10", "ax": "5.0", "ay": "5.0"},
        ],
    )

    report = check_csv(source)

    assert report["timestamp"]["duplicate_count"] == 1
    assert report["timestamp"]["out_of_order_count"] == 1
    assert report["timestamp"]["irregular_interval_count"] >= 1
    assert report["missing_values"]["ax"] == 1
    assert report["non_numeric_values"]["ay"] == 1
    assert report["non_finite_values"]["ax"] == 2
    assert len(report["warnings"]) >= 4


def test_non_finite_timestamp_is_reported_without_crashing(tmp_path: Path) -> None:
    source = tmp_path / "bad-time.csv"
    write_csv(
        source,
        [
            {"timestamp": "0.0", "ax": "1.0"},
            {"timestamp": str(math.nan), "ax": "2.0"},
            {"timestamp": "0.02", "ax": "3.0"},
        ],
    )

    report = check_csv(source)

    assert report["non_finite_values"]["timestamp"] == 1
    assert any("时间列" in warning for warning in report["warnings"])


@pytest.mark.parametrize(
    ("header", "message"),
    [
        ("timestamp,timestamp,ax\n0.0,0.1,1.0\n", "重复列名"),
        ("timestamp,,ax\n0.0,0.1,1.0\n", "空列名"),
    ],
)
def test_invalid_headers_are_rejected(tmp_path: Path, header: str, message: str) -> None:
    source = tmp_path / "bad-header.csv"
    source.write_text(header, encoding="utf-8")

    with pytest.raises(ValueError, match=message):
        check_csv(source)


def test_row_with_extra_cells_is_rejected(tmp_path: Path) -> None:
    source = tmp_path / "extra-cell.csv"
    source.write_text("timestamp,ax\n0.0,1.0,NaN\n", encoding="utf-8")

    with pytest.raises(ValueError, match="第 2 行.*多余字段"):
        check_csv(source)
