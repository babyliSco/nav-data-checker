# nav-data-checker

一个小而诚实的导航 CSV 数据质量检查工具。它不替你“调好滤波器”，只先回答几个基础问题：字段是否完整、时间戳是否单调、采样间隔是否异常、数据中是否存在空值、非数字、`NaN` 或 `Inf`。

项目对应文章：《组合导航结果为什么“看着很顺”，却可能从根上就是错的？》

## 当前能力

- 读取 UTF-8 / UTF-8 BOM CSV；
- 支持自定义时间列；
- 统计总行数和字段；
- 统计重复、逆序和异常采样间隔；
- 统计各字段缺失值、非数字值和非有限值；
- 输出中文告警和 JSON 报告；
- 只使用 Python 标准库，运行时无第三方依赖。

## 安装

需要 Python 3.11 或更高版本。

```bash
git clone https://github.com/babyliSco/nav-data-checker.git
cd nav-data-checker
python -m pip install -e .
```

仓库尚未发布时，可以直接在本目录执行安装命令。

## 使用

第一次使用、需要配置 PyCharm，或遇到导入与路径问题时，请先阅读：[运行说明.md](运行说明.md)。

检查示例数据并在终端输出 JSON：

```bash
nav-data-checker examples/sample_nav.csv
```

写入报告文件：

```bash
nav-data-checker examples/sample_nav.csv --output sample_report.json
```

时间列不叫 `timestamp` 时：

```bash
nav-data-checker your_data.csv --time-column time_s --output report.json
```

## 报告字段

| 字段 | 含义 |
|---|---|
| `row_count` | 数据行数 |
| `columns` | CSV 字段列表 |
| `timestamp.valid_count` | 有效时间戳数量 |
| `duplicate_count` | 相邻重复时间戳数量 |
| `out_of_order_count` | 相邻逆序时间戳数量 |
| `interval_stats` | 正采样间隔的最小值、中位数和最大值 |
| `irregular_interval_count` | 小于中位数 0.5 倍或大于 1.5 倍的正间隔数量 |
| `missing_values` | 各列空值数量 |
| `non_numeric_values` | 各列非数字数量 |
| `non_finite_values` | 各列 `NaN/Inf` 数量 |
| `warnings` | 面向人工复核的中文告警 |

## 测试

```bash
python -m pip install pytest
python -m pytest tests -v
```

## 局限

- 当前只接受 CSV，不自动识别 ROS bag、MAT、二进制或串口数据；
- 异常采样间隔采用简单的中位数比例规则，不是通用异常检测模型；
- 不进行坐标系转换、传感器标定、时间延迟估计或滤波器参数整定；
- 不判断某个传感器数值是否满足特定型号的物理范围；
- 报告是数据入口检查，不能替代完整的导航系统验证。

## 免费版与后续付费能力的边界

本仓库的单文件检查保持免费、可运行。只有在真实需求得到验证后，才考虑开发多文件批处理、字段映射、Markdown 报告、Windows 免配置打包和一次格式适配服务。

不会故意删除一个关键常数让免费版无法运行，也不会把尚未实现的功能写进当前能力。

## 许可证与来源

代码采用 MIT License。示例数据为本项目从零生成的合成数据，不对应任何真实设备、客户或课题数据。详见 [SOURCES.md](SOURCES.md)。

