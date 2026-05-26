# ODPlatform AI 接手指南

> **目标**：让新启动的 AI 在 5 分钟内了解项目全貌，避免每次重复询问上下文。

---

## 一、项目定位

ODPlatform 是一个**通用目标检测开发平台**。它不是一个训练好的模型，而是一个**工程平台**——覆盖从原始标注数据 → 格式转换 → 数据校验 → 配置管理 → 训练/推理的全链路。
具体到项目就是低空航拍智能目标识别与监测系统。
其他应用方向包括但不限于：遥感图像检测、安全帽检测、车辆检测、工业质检等。

核心技术栈：
- **深度学习框架**：Ultralytics YOLOv**（作为底层训练/推理引擎）
- **前端/UI**：Gradio（Python Web UI）
- **数据格式**：Pascal VOC / COCO JSON → YOLO txt
- **配置管理**：自研 field 注册表 + YAML 配置链

---

## 二、环境配置（关键！）

### Conda 环境

```bash
# 环境名：odp-gpu
# Python 版本：3.10+
# 位置：E:\Anaconda\envs\odp-gpu\
conda activate odp-gpu
```

### 安装项目包（首次 / 依赖变更后）

```bash
# 必须 cd 到 apps/platform 目录安装
cd F:\python_projects\class\ODPlatform\apps\platform
pip install -e .
```

如需重装（entry-point 变更时）：

```bash
pip install -e . --force-reinstall --no-deps
```

### 项目根目录

```
F:\python_projects\class\ODPlatform
```

**所有命令都在项目根目录下执行**，不要 cd 到 `apps/platform/src`。

---

## 三、目录结构速览

```
ODPlatform/
├── apps/
│   └── platform/                        # 核心平台（唯一活跃端）
│       ├── src/odp_platform/
│       │   ├── cli/                     # CLI 命令入口（odp-*）
│       │   │   ├── init_project.py      #   odp-init
│       │   │   ├── reset_project.py     #   odp-reset
│       │   │   ├── transform_data.py    #   odp-transform（D3 数据管线）
│       │   │   ├── validate_data.py     #   odp-validate（D4 数据校验）
│       │   │   ├── config_cli.py        #   odp-config（D5 配置管理）
│       │   │   └── train.py            #   odp-train（集成入口）
│       │   ├── common/                  # 公共模块
│       │   │   ├── paths.py             #   路径中心化管理
│       │   │   ├── constants.py         #   共享常量/枚举
│       │   │   ├── logging_utils.py     #   日志工具
│       │   │   └── string_utils.py      #   字符串工具
│       │   ├── data_pipeline/           # D3：数据格式转换+划分
│       │   │   ├── registry.py          #   @register 装饰器
│       │   │   ├── service.py           #   调度层
│       │   │   ├── orchestrator.py      #   端到端管线
│       │   │   ├── core/{coco,pascal_voc,yolo}.py
│       │   │   └── split/{manifest,splitter,materializer,yaml_writer}.py
│       │   ├── data_validation/         # D4：数据质检
│       │   │   ├── registry.py          #   @check 装饰器
│       │   │   ├── service.py           #   调度层
│       │   │   ├── snapshot.py          #   数据集快照
│       │   │   ├── report.py / render.py
│       │   │   └── checks/              #   4 个检查器
│       │   ├── run_config/              # D5：运行配置管理
│       │   │   ├── registry.py          #   @config_field 装饰器
│       │   │   ├── service.py           #   调度层
│       │   │   ├── schema.py / validator.py
│       │   │   ├── template.py / merger.py / loader.py
│       │   │   └── fields/{train,val,predict}.py
│       │   ├── webui/                   # Gradio 前端
│       │   │   ├── app.py               #   create_app() 入口
│       │   │   ├── dashboard.py         #   Dashboard Tab
│       │   │   ├── dataset_browser.py   #   数据集浏览 Tab
│       │   │   ├── training_tab.py      #   训练 Tab
│       │   │   ├── model_demo.py        #   模型演示 Tab
│       │   │   ├── validation_tab.py    #   数据校验 Tab
│       │   │   ├── config_tab.py        #   配置管理 Tab
│       │   │   └── utils.py             #   UI 工具函数
│       │   └── _version.py              # 版本号：0.1.0
│       ├── configs/
│       │   ├── datasets/                # 数据集 YAML 配置
│       │   ├── train_config.yaml        # 训练配置
│       │   └── *.example.yaml           # 参考配置
│       ├── logging/                     # 运行时日志
│       └── pyproject.toml              # 包定义 + entry-points
├── data/
│   ├── raw/<dataset>/                   # 原始数据（images/ + annotations/）
│   ├── {train,val,test}/{images,labels}/ # 转换后 YOLO 格式
│   ├── models/{pretrained,checkpoints}/
│   └── runs/{data_validation,run_config}/
├── docs/
│   ├── architecture/                    # ADR 决策记录
│   ├── srs/                             # 需求规格说明书
│   └── teaching/                        # 教学讲义
├── scripts/                             # 工具脚本
└── pyproject.toml                       # 顶层工具配置（ruff/mypy/pytest）
```

### 关键路径速查

| 用途 | 路径 |
|------|------|
| 包源码 | `apps/platform/src/odp_platform/` |
| CLI 入口 | `apps/platform/src/odp_platform/cli/` |
| WebUI 入口 | `apps/platform/src/odp_platform/webui/app.py:create_app()` |
| 数据集配置 | `apps/platform/configs/datasets/*.yaml` |
| 日志目录 | `apps/platform/logging/` |
| 原始数据 | `data/raw/<dataset_name>/` |
| YOLO 数据 | `data/{train,val,test}/{images,labels}/` |
| 文档 | `docs/` |

---

## 四、可用数据集

| 数据集名 | 格式 | 类别数 | 类别 | 样本数 |
|----------|------|--------|------|--------|
| `rsod` | Pascal VOC | 4 | aircraft, oiltank, overpass, playground | 936 |
| `voc` | Pascal VOC | 4 | cat, dog, bird, fish | 10 |
| `coco_demo` | COCO | 3 | person, bicycle, car | 5 |
| `safety_helmet` | Pascal VOC | 3 | head, helmet, person | 8 |

数据量小的（voc/coco_demo/safety_helmet）是测试数据集，`rsod` 是真实遥感数据集。

---

## 五、CLI 命令大全

安装 `pip install -e ./apps/platform` 后获得以下命令：

| 命令 | 功能 | 对应模块 |
|------|------|----------|
| `odp-init` | 创建运行时目录结构 | `cli/init_project.py` |
| `odp-reset` | 安全清除运行时产物 | `cli/reset_project.py` |
| `odp-transform` | 数据格式转换（VOC/COCO → YOLO）+ 划分 | `cli/transform_data.py` |
| `odp-validate` | 数据质量校验（4 项检查） | `cli/validate_data.py` |
| `odp-config` | 配置生成/验证/溯源/快照 | `cli/config_cli.py` |
| `odp-train` | 端到端训练（含前置校验） | `cli/train.py` |
| `odp-webui` | 启动 Gradio 前端 | `webui/app.py:main()` |

### 常用命令示例

```bash
# 初始化项目目录
odp-init

# 转换数据集
odp-transform --dataset rsod --format pascal_voc

# 数据校验
odp-validate --dataset rsod

# 生成训练配置
odp-config generate --task train

# 启动 WebUI（需先安装 gradio）
odp-webui
# 或：
python -c "import sys; sys.path.insert(0, 'apps/platform/src'); from odp_platform.webui import create_app; create_app().launch(server_name='0.0.0.0', server_port=7860)"

# 运行测试
cd apps\platform\src
python -m pytest tests -v
```

---

## 六、Gradio 前端（WebUI）

入口文件：`apps/platform/src/odp_platform/webui/app.py`

核心函数：`create_app()` → 返回 `gr.Blocks` 对象

6 个 Tab：
1. **Dashboard** — 项目概览、实验状态
2. **数据集浏览** — 查看图片 + 标注
3. **训练** — 配置参数 + 启动训练（调用 `odp-train`）
4. **模型演示** — 加载模型 + 推理 + 结果可视化（调用 `model_demo.py`）
5. **数据校验** — 运行质检 + 查看报告
6. **配置管理** — 生成/验证/追踪配置

### 启动方式

入口文件：`apps/platform/src/odp_platform/webui/app.py`

核心函数：`create_app()` → 返回 `gr.Blocks` 对象 → 启动应使用 `main()`

```bash
conda activate odp-gpu
cd F:\python_projects\class\ODPlatform
python apps\platform\src\odp_platform\webui\app.py
```

> ⚠️ **不要**用 `create_app().launch()` 方式启动——`main()` 中传了 `allowed_paths=[str(ASSETS_DIR)]`，缺少此参数会导致壁纸 PNG 等静态资源无法加载，液态玻璃效果完全失效。

---

## 七、Git 工作流

### 远程仓库

```
origin  https://github.com/wuwo1979/ODPlatform.git
```

### 分支策略

- `main` — 主分支，稳定的可发布版本
- `pr/<number>` — PR 测试分支（`git fetch origin pull/<id>/head:pr/<id>`）
- 功能开发在 fork 仓库中完成，通过 PR 提交

### 拉取 PR 测试

```bash
git fetch origin pull/<PR编号>/head:pr/<PR编号>
git checkout pr/<PR编号>
# 测试完成后切回 main
git checkout main
```

### 一致性验证（本地 vs GitHub）

每次操作前建议确认本地与远程一致：

```bash
git fetch origin main         # 拉取最新远程状态
git diff HEAD origin/main     # 对比本地和远程差异
# 无输出 = 完全一致
git status                    # 确认 working tree clean
```

如果发现不一致，先 `git pull origin main` 同步，再继续操作。

### 提交规范

用中文写 commit message，清晰描述改动内容。不要用英文/Chinglish。

### 已知历史问题：2026-05-24 本地 .git 重建事件

> **背景**：首次 PR #1 合并后，AI 执行 `git rebase origin/main` 失败，导致本地 `.git` 目录丢失。
>
> **恢复方式**：`git init` → `git remote add origin` → `git fetch origin main` → `git branch main origin/main` → `git checkout -f main`
>
> **验证**：`git diff HEAD origin/main` 输出为空（完全一致）。本地 `main` 与远程 `origin/main` 完全同步，149 个文件全量跟踪。`.gitignore` 正常生效。
>
> **影响**：本地 `pr/<编号>` 分支丢失（PR 已合并则不需要）。未来 PR 测试时重新 `git fetch origin pull/<id>/head:pr/<id>` 即可。

---

## 八、测试

```bash
# 运行所有测试
cd apps\platform\src
python -m pytest tests -v

# 运行单元测试
python -m pytest tests -v -m unit

# 运行集成测试
python -m pytest tests -v -m integration
```

测试框架：pytest
测试目录：
- `apps/platform/src/tests/` — 主测试目录（按子系统分）
- `tests/` — 顶层集成测试

---

## 九、代码质量工具

```bash
# Lint（ruff）
ruff check apps/platform/src/

# 类型检查（mypy）
mypy apps/platform/src/

# 格式化
ruff format apps/platform/src/
```

配置在顶层 `pyproject.toml` 的 `[tool.ruff]` 和 `[tool.mypy]` 中。

---

## 十、关键架构决策（ADR）

所有 ADR 记录在 `docs/architecture/`：

| ADR | 内容 |
|-----|------|
| ADR-001 | Monorepo 结构 |
| ADR-002 | 数据管线设计 |
| ADR-002-paths | 路径策略 |
| ADR-003 | 命名规范 |
| ADR-004 | 数据校验子系统 |
| ADR-013 | 运行配置子系统（field 注册表） |

核心设计理念：
- **路径中心化**：所有路径统一在 `common/paths.py` 管理
- **注册表模式**：数据格式（`@register`）、校验检查器（`@check`）、配置字段（`@config_field`）都通过装饰器注册
- **不可变快照**：数据校验时先拍快照，保证分析一致性

---

## 十一、AI 首次启动 Checklist

当新 AI 启动来接手此项目时，请按以下顺序操作：

1. 读此文档（`docs/ODPlatform_AI接手指南.md`）
2. 激活 conda 环境：`conda activate odp-gpu`
3. 查看当前分支：`git branch`
4. 如果需要 PR 测试：`git fetch origin pull/<id>/head:pr/<id> && git checkout pr/<id>`
5. 如有依赖变更：`pip install -e ./apps/platform --force-reinstall --no-deps`
6. 查看项目根目录结构：`ls F:\python_projects\class\ODPlatform`
7. 所有 CLI 命令在项目根目录执行

---

## 十二、常见注意事项

1. **路径问题**：所有命令在项目根目录执行，不是 `apps/platform/src`，不是 `apps/platform`
2. **虚拟环境**：任何时候都使用 `odp-gpu`，不要用全局 Python
3. **不要修改别人的代码**：PR 代码保持原样，兼容问题先确认再改
4. **数据集路径**：自动由 `paths.py` 管理，手动配置用 `odp_meta.dataset` 字段
5. **日志**：运行时日志在 `apps/platform/logging/webui/` 下，按时间命名
6. **版本号**：在 `_version.py` 中维护（`__version__ = "0.1.0"`）

---

## 十三、⚠️ 重大变更：双层架构（2026-05-26）

### 架构变更

从原来的「Gradio WebUI + FastAPI（实验管理）」改为：

```
用户（浏览器）
    │
    ▼
Streamlit Web 前端（apps/web-frontend/app.py）
    │  ┌─ 用户层（默认）：图像检测 / 检测结果 / 模型选择 / LLM对话 / 用户信息
    │  └─ 管理员层（⚙️密码0000）：工作台 / 训练 / 校验 / 配置 / 数据浏览 / 模型演示
    │
    ▼
FastAPI 后端（apps/web-backend/main.py）
    │  /api/v1/auth/*          — 登录注册
    │  /api/v1/detection/*     — 检测任务
    │  /api/v1/models/*        — 模型管理
    │  /api/v1/llm/*           — LLM 对话透传
    │  /api/v1/users/*         — 用户信息
    │  /api/experiments/*      — 实验管理（原有，保留）
    │
    ▼
odp_platform 核心层（不变）
    ├── training/              # ← PR #3 新增（experiment/recipe/callbacks/tracker）
    ├── cli/train.py           # odp-train CLI
    ├── data_pipeline/         # D3 数据转换
    ├── data_validation/       # D4 数据校验
    ├── run_config/            # D5 配置管理
    └── webui/                 # Gradio WebUI（管理员层 import 使用）
```

### 新增目录

```
apps/
├── web-backend/          # FastAPI 后端（新）
│   ├── main.py
│   ├── api/auth.py, detection.py, llm.py, models_api.py, users_api.py
│   └── db/init_db.py
├── web-frontend/         # Streamlit 前端（新）
│   ├── app.py
│   ├── pages/user/page_detection.py, page_results.py, page_models.py, page_llm.py, page_profile.py
│   └── api/client.py
└── platform/             # 核心层（原有，不变）
```

### 一键启动（项目根目录）

```bash
# 方式 1：Python 脚本
python launch.py

# 方式 2：双击批处理
start.bat
```

两个脚本在 `launch.py` 和 `start.bat`，已存在项目根目录。

---

## 十四、PR #3 代码审查记录（2026-05-26）

### PR 信息

- 来源：`XDPoist` 的 fork
- 分支名：`pr-3`
- 标题：`feat: add training experiment infrastructure`
- 文件数：5 个，共 2198 行新增
- 位置：`apps/platform/src/odp_platform/training/`

### 文件清单

| 文件 | 行数 | 功能 |
|------|------|------|
| `training/__init__.py` | 0 | 空包文件 |
| `training/experiment.py` | 616 | 实验配置 + 运行入口 + 结果解析 |
| `training/recipe.py` | 377 | 预置实验模板（RSOD/VisDrone baseline + sweep） |
| `training/callbacks.py` | 609 | 回调系统（EarlyStopping + Checkpoint + 后端通信） |
| `training/tracker.py` | 596 | 实验结果收集 + CSV 对比导出 |

### 依赖项

- `odp_platform.common.paths` → 已有 ✅
- `odp_platform.common.logging_utils` → 已有 ✅
- `odp_platform.training.hooks` → **不存在**（用 `try/except` 安全降级）✅
- `requests`（callbacks.py 向后端发 HTTP）→ 标准库外，需安装
- `odp-train` CLI（experiment.py 通过 subprocess 调用）→ **已有**（`cli/train.py`）

### 审查结论

代码质量良好，无阻塞性问题。建议：

1. **补充 `hooks.py`**（可选）或保持 `try/except` 降级现状
2. 确保 `requests` 在依赖中
3. 数据集的 `rsod`/`visdrone` 需重新下载后才能跑通完整实验

### 合并状态

**尚未合并到 main**（用户正在决定中）。当前 `main` 分支不包含 training/ 目录。

---

## 十五、本地环境关键信息（2026-05-26 快照）

### 数据集状态

| 数据集 | 状态 | 操作 |
|--------|------|------|
| `rsod` | ❌ **丢失**（需重新下载） | `odp-transform --dataset rsod --format pascal_voc` |
| `visdrone` | ❌ **丢失**（需重新下载） | 需先准备原始数据到 `data/raw/visdrone/` |
| 其他测试集 | ❌ **丢失** | 需重新准备 |

### Git 状态

| 项目 | 值 |
|------|-----|
| 当前分支 | `main` |
| 远程 | `origin https://github.com/wuwo1979/ODPlatform.git` |
| 本地 vs 远程 | `git diff HEAD origin/main` 应为空 |
| 未跟踪文件 | `launch.py`, `start.bat` |

### Conda 环境

```
环境名：odp-gpu
Python：3.10+
路径：E:\Anaconda\envs\odp-gpu\
```

---

## 十六、⚠️ 血泪教训：git checkout PR 分支会删文件

### 问题现象

2026-05-26 执行 `git checkout pr-3` 后，以下文件被删除：
- `docs/` 全部文档
- `apps/platform/configs/` 全部配置
- `apps/platform/src/odp_platform/data_pipeline/`、`run_config/`、`data_validation/` 等
- `data/` 下的数据集文件（**不可恢复**，因为不在 git 跟踪中）

### 原因

`pr-3` 分支**只包含 5 个 training 文件**。切过去时，git 把工作目录中所有不属于 pr-3 的文件删掉了。

### 恢复方法

```bash
# 立即切回 main
git checkout main
# 强制执行 restore
git restore .
```

### 预防措施

**永远不要**用 `git checkout pr-<编号>` 切分支。改用：

```bash
# ✅ 安全做法：只提取 PR 代码查看
git fetch origin pull/3/head:pr-3
git diff main...pr-3 --stat         # 只看变更统计
git diff main...pr-3 -- file/path   # 只看某个文件
git show pr-3:path/to/file          # 查看单个文件内容

# 如果要真正切过去，先 stash 或备份
git stash
git checkout pr-3
# 看完了立刻
git checkout main
git stash pop
```

---

## 十七、待办事项（下一次 AI 会话）

### 优先级 P0：恢复数据集

```bash
conda activate odp-gpu
cd F:\python_projects\class\ODPlatform

# 下载 rsod 原始数据到 data/raw/rsod/
# 然后：
odp-transform --dataset rsod --format pascal_voc
odp-validate --dataset rsod
```

### 优先级 P1：PR #3 决策

- 审阅代码 ✅（已做）
- 决定是否合并到 main
- 如合并：`git merge pr-3`
- 验证：`python -c "from odp_platform.training.experiment import ExperimentConfig; print('OK')"`

### 优先级 P2：启动脚本 → exe 打包

```bash
# 用 PyInstaller 把 launch.py 打包为 exe
pip install pyinstaller
pyinstaller --onefile --console launch.py -n ODPlatform
```

### 优先级 P3：双层架构联调

- 后端 5 个 API（auth/detection/models/llm/users）
- 前端 5 个用户 Tab + 管理员层 import 已有 webui
- 确认一键启动 `python launch.py` 能正常工作