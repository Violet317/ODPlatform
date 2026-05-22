# ODPlatform 命令速查

> 严格对齐 D3 / D4 讲义与需求规格说明书
> 注意：所有命令在项目根目录执行，不要在 `apps/platform/src` 下执行

---

## 一、环境搭建

```bash
# 激活环境（不同机器按实际情况）
conda activate odp-gpu

# 安装项目核心包（安装后才有 odp-xxx 命令）
pip install -e ./apps/platform

# 重装（修改 pyproject.toml 或 entry-point 后必须执行）
pip install -e ./apps/platform --force-reinstall --no-deps
```

---

## 二、D2 — 项目初始化与重置

### odp-init

```bash
# 创建所有运行时目录
odp-init
```

创建目录清单（D2 + D3 增量）：

```
data/raw/              # 数据集存放根
data/train/{images,labels}
data/val/{images,labels}
data/test/{images,labels}
data/runs/
outputs/
models/pretrained/
models/trained/
configs/datasets/      # D3 新增
```

### odp-reset

安全撤销 `odp-init` 创建的运行时产物，**只删白名单目录，不动 `data/raw/`**。

```bash
odp-reset                  # dry-run，只打印不删除
odp-reset --yes            # 真删除 + 交互确认
odp-reset --yes --force    # 跳过交互，直接删除
odp-reset --dry-run        # 显式 dry-run
```

---

## 三、D3 — 数据格式转换与划分

### 数据集目录约定

```
data/raw/<dataset_name>/
├── images/         # 原始图像 (jpg/png/...)
└── annotations/    # 原始标注 (xml/json/txt, 按格式而定)
```

### 查看支持的能力矩阵

```bash
odp-transform --list
```

输出示例：

```
格式能力矩阵:
  pascal_voc       -> ['detect']
  coco             -> ['detect', 'segment']
  yolo             -> ['detect']
```

### 端到端转换（原始数据集 → YOLO → 划分 → yaml）

```bash
# VOC → YOLO（推荐方式）
odp-transform --dataset voc --format pascal_voc

# 自定义划分比例 + 随机种子
odp-transform --dataset voc --format pascal_voc --train-rate 0.7 --val-rate 0.2

# 指定任务类型
odp-transform --dataset coco_demo --format coco --task segment

# COCO 91→80 类别映射
odp-transform --dataset coco_demo --format coco --coco-cls91to80

# 指定类别白名单
odp-transform --dataset voc --format pascal_voc --classes cat dog bird
```

### 输出产物

```
data/
├── train/images/*.jpg
├── train/labels/*.txt
├── val/images/*.jpg
├── val/labels/*.txt
└── test/images/*.jpg
└── test/labels/*.txt

configs/datasets/<dataset_name>.yaml    # ultralytics 训练 yaml
```

### 覆盖率 fail-fast

标注覆盖率低于 50% 时立即阻断：

```bash
odp-transform --dataset broken_voc --format pascal_voc
# ❌ 图像-标注覆盖率过低: 5.0% (硬阈值 50%)
```

### od-pipeline 架构说明

```
data_pipeline/
├── registry.py       # 注册表 + @register 装饰器
├── service.py        # 调度层（converter_data_to_yolo）
├── orchestrator.py   # 端到端 DatasetPipeline
├── core/
│   ├── pascal_voc.py # VOC XML → YOLO txt
│   ├── coco.py       # COCO JSON → YOLO txt
│   └── yolo.py       # YOLO 直通
└── split/
    ├── manifest.py     # 划分清单
    ├── splitter.py     # 随机划分
    ├── materializer.py # 落盘（copy/hardlink）
    └── yaml_writer.py  # 生成 ultralytics yaml
```

---

## 四、D4 — 数据校验

### 快速质检（推荐方式）

```bash
# 按数据集名质检（自动查找 configs/datasets/<name>.yaml）
odp-validate --dataset voc

# 指定任务类型
odp-validate --dataset voc --task detect

# 调试方式：直接指定 yaml 路径
odp-validate --yaml configs\datasets\voc.yaml

# 详细模式（显示 DEBUG 日志）
odp-validate --dataset voc --verbose

# 不写 JSON 报告
odp-validate --dataset voc --no-report
```

### 验收场景

#### 7.1 健康数据集

```bash
odp-validate --dataset voc --task detect
echo "exit: $?"
```

期望：4 PASS，退出码 0，生成 `runs/data_validation/<run_id>/report.json`

#### 7.2 数据泄露检测

```bash
# 将一张训练集图片复制到验证集
cp data/voc/train/images/xxx.jpg data/voc/val/images/
odp-validate --dataset voc --task detect
# 期望：split_uniqueness ERROR，其他 3 个 check 仍跑完
# 恢复
rm data/voc/val/images/xxx.jpg
```

#### 7.3 坏 yaml 诊断

构造 `nc=3` 但 `names=['a','b']`（长度不匹配），yaml_schema 输出 ERROR。

#### 7.5 退出码语义

| 场景 | 退出码 |
|---|---|
| 全 PASS | 0 |
| 仅 INFO，无 WARNING/ERROR | 0 |
| 含 WARNING，无 ERROR | 1 |
| 含 ERROR | 2 |
| Ctrl-C | 3 |

### 数据校验架构说明

```
data_validation/
├── registry.py       # @check 装饰器 + 自动 import
├── snapshot.py       # DatasetSnapshot + build_snapshot
├── service.py        # run_all_checks + validate_dataset
├── report.py         # ValidationReport（纯数据）
├── render.py         # render_to_logger（纯展示）
└── checks/
    ├── yaml_schema.py      # yaml 字段完整性
    ├── pair_existence.py   # 图像-标签配对
    ├── label_format.py     # YOLO txt 行格式
    └── split_uniqueness.py # train/val/test 图像唯一性
```

四个 check 互相独立，任何一个抛异常不阻断其他 check。

---

## 五、D5 — 配置管理子系统

### 生成默认配置

```bash
# 生成训练配置（输出到 configs/train_config.yaml）
odp-config generate --task train

# 指定输出路径
odp-config generate --task train --output my_config.yaml
```

### 验证配置

```bash
# 验证正确配置
odp-config validate --config configs\train_config.yaml --task train

# 验证错误配置（nc=3 但 names 只有 2 个）
odp-config validate --config configs\bad_config.yaml --task train
# 期望：yaml_schema ERROR → 退出码 2
```

### 追踪配置来源

```bash
# 查看配置文件中每个字段的来源层级
odp-config trace --config configs\train_config.yaml
# 输出示例：classes → CLI > env var > default
```

### 配置快照（保存 & 恢复）

```bash
# 导出快照（保存当前配置的完整副本）
odp-config snapshot export --config configs\train_config.yaml

# 恢复快照（从历史快照恢复配置）
odp-config snapshot restore --snapshot runs\config_snapshots\<snapshot_name>.yaml

# 快照目录：runs/config_snapshots/
```

### 配置管理架构说明

```
config_manager/
├── registry.py       # @config_generator 注册装饰器
├── service.py        # 核心调度（generate/validate/trace/snapshot）
├── snapshot.py       # snapshot 导出与恢复
├── generator.py      # 配置生成器基类
├── validator.py      # 配置校验器
├── tracer.py         # 配置溯源
└── generators/
    └── train.py      # 训练配置生成器
```

---

## 六、集成命令（D3 + D4 + D5 串联）

### 端到端训练准备

```bash
# 一键运行：数据验证 → 配置生成 → 快照保存（不实际训练）
odp-train --dry-run

# 输出流程：
#   1. odp-transform D3 数据校验（内部调用）
#   2. odp-validate D4 数据质检
#   3. odp-config generate 自动生成配置
#   4. odp-config snapshot export 保存快照
#   5. 退出（--dry-run 跳过实际训练）
```

---

## 七、回归测试

```bash
# 从 apps/platform/src 目录运行
cd apps\platform\src
python -m pytest tests -v
```

---

## 八、关键目录结构

```
ODPlatform/
├── apps/platform/
│   ├── src/odp_platform/
│   │   ├── cli/
│   │   │   ├── init_project.py     # odp-init
│   │   │   ├── reset_project.py    # odp-reset
│   │   │   ├── transform_data.py   # odp-transform （D3）
│   │   │   ├── validate_data.py    # odp-validate （D4）
│   │   │   ├── config_cli.py       # odp-config （D5）
│   │   │   └── train.py            # odp-train （集成）
│   │   ├── common/
│   │   │   ├── paths.py
│   │   │   ├── constants.py
│   │   │   └── ...
│   │   ├── data_pipeline/          # D3 子系统
│   │   │   ├── registry.py
│   │   │   ├── service.py
│   │   │   ├── orchestrator.py
│   │   │   ├── core/
│   │   │   └── split/
│   │   ├── data_validation/        # D4 子系统
│   │   │   ├── registry.py
│   │   │   ├── snapshot.py
│   │   │   ├── service.py
│   │   │   ├── report.py
│   │   │   ├── render.py
│   │   │   └── checks/
│   │   ├── config_manager/         # D5 子系统
│   │   │   ├── registry.py
│   │   │   ├── service.py
│   │   │   ├── snapshot.py
│   │   │   ├── generator.py
│   │   │   ├── validator.py
│   │   │   ├── tracer.py
│   │   │   └── generators/
│   │   └── __init__.py
│   ├── configs/
│   │   ├── datasets/               # 数据集 yaml
│   │   ├── train_config.yaml       # 训练配置
│   │   └── bad_config.yaml         # 坏配置（测试用）
│   └── pyproject.toml
├── data/
│   ├── raw/<dataset>/{images,annotations}/
│   ├── {train,val,test}/{images,labels}/
│   └── runs/
│       ├── data_validation/        # D4 质检报告
│       └── config_snapshots/       # D5 配置快照
├── scripts/
└── ODPlatform_命令速查.md
```