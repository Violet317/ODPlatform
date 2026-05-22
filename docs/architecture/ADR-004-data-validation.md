# ADR-004: 数据质量检查子系统 (D4)

## 状态

已实现 (2026-05-21)

## 上下文

D3 数据流水线完成格式转换和数据集划分后，产出的 YOLO 数据集可能隐含多种质量问题：
- YAML 配置文件字段缺失/错误（nc/names 不匹配）
- 图像-标签文件配对缺失（部分图像无对应标签）
- 标签文件格式错误（class_id 越界、坐标值非法）
- 训练/验证/测试集图像重复（数据泄露）

需要一个独立的质检子系统，在模型训练前对数据集进行全面检查。

## 决策

实现 `odp.data_validation` 质检子系统，核心设计如下：

### 1. 注册表模式 + 自动发现

延续 D3 转换器的注册表模式，质检 check 通过 `@check("name")` 装饰器注册，
`pkgutil.iter_modules` 实现自动发现。新增 `_INITIALIZED` 守卫旗标解决
直接 import 单个 check 模块导致部分模块未被加载的问题。

### 2. 四层架构

| 层次 | 模块 | 职责 |
|------|------|------|
| 数据模型 | `snapshot.py` | `DatasetSnapshot` 不可变快照，反映数据集元数据 |
| 注册管理 | `registry.py` | `CheckEntry`/`CheckResult`/`CheckSeverity` |
| 检查器 | `checks/` | 每个 .py 文件实现一个独立 check |
| 编排/报告 | `service.py` / `report.py` / `render.py` | 协调执行/数据类/日志渲染 |

### 3. 四个核心检查器

- **yaml_schema**: 验证 YAML 文件存在、可解析、nc/names 完整且一致
- **pair_existence**: 逐 split 检查图像-标签配对完整性，阈值 5% WARN / 50% ERROR
- **label_format**: 解析每行标签，验证 class_id 范围、坐标值格式和边界
- **split_uniqueness**: 跨 split 去重检测，防止数据泄露

### 4. 报告体系

`ValidationReport` 纯数据类承载完整质检结果，支持：
- `to_dict()` → JSON 序列化
- `render_to_logger()` → 控制台友好输出
- `exit_code` 派生属性（0=通过 / 1=警告 / 2=错误）

## 后果

### 正面

- 与 D3 转换器一致的注册表/装饰器模式，降低学习成本
- `DatasetSnapshot` 不可变数据结构避免并发修改
- 覆盖率前置校验（50% 硬阈值）在 D3 转换阶段拦截低质量数据
- JSON 报告持久化支持后续分析

### 负面

- 当前仅支持 detect/segment 两种任务的标签格式校验
- `scan_warnings` 在快照构建阶段收集，非结构化可能丢失部分上下文

## 相关 ADR

- [ADR-001: Monorepo 结构设计](./ADR-001-monorepo.md)
- [ADR-002: 数据流水线 (D3)](./ADR-002-data-pipeline.md)
- [ADR-003: 命名规范](./ADR-003-naming.md)