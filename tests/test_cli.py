import csv
import json
import os
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def run_cli(*arguments: str) -> subprocess.CompletedProcess[str]:
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(PROJECT_ROOT / "src")
    return subprocess.run(
        [sys.executable, "-m", "nav_data_checker.cli", *arguments],
        cwd=PROJECT_ROOT,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )


def test_cli_writes_json_report(tmp_path: Path) -> None:
    source = tmp_path / "sample.csv"
    output = tmp_path / "report.json"
    write_csv(source, [{"timestamp": "0.0", "ax": "1.0"}, {"timestamp": "0.01", "ax": "1.1"}])

    result = run_cli(str(source), "--output", str(output))

    assert result.returncode == 0
    report = json.loads(output.read_text(encoding="utf-8"))
    assert report["row_count"] == 2
    assert "报告已写入" in result.stdout


def test_cli_missing_file_returns_actionable_error(tmp_path: Path) -> None:
    result = run_cli(str(tmp_path / "missing.csv"))

    assert result.returncode == 2
    assert "输入文件不存在" in result.stderr


def test_cli_missing_time_column_returns_actionable_error(tmp_path: Path) -> None:
    source = tmp_path / "no-time.csv"
    write_csv(source, [{"t": "0.0", "ax": "1.0"}])

    result = run_cli(str(source))

    assert result.returncode == 2
    assert "未找到时间列" in result.stderr
    assert "--time-column" in result.stderr


def test_cli_refuses_to_overwrite_input_file(tmp_path: Path) -> None:
    source = tmp_path / "source.csv"
    original = "timestamp,ax\n0.0,1.0\n0.1,1.1\n"
    source.write_text(original, encoding="utf-8")

    result = run_cli(str(source), "--output", str(source))

    assert result.returncode == 2
    assert "不能与输入文件相同" in result.stderr
    assert source.read_text(encoding="utf-8") == original


def test_cli_reports_output_io_error_without_traceback(tmp_path: Path) -> None:
    source = tmp_path / "source.csv"
    blocked_parent = tmp_path / "not-a-directory"
    write_csv(source, [{"timestamp": "0.0", "ax": "1.0"}])
    blocked_parent.write_text("occupied", encoding="utf-8")

    result = run_cli(str(source), "--output", str(blocked_parent / "report.json"))

    assert result.returncode == 2
    assert "无法写入报告" in result.stderr
    assert "Traceback" not in result.stderr
