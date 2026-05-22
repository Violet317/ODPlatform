# ADR-002: 数据管道架构

## 状态

✅ 已采纳 (2026-05-20)

## 背景

ODPlatform 需要统一管理遥感/无人机数据集的格式转换、划分和训练 YAML 生成。原始数据来源多样（VOC/COCO/YOLO），输出格式必须是 YOLO（Ultralytics 兼容）。

## 决策

采用 **注册表模式 + 模块化划分流水线** 架构：

```
原始数据 → [注册表查找转换器] → YOLO → [Manifest → Splitter → Materializer → YAML Writer]
```

### 1. 转换器注册表

- `registry.py` 维护 `_registry: dict[str, ConverterFunc]`，核心函数：
  - `_register(format_name, func)` — 各 converter 模块自主注册
  - `get_converter(format_name)` — 查找转换器
  - `list_capabilities()` — 格式能力矩阵
- `_lazy_init()` 延迟导入三个 core 模块，避免循环导入
- 各 `core/*.py` 模块文件末尾调用 `_register()` 自注册

### 2. ConvertOptions

- 单一数据类承载所有转换参数（输入/输出/类别/划分比例/随机种子）
- `__post_init__` 校验比例非负且之和=1

### 3. 划分流水线

| 模块 | 职责 |
|------|------|
| `manifest.py` | 扫描 YOLO 目录构建 (image, label) 配对 |
| `splitter.py` | 随机划分 train/val/test，边界处理 |
| `materializer.py` | 按 `{split}/images/` `{split}/labels/` 写入磁盘 |
| `yaml_writer.py` | 生成包含 `odp_meta` 块的 ultralytics yaml |

### 4. 覆盖率 fail-fast

- `orchestrator._check_raw()` 在转换前检查标注/图片比例
- 覆盖率 < 50% 拒绝转换

### 5. 命名空间

- 划分后 yaml 写入 `configs/datasets/<name>.yaml`
- yaml 含 `odp_meta` 块记录 pipeline 元数据

## 备选方案

| 方案 | 优点 | 缺点 |
|------|------|------|
| 工厂模式 | 集中创建 | 新格式需改工厂代码，违开发闭原则 |
| 抽象基类 | 接口强约束 | Python 缺乏编译期检查，不如 duck typing 灵活 |
| 注册表 ✅ | 新格式自主注册，无需改核心代码 | 需保证初始化顺序 |

## 影响

- 新格式支持只需新增 `core/xxx.py` + 调用 `_register`
- CLI 的 `--help` 能力矩阵从注册表实时读取，无需手工维护
- 旧版 `odp-trans` 保留兼容