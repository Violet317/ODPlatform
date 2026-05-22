# ADR-003: 命名规范

## 状态
已接受

## 背景
项目涉及多个端、多种数据格式、多个工具模块，需要统一命名规范，
降低认知负荷，让团队成员能通过名字猜测代码功能。

## 决策

### 1. Python 包名 — snake_case
```
odp_platform                  # 主包
├── common                    # 公共工具
├── data_pipeline             # 数据管道
├── data_validation           # 数据校验
├── training                  # 模型训练
├── evaluation                # 模型评估
├── inference                 # 模型推理
└── cli                       # 命令行入口
```

### 2. 模块名 — snake_case + 功能后缀
| 后缀 | 用途 | 示例 |
|------|------|------|
| `_utils` | 工具函数 | `logging_utils.py`, `performance_utils.py` |
| `_config` | 配置相关 | `train_config.py` |
| `_service` | 服务层编排 | `training_service.py` |
| `_pipeline` | 管道处理 | `coco_pipeline.py` |

### 3. 类名 — PascalCase + 用途后缀
```
TrainConfig           # 配置类
PascalVOCConverter    # 转换器
MetricTracker         # 指标追踪器
TrainingHistory       # 训练历史管理器
```

### 4. 函数名 — snake_case + 动词优先
```
convert_voc_to_yolo()
validate_dataset()
get_logger()
train_model()
evaluate_model()
```

### 5. CLI 命令 — 前缀 + 连字符
```
odp-init              # 项目初始化
odp-trans             # 数据转换
odp-validate          # 数据校验
odp-train             # 模型训练
odp-val               # 模型评估
odp-infer             # 模型推理
```

### 6. Git 提交信息规范
```
feat:     新功能         feat: add VOC converter
fix:      修复 bug       fix: fix path resolution
docs:     文档改动       docs: update README
refactor: 重构代码       refactor: rename variables
perf:     性能优化       perf: cache path lookup
test:     测试相关       test: add unit tests
chore:    工程维护       chore: update deps
```

### 7. 目录命名
| 目录 | 命名规则 | 示例 |
|------|---------|------|
| 包内 | 下划线 | `data_pipeline/` |
| 数据 | 小写 | `data/models/`, `data/runs/` |
| 文档 | 小写 | `docs/architecture/` |

## 影响
- 命名即文档，阅读代码时减少心理负担
- 新模块自动遵循已有模式
- 全局搜索方便（如 `grep "def get_"` 可找出所有工厂函数）