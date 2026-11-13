import argparse
import csv
import json
import sys
from pathlib import Path

from .checker import check_csv


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="检查导航 CSV 的字段、时间戳、采样间隔和缺失/异常值。"
    )
    parser.add_argument("input", type=Path, help="待检查的 UTF-8 CSV 文件")
    parser.add_argument(
        "--time-column",
        default="timestamp",
        help="时间列名称，默认：timestamp",
    )
    parser.add_argument("--output", type=Path, help="JSON 报告输出路径")
    return parser


def main(argv: list[str] | None = None) -> int:
    arguments = build_parser().parse_args(argv)
    if arguments.output:
        try:
            same_path = arguments.input.samefile(arguments.output)
        except OSError:
            same_path = arguments.input.resolve() == arguments.output.resolve()
        if same_path:
            print("错误：报告输出路径不能与输入文件相同。", file=sys.stderr)
            return 2

    try:
        report = check_csv(arguments.input, arguments.time_column)
    except FileNotFoundError as error:
        print(f"错误：{error}", file=sys.stderr)
        return 2
    except (UnicodeError, csv.Error) as error:
        print(f"错误：无法解析 CSV：{error}", file=sys.stderr)
        return 2
    except ValueError as error:
        hint = "。如时间列名称不同，请使用 --time-column 指定" if "未找到时间列" in str(error) else ""
        print(f"错误：{error}{hint}。", file=sys.stderr)
        return 2
    except OSError as error:
        print(f"错误：无法读取输入文件：{error}", file=sys.stderr)
        return 2

    rendered = json.dumps(report, ensure_ascii=False, indent=2)
    if arguments.output:
        try:
            arguments.output.parent.mkdir(parents=True, exist_ok=True)
            arguments.output.write_text(rendered + "\n", encoding="utf-8")
        except OSError as error:
            print(f"错误：无法写入报告：{error}", file=sys.stderr)
            return 2
        print(f"报告已写入：{arguments.output}")
    else:
        print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

