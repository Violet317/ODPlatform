# ADR-013: 运行配置子系统 (run_config)

| 字段 | 内容 |
|---|---|
| 状态 | Accepted |
| 日期 | 2026-05-22 |
| 决策者 | 实训团队 |
| 受影响范围 | `run_config/` 模块、CLI `odp-config` 命令 |
| 相关 ADR | ADR-004(配置系统设计，本 ADR 为其具体实现)、ADR-007(训练编排)、ADR-008(推理流水线) |

## 背景

ADR-004 确立了"三源合并（代码默认值 → YAML → CLI）+ 来源溯源"的配置设计方向，但留下了具体实现方式的选择：

- ADR-004 设想的方案是**每类任务一个 Pydantic 模型**（TrainConfig、ValConfig 等）
- 但随着 D5 实训推进，遇到几个具体问题：
  1. **跨任务共享字段**：model、device、workers 等字段在不同任务中重复定义，Pydantic 模型继承体系会让字段溯源变得复杂
  2. **配置溯源需要每个字段独立跟踪来源**：Pydantic 模型在校验时会丢失"这个值来自哪个源头"的信息
  3. **字段按任务分组**：同一个字段名在不同任务中可能有不同的默认值或约束（如 batch 在 train 中默认 16，在 val 中默认 16 但含义不同）
  4. **实验复现需要可序列化的快照**：快照需要包含完整配置 + 时间戳 + 版本号，Pydantic 模型序列化会携带类结构信息

这些问题的本质是：**配置管理需要"字段为中心"的视角，而非"任务为中心"的视角**。

## 选项

### 选项 A:Pydantic 模型继承体系（ADR-004 原方案）

每类任务一个 Pydantic 模型，共享字段通过基类继承。

```
BaseConfig (model, device, workers, ...)
├── TrainConfig (epochs, batch, lr0, ...)
├── ValConfig (batch, imgsz, conf, ...)
└── PredictConfig (source, save_txt, ...)
```

- **优点**：类型安全、IDE 提示好、Pydantic 生态成熟
- **缺点**：
  - 字段溯源需要额外包装（Pydantic 不原生支持"每个字段来自哪里"）
  - 同名字段在不同任务中有不同约束（如 batch 的 group 不同），继承体系难以表达
  - 新增字段需要修改模型定义，违反开闭原则
  - 序列化会携带 Pydantic 模型结构信息，快照不纯净

### 选项 B:ConfigField 注册表 + 懒加载字段模块（采用方案）

用 `ConfigField` 定义单个字段（名称 + 类型 + 默认值 + 分组 + 校验规则），通过注册表统一管理，按需懒加载。

```
run_config/
├── registry.py     # 注册表：register_field / get_field / list_fields
├── fields/         # 字段定义模块（按任务分组）
│   ├── __init__.py # 通用字段（task, model, device, workers, ...）
│   ├── train.py    # 训练专用字段（epochs, batch, lr0, ...）
│   ├── val.py      # 验证专用字段（batch, imgsz, conf, ...）
│   └── predict.py  # 推理专用字段（source, save_txt, ...）
├── schema.py       # 数据结构（ConfigField, ConfigBundle, ConfigSnapshot, TraceRecord）
├── loader.py       # YAML 加载 + CLI 参数解析
├── merger.py       # 三源合并（默认值 → YAML → CLI）
├── validator.py    # 字段级校验 + 跨字段校验
└── service.py      # 编排层（build_config / restore_from_snapshot）
```

- **优点**：
  - **字段为中心**：每个字段独立定义，同名字段首次注册生效，后续静默跳过
  - **按任务分组**：通过 `group` 字段（如 `"train_训练"`）支持 `list_fields(task)` 过滤
  - **溯源原生支持**：merge 过程中自动记录每个字段的来源链
  - **开闭原则**：新增字段只需新建 .py 文件注册，不改旧代码
  - **快照纯净**：`ConfigSnapshot` 只存 `{field: value}` 字典，不携带类结构
- **缺点**：
  - 比 Pydantic 多一些样板代码（每个字段要写 ConfigField 定义）
  - 没有 IDE 静态类型提示（配置值运行时才确定类型）
  - 同名字段冲突用"首次注册胜出"策略，可能丢失任务特化约束

### 选项 C:JSON Schema + 动态校验

用 JSON Schema 定义配置结构，用 jsonschema 库校验。

- **优点**：语言无关、生态广
- **缺点**：Python 类型提示丢失；溯源需要额外实现；动态校验错误信息不够友好

## 决策

**采纳选项 B（ConfigField 注册表 + 懒加载字段模块）**。

## 理由

1. **溯源是三源合并的核心价值**：TraceRecord 在 merge 过程中自然产生，每个字段都记录"最终值"和"来源链"。这是 Pydantic 方案需要额外包装才能做到的。
2. **字段懒加载让新增字段零侵入**：在 `fields/` 目录下新建 .py 文件，调用 `register_field()` 即可。不需要修改 registry、merger、validator 等框架代码。
3. **register_field 幂等设计**：同名字段在不同模块中重复定义时，首次注册胜出，后续静默跳过。这让共享字段（如 device、batch）可以在 `__init__.py` 中统一定义，任务模块中的同名定义被安全忽略。
4. **ConfigSnapshot 为实验复现而生（FR-23）**：
   ```python
   @dataclass(frozen=True)
   class ConfigSnapshot:
       version: int       # 快照格式版本号
       task: str          # 任务类型
       config: dict       # 纯键值对，无类结构
       created_at: str    # ISO 时间戳
   ```
   序列化为 JSON 后体积小、可读性强、跨语言兼容。
5. **敏感字段脱敏（FR-24）**：ConfigField 的 `sensitive=True` 标记在 `to_report_dict(mask_sensitive=True)` 时自动将值替换为 `"***"`，适用于 API Key 等凭据。
6. **CLI 一体化**：`odp-config` 子命令（generate / validate / trace / snapshot）全部基于同一套 registry 和 service，命令行体验与 Python API 一致。

## 后果

### 正面后果
- 溯源成为配置系统的自然产物，非额外功能
- 新增一个配置字段 = 在 `fields/` 下加一个注册调用，不影响任何现有代码
- 快照 JSON 可以直接用于跨环境传递和存档
- 敏感字段脱敏机制无需用户额外配置，声明即生效

### 代价
- 字段定义散布在多个文件中，查看"某个任务有哪些字段"需要查多个文件（可通过 `odp-config generate --task <T>` 查看完整清单）
- 同名字段"首次注册胜出"策略意味着 `predict.py` 中定义的 device（group="predict_输入"）不会生效，而是使用 `__init__.py` 中的通用定义（group="模型"）。这意味着 `list_fields("predict")` 不会返回 device——但 build_config 使用时，`list_fields()`（无过滤）会包含所有字段，所以 device 仍然可用且校验通过。
- ConfigField 是运行时类型检查，不是静态类型检查——传错类型在配置加载时报错而非 IDE 提示

## 何时重新评估

1. 如果字段数量膨胀到 100+，文件碎片化成为维护负担 → 考虑按功能域合并字段模块
2. 如果需要对同一字段在不同任务中有不同约束（如 train batch 和 val batch 有不同 ge/le）→ 需要引入"任务感知"的字段定义机制（如 ConfigField(task_overrides=...)）
3. 如果 Pydantic v3 或替代方案出现原生溯源支持 → 重新评估是否迁移

## 延伸资料
- ADR-004：配置系统设计（本 ADR 的具体实现）
- `odp_platform/run_config/` 源码
- `SRS-ODPlatform 运行配置子系统.md`：需求规格说明书