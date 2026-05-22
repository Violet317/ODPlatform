# ODPlatform 团队分工与协作指南

> 6 人小团队，轻量协作，聚焦功能落地。

---

## 一、分工与目标

### 模型训练工程师

**负责**：训练流程搭建、数据集导入、超参调试、模型保存。

- [ ] 搭建训练流水线，支持 YOLO 一键训练
- [ ] 支持多数据集切换（RSOD / VisDrone / VOC）
- [ ] 实现自动超参搜索（Grid Search）
- [ ] 训练日志记录与可视化
- [ ] 模型导出（ONNX / TensorRT）

### 算法优化工程师

**负责**：网络结构改进、损失函数调优、消融实验。

- [ ] Baseline 复现与精度验证
- [ ] 引入注意力机制 / 改进 Neck
- [ ] 损失函数对比实验（CIoU / SIoU / Focal）
- [ ] 数据增强参数调优
- [ ] 输出实验对比报告

### UI & 前端工程师

**负责**：界面设计、页面布局、可视化交互。

- [ ] Gradio UI 布局优化与主题统一
- [ ] 训练进度实时曲线展示
- [ ] 数据集统计图表（类别分布、标注数量）
- [ ] 推理结果展示增强（批量上传、对比视图）
- [ ] 响应式适配

### 数据库 & 后端接口工程师

**负责**：数据库设计、REST API 开发、数据持久化。

- [ ] 数据库表设计（实验记录、训练日志、模型元信息）
- [ ] FastAPI 后端搭建
- [ ] 实验 CRUD 接口
- [ ] 训练进度实时写入接口
- [ ] Swagger API 文档

### 推理与可视化工程师

**负责**：模型推理封装、图片/视频检测、结果可视化。

- [ ] 统一推理接口封装 `Detector.predict(image) -> List[Box]`
- [ ] 支持图片、视频文件、摄像头实时检测
- [ ] 检测结果画框 + 标置信度
- [ ] 推理性能优化（FP16 / TensorRT）
- [ ] 批量推理 CLI 工具

### 项目架构工程师

**负责**：项目架构设计、代码规范、模块集成、进度统筹。

- [ ] Git 仓库管理与分支策略
- [ ] 代码审查与规范落地
- [ ] 模块接口协调与集成
- [ ] CI 搭建（自动测试+代码检查）
- [ ] 版本管理与发布

---

## 二、Git 协作方式

### 分支策略

```
main              ← 稳定分支，保护起来
  ├── feat/training
  ├── feat/algorithm
  ├── feat/frontend
  ├── feat/backend
  └── feat/inference
```

### 流程

1. 每人从 `main` 拉自己的 `feat/xxx` 分支
2. 完成后提 Pull Request
3. 架构师审查代码 → 合并到 `main`
4. 定期各分支同步 `main` 的更新

### 提交规范

```
feat: 添加XX功能
fix: 修复XX问题
refactor: 重构XX模块
test: 添加XX测试
```

---

## 三、模块间约定

| 约定 | 说明 |
|---|---|
| 路径不走硬编码 | 从 `common/paths.py` 获取 |
| 常量不走字面量 | 从 `common/constants.py` 取 |
| 日志用 logger | `logging.getLogger(__name__)`，不用 print |
| data/ 不纳入 Git | 运行时目录，各人本地放 |
| 新增模块不破坏现有 | 扩展不走改核心 |

### 各人不能动什么

| 模块 | 谁可改 | 原因 |
|---|---|---|
| `common/` | 仅架构师 | 全项目依赖 |
| `data_pipeline/` | 暂不改 | D3 已稳定 |
| `data_validation/` | 暂不改 | D4 已稳定 |
| `webui/` | UI 工程师 | 前端 |
| `training/`（新建） | 训练 + 算法 | 实验代码 |
| `inference/`（新建） | 推理工程师 | 独立模块 |
| `web-backend/`（新建） | 后端工程师 | 独立模块 |

---

## 四、开发节奏

| 阶段 | 目标 |
|---|---|
| **第 1 周** 基建 | 仓库就绪，每人搭好环境，模块骨架跑通 |
| **第 2-3 周** 核心功能 | 各模块核心功能可用 |
| **第 4 周** 联调 | 全链路打通：训练 → 导出 → 推理 → 展示 |
| **第 5 周** 完善 | 文档、测试、部署 |

---

## 五、快速开始

```bash
git clone https://github.com/wuwo1979/ODPlatform.git
cd ODPlatform
git checkout -b feat/xxx          # 按角色创建分支
pip install -e ./apps/platform
odp-init                          # 验证环境
python scripts/odp-dashboard.py   # 启动 UI
```