# ODPlatform - Object Detection Platform

基于 YOLO 的多格式目标检测开发平台，覆盖数据转换、模型训练、评估和推理全流程。

## 快速开始

```bash
conda create -n odp-gpu python=3.12 -y
conda activate odp-gpu
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
cd apps/platform
pip install -e .
cd ../..
```

## CLI 命令速览

| 命令 | 功能 | 详细文档 |
|------|------|---------|
| `odp-init` | 初始化项目目录 | [命令速查](ODPlatform_命令速查.md#二项目初始化-odp-init) |
| `odp-reset` | 安全重置运行时产物 | [命令速查](ODPlatform_命令速查.md#三项目重置-odp-reset) |
| `odp-transform` | 端到端数据转换+划分+yaml | [命令速查](ODPlatform_命令速查.md#四数据格式转换与划分-odp-transform) |
| `odp-trans` | 旧版单步格式转换 | [命令速查](ODPlatform_命令速查.md#五旧版单步转换-odp-trans--兼容保留) |
| `odp-validate` | 数据集校验与分析 | [命令速查](ODPlatform_命令速查.md#六数据校验-odp-validate) |
| `odp-train` | 模型训练 | [命令速查](ODPlatform_命令速查.md#十训练-odp-train) |
| `odp-val` | 模型评估 | [命令速查](ODPlatform_命令速查.md#十一评估-odp-val) |
| `odp-infer` | 模型推理 | [命令速查](ODPlatform_命令速查.md#十二推理-odp-infer) |

## 项目结构

```
ODPlatform/
├── apps/platform/           ← 核心引擎
│   └── src/odp_platform/
│       ├── common/         基础工具（路径/日志/性能）
│       ├── config/         配置管理
│       ├── data_pipeline/  数据管道（格式转换+划分）
│       ├── data_validation/数据校验
│       ├── training/       模型训练
│       ├── evaluation/     模型评估
│       ├── inference/      模型推理
│       └── cli/            命令行入口
├── docs/                   文档 + ADR + SRS
├── data/                   数据集（.gitignore）
├── models/                 模型权重（Git LFS）
└── pyproject.toml          开发工具配置
```

## 支持的数据格式

| 输入 → 输出 | 命令 |
|-----------|------|
| Pascal VOC → YOLO | `odp-trans voc` / `odp-transform` |
| COCO → YOLO | `odp-trans coco` / `odp-transform` |
| LabelMe → YOLO | `odp-trans labelme` |
| YOLO → COCO | `odp-trans yolo2coco` |
| YOLO 重排+划分 | `odp-transform --format yolo` |

## 文档导航

| 文档 | 内容 |
|------|------|
| [命令速查](ODPlatform_命令速查.md) | 所有 CLI 命令及参数（日常使用） |
| [学习指南](ODPlatform_学习指南.md) | 架构详解 + 学习路线（从零入门） |
| [企业软件开发指南](ODPlatform_企业软件开发指南.md) | 企业级工程规范与最佳实践 |
| [项目结构设计指南](ODPlatform_项目结构设计指南_V1_0.pdf) | 架构决策与演进路线 |
| [企业级优化建议](ODPlatform_企业级优化建议.md) | serve 项目改造参考 |

## 数据集存放规范

数据集统一存放在 `data/` 下，按名称组织：

```
data/
├── RSOD/        # RSOD 遥感数据集
├── DIOR/        # DIOR 遥感数据集
└── coco128/     # 快速测试数据集
```

**完整流程示例**：

```bash
odp-init                                                  # 1. 初始化目录
odp-transform --dataset RSOD --format pascal_voc \         # 2. 数据转换+划分
    --source-dir data\raw\RSOD --output-dir data\yolo\RSOD \
    --classes "aircraft ship oiltank playground overpass"
odp-train --model yolo11n.pt \                            # 3. 训练
    --data configs\datasets\RSOD.yaml --epochs 100
odp-val --model data\runs\train\exp\weights\best.pt \     # 4. 评估
    --data configs\datasets\RSOD.yaml
odp-infer --model best.pt --source data\test\images       # 5. 推理
```

## License

MIT License - see [LICENSE](LICENSE) for details.