# ADR-001: Monorepo 项目结构

## 状态
已接受

## 背景
ODPlatform 项目包含多个端（platform、web、mobile 等）、共享库和文档。
我们需要决定采用 Monorepo（单仓库）还是 Polyrepo（多仓库）方案。

## 决策
选择 **Monorepo** 结构，原因如下：

| 因素 | Monorepo | Polyrepo |
|------|----------|----------|
| 跨模块重构 | 一次 PR 完成 | 多次 PR，跨仓库协调 |
| 依赖管理 | 统一版本，无冲突 | 版本可能漂移 |
| 代码复用 | 共享模块即时可见 | 需发布包 + 更新依赖 |
| 教学/新手友好 | 一个仓库，结构清晰 | 多个仓库，理解成本高 |
| CI/CD | 一次构建所有 | 构建矩阵复杂度高 |

## 关键文件
```
ODPlatform/
├── apps/                      # 各端代码
│   ├── platform/              # 目标检测引擎（主端）
│   │   ├── pyproject.toml     # 可发布的子包配置
│   │   └── src/odp_platform/  # Python 源码
│   ├── web/                   # Web 前端（未来）
│   └── mobile/                # 移动端（未来）
├── packages/                  # 共享库
├── pyproject.toml              # 顶层 workspace 工具配置
├── .odp-workspace             # workspace 根标记
└── docs/                      # 统一文档
```

## 约定
1. 每个 `apps/*` 子目录是一个独立的 Python 包，有自己的 `pyproject.toml`
2. 顶层 `pyproject.toml` 只放开发工具（ruff / mypy / pytest）配置
3. 大文件（数据集、模型权重）通过 `.gitignore` 忽略
4. 共享代码放在 `packages/` 下

## 影响
- 所有代码在一个仓库中，开发体验统一
- 需注意 `.gitignore` 正确配置，避免大文件进入版本控制