# D2 深度补充：performance_utils.py 与 pyproject.toml 完全指南

> **配套**：D2 文档 阶段 9 + 阶段 11
>
> **文档目标**：把这两块原文档"一笔带过"的内容讲透——
> 1. **performance_utils.py 为什么需要？**装饰器的底层机制是什么？工业界怎么用？
> 2. **pyproject.toml 到底是什么？**为什么有两层？每一个字段什么意思？哪些必须哪些可选？企业常见配置长什么样？

---

# 第一部分：performance_utils.py 深度解析

## 一、为什么需要性能测量工具？

### 1.1 真实场景的痛点

让我们假设几个真实开发场景，看看"没有性能工具"会有多痛苦：

#### 场景 A：训练突然变慢了

你的 YOLO 训练脚本上周一个 epoch 跑 5 分钟，这周突然要 8 分钟。**你怎么定位变慢的环节？**

如果代码里没有任何"耗时记录"，你只能：

```python
# 在每个可疑的地方手动加 print
import time

start = time.time()
images = load_dataset(...)
print(f"加载数据: {time.time() - start}s")  # 加一次

start = time.time()
augmented = augment(images)
print(f"数据增强: {time.time() - start}s")  # 又加一次

start = time.time()
loss = model(augmented)
print(f"前向: {time.time() - start}s")     # 再加一次

# ... 加了 20 处
```

**问题来了**：

1. **代码污染严重**——业务逻辑被 timing 代码淹没
2. **改完忘删**——上线了一堆调试 print
3. **不一致**——有的用 `time.time()`，有的用 `time.perf_counter()`，有的没小数位
4. **不能开关**——想关掉就只能注释，下次又要加回来
5. **没有平均值**——某次特别快/特别慢都看不出来是不是异常

#### 场景 B：算法选型对比

要在两种数据增强算法里选一个，需要测它们的速度。

```python
# 方法 1
start = time.time()
for _ in range(1000):
    augment_v1(image)
print(f"v1 平均: {(time.time() - start) / 1000}s")

# 方法 2
start = time.time()
for _ in range(1000):
    augment_v2(image)
print(f"v2 平均: {(time.time() - start) / 1000}s")
```

**痛点**：每次对比新算法都要重写这段循环代码——重复劳动。

#### 场景 C：上线后的 SLA 监控

服务上线了，用户反馈"推理接口偶尔很慢"。你需要长期记录每次推理的耗时，找规律。

如果代码里没有规范的耗时记录机制，事后加埋点要改 N 个文件，且容易加得不一致。

### 1.2 工业界的标准做法：装饰器

工业界对"测量函数耗时"这个需求的标准答案是 **装饰器(Decorator)**：

```python
@time_it()
def expensive_function():
    # 业务代码,完全不用关心 timing
    ...
```

**为什么装饰器是标准答案？**

| 需求 | 装饰器如何满足 |
|---|---|
| 不污染业务代码 | timing 逻辑封装在装饰器里,业务函数本身一行不变 |
| 一处定义,处处使用 | 写一次装饰器,所有函数 `@time_it()` 即可 |
| 可开关 | 测试时加 `@time_it()`,生产环境改成 `@no_op` 即可关闭 |
| 一致性 | 所有用了装饰器的函数,输出格式完全一致 |
| 可扩展 | 装饰器可以传参(迭代次数、自定义名字、日志输出) |

### 1.3 为什么不直接用 Python 自带的工具？

你可能会问：Python 有 `cProfile`、`timeit`，为什么还要自己写?

**答案：不同工具的定位不同**。

| 工具 | 定位 | 优点 | 缺点 |
|---|---|---|---|
| `time.time()` 手写 | 临时测一次 | 简单 | 重复劳动、污染代码 |
| `timeit` 模块 | 微基准测试 | 精确,自动多次运行 | 仅适合小代码段,不适合在生产代码里用 |
| `cProfile` | 全局性能剖析 | 详尽 | 输出复杂,生产环境开销大 |
| `@time_it()` 自定义装饰器 | **生产代码常驻 timing** | 优雅集成,可开关,可定制 | 需要自己实现 |

`timeit` 和 `cProfile` 是**研究工具**——临时跑一下分析问题。`@time_it()` 是**产品工具**——长期住在代码里,定期产出耗时报告,服务于持续监控。

**所以两者并不冲突**:

- 怀疑某段代码慢? → 临时用 `cProfile` 深入剖析
- 想长期监控关键路径耗时? → 业务代码里加 `@time_it()`

## 二、装饰器机制：从零理解 `@time_it()` 怎么 work

如果你对装饰器机制还不熟悉,这一节会从零讲起。如果熟悉,可以跳到下一节。

### 2.1 函数是"一等公民"

Python 里函数和数字、字符串一样,是可以**赋值、传递、返回**的对象:

```python
def hello():
    print("hi")

# 函数可以赋值
my_func = hello
my_func()  # 输出 "hi"

# 函数可以作为参数传递
def call_twice(f):
    f()
    f()
call_twice(hello)  # 输出两次 "hi"

# 函数可以作为返回值
def make_greeter():
    def greet():
        print("hello!")
    return greet

greeter = make_greeter()
greeter()  # 输出 "hello!"
```

**这三个特性合起来**,就是装饰器的全部基础。

### 2.2 装饰器的本质：包一层壳

装饰器干的事就一句话:**接收一个函数,返回一个新函数,新函数在调用原函数前后做一些额外的事**。

最简版本:

```python
def my_decorator(func):
    def wrapper():
        print("调用前")
        func()           # 调用原函数
        print("调用后")
    return wrapper       # 返回新函数

@my_decorator
def say_hi():
    print("hi")

say_hi()
# 输出:
# 调用前
# hi
# 调用后
```

`@my_decorator` 这个语法等价于:

```python
say_hi = my_decorator(say_hi)
```

也就是说,`say_hi` 这个名字现在指向的是 `wrapper` 函数,不再是原来的 `say_hi`。每次调用 `say_hi()`,实际执行的是 `wrapper()`。

### 2.3 我们的 `@time_it()` 多了什么?

`@time_it()` 比上面那个最简版本复杂一点点,因为:

1. **它带括号`()`**——意味着 time_it 本身是一个"工厂",调用它返回真正的装饰器
2. **它要支持任意参数的函数**——所以 `wrapper` 写成 `(*args, **kwargs)`
3. **它要保留原函数的元数据**——所以用 `@functools.wraps(func)`

完整版本逐行解释:

```python
def time_it(iterations=1, name=None, logger_instance=None):
    # ↑ 这是【装饰器工厂】——它接收【装饰器的配置参数】,返回【真正的装饰器】
    
    def decorator(func):
        # ↑ 这是【真正的装饰器】——它接收【被装饰的函数】,返回【新函数】
        
        @wraps(func)
        # ↑ 让 wrapper "伪装"成 func,保留 func.__name__、func.__doc__ 等元数据
        # 这样 print(my_func.__name__) 还能打印出原函数名,而不是 "wrapper"
        
        def wrapper(*args, **kwargs):
            # ↑ 这是【新函数】——它会代替原函数被调用
            # *args, **kwargs 让它能接受任意参数(以适配任意被装饰的函数)
            
            # === 调用原函数前: 准备 timing ===
            display_name = name if name is not None else func.__name__
            total = 0.0
            
            # === 多次调用以求平均 ===
            for _ in range(iterations):
                start = time.perf_counter()
                result = func(*args, **kwargs)  # ← 真正调用原函数
                end = time.perf_counter()
                total += (end - start)
            
            # === 调用后: 输出结果 ===
            avg = total / iterations
            logger.info(f"性能报告: '{display_name}' 平均耗时: {format(avg)}")
            
            return result  # ← 把原函数的返回值传回去
        
        return wrapper
    
    return decorator
```

### 2.4 三层嵌套是怎么对应使用方式的

这是初学者最容易绕晕的地方。让我们把"使用"和"定义"对应起来看:

```python
# 你写的代码:
@time_it(iterations=10, name="推理")
def my_inference(image):
    return model(image)

result = my_inference(some_image)
```

执行过程拆解:

```
第 1 步: time_it(iterations=10, name="推理")
        ↓
        time_it 函数被调用,iterations=10, name="推理"
        ↓
        time_it 返回内部的 decorator 函数
        ↓
        我们暂且叫它 decorator_with_args

第 2 步: @decorator_with_args  应用到  my_inference 上
        ↓ 等价于
        my_inference = decorator_with_args(my_inference)
        ↓
        decorator_with_args 调用 wrapper 闭包,捕获 my_inference 引用
        ↓
        my_inference 这个名字现在指向 wrapper 函数

第 3 步: result = my_inference(some_image)
        ↓ 实际执行
        result = wrapper(some_image)
        ↓
        wrapper 内部循环 10 次调用真正的 my_inference(some_image)
        ↓
        计算平均耗时,打印日志
        ↓
        返回最后一次的 result
```

### 2.5 几个细节点

#### `time.perf_counter()` vs `time.time()`

我们用的是 `time.perf_counter()` 而不是 `time.time()`。区别:

| 函数 | 测量精度 | 适合场景 |
|---|---|---|
| `time.time()` | 通常毫秒级 | 获取"现在是几点几分"的真实时间 |
| `time.perf_counter()` | 纳秒级 | 测量"过了多久" |

测耗时**永远用 `time.perf_counter()`**——它是 Python 官方推荐的"性能测量计时器",不会受系统时间调整(比如 NTP 同步)影响。

#### 单位自动切换

我们的 `_format_time_auto_unit` 函数会根据耗时大小自动选择单位:

```python
0.0001 秒 → "0.100 毫秒"
0.5 秒    → "500.000 毫秒"  
30 秒     → "30.00 秒"
300 秒    → "5 分钟 0.00 秒"
```

为什么这么做?**因为人类对数字的感觉是有"舒适区"的**:

- "0.000123 秒" 不如 "123 微秒" 直观
- "3823.5 秒" 不如 "1 小时 3 分钟 43 秒" 直观

让数字落在 1-1000 区间内,人最容易快速理解。

## 三、@time_it 的进阶用法

### 3.1 在我们项目里的实际用法

D2 课程的 `init_project.py` 用了这样:

```python
@time_it(iterations=1, name="项目初始化", logger_instance=logger)
def initialize_project() -> None:
    # ...
```

**参数解释**:

- `iterations=1`: 只跑一次(初始化是不可重复的操作,多跑没意义)
- `name="项目初始化"`: 自定义显示名,比函数名 `initialize_project` 更友好
- `logger_instance=logger`: 用项目自己的彩色 logger,而不是装饰器内置的简陋 logger

输出效果:

```
2026-05-06 14:30:01 [INFO ] init_project.py │ 性能报告: '项目初始化' 执行耗时: 23.451 毫秒
```

### 3.2 实战场景示例

#### 场景 1: 推理批次性能测试

```python
@time_it(iterations=100, name="单图推理")
def infer_one(image):
    return model(image)

# 第一次调用,自动跑 100 次,输出平均耗时
infer_one(test_image)
```

输出:

```
性能报告: '单图推理' 执行 100 次 | 总耗时: 5.20 秒 | 平均耗时: 52.000 毫秒
```

#### 场景 2: 不同实现对比

```python
@time_it(iterations=1000, name="算法 A")
def algorithm_a(data):
    return sorted(data)

@time_it(iterations=1000, name="算法 B")
def algorithm_b(data):
    return list(set(data))

algorithm_a(test_data)
algorithm_b(test_data)
```

输出立刻能对比两种算法的耗时。

#### 场景 3: 训练循环里的关键路径监控

```python
@time_it(name="数据加载", logger_instance=train_logger)
def load_batch(loader):
    return next(iter(loader))

@time_it(name="前向", logger_instance=train_logger)
def forward(model, batch):
    return model(batch)

@time_it(name="反向", logger_instance=train_logger)
def backward(loss):
    loss.backward()
```

训练日志里会持续记录每个环节的耗时——出问题时能立刻定位是哪一步变慢了。

### 3.3 装饰器的几种"开关"姿势

工业界生产环境,经常需要"开发时开启,生产时关闭"性能监控。几种常见做法:

#### 做法 1: 通过环境变量

```python
import os

ENABLE_TIMING = os.environ.get("ENABLE_TIMING", "0") == "1"

def time_it(iterations=1, name=None, logger_instance=None):
    if not ENABLE_TIMING:
        # 生产环境直接返回原函数,无任何 overhead
        return lambda func: func
    
    # ... 原本的装饰器逻辑
```

开发环境 `ENABLE_TIMING=1 python xxx.py` 启用,生产环境不设这个变量就自动关闭。

#### 做法 2: 通过日志级别

把装饰器输出改成 `logger.debug(...)`,然后通过日志级别控制——开发环境 DEBUG 级别能看到,生产环境 INFO 级别自动隐藏。

#### 做法 3: 采样

每 N 次调用才记录一次,降低对性能的影响:

```python
def time_it(sample_rate=1.0, ...):
    counter = [0]
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            counter[0] += 1
            if counter[0] % int(1/sample_rate) != 0:
                # 跳过 timing,直接调用
                return func(*args, **kwargs)
            # 正常 timing 流程
            # ...
```

这是大型分布式系统里的标准做法——**每个请求都测会拖慢系统,采样测就够用了**。

## 四、为什么 performance_utils 是"基础设施"

回到 D2 课程的核心叙事——**performance_utils 不是某个业务模块的专属工具,而是【全项目通用】的基础设施**。

它会被这些模块用到:

```
common/performance_utils.py
   ↓ 提供 @time_it
   ↓
   ├──→ cli/init_project.py    (测项目初始化耗时)
   ├──→ training/train.py      (测训练循环各阶段耗时)
   ├──→ inference/infer.py     (测推理耗时)
   ├──→ data_converter/...     (测数据转换耗时)
   └──→ evaluation/...         (测评估耗时)
```

**写一次,处处复用——这就是 common/ 层的根本价值**。

> 💡 **金句**: "好的基础设施工具,定义在【一个】地方,使用在【一百个】地方。"

---

# 第二部分:pyproject.toml 完全指南

## 一、pyproject.toml 是什么? 为什么有它?

### 1.1 一段历史:Python 打包的混乱年代

要理解 pyproject.toml,先要理解它**取代了什么**。

#### 远古时期(2000-2015): setup.py 一统天下

最早,Python 项目的"打包配置"全写在 `setup.py` 里:

```python
# setup.py
from setuptools import setup

setup(
    name="my-package",
    version="1.0.0",
    install_requires=["numpy>=1.20"],
    # ...
)
```

跑 `python setup.py install` 就能装。

**问题**:
1. **它是 Python 代码**——意味着安装包的过程要"先执行任意代码",有安全风险
2. **配置和代码混在一起**——工具想读这些信息,只能解析 Python 代码
3. **只支持 setuptools 一个打包工具**——其他打包工具(poetry、flit、hatch)只能各搞一套

#### 中古时期(2015-2020): 配置爆炸

为了解决 setup.py 的问题,各种配置文件冒出来:

- `setup.cfg` —— setuptools 的 INI 格式配置
- `requirements.txt` —— 依赖列表
- `MANIFEST.in` —— 控制打包内容
- `tox.ini` —— 测试配置
- `.flake8` —— 代码风格配置
- `mypy.ini` —— 类型检查配置
- `pytest.ini` —— 测试框架配置
- ...

**一个项目根目录下散落着十几个配置文件**——又乱又难维护。

#### 现代(2020+): pyproject.toml 统一

PEP 518(2016)和 PEP 621(2020)规范了一种新方案:

> **所有 Python 项目配置,统一写在一个文件里:`pyproject.toml`。**

它:
1. **是 TOML 格式,不是 Python 代码**——工具能直接解析,无需执行,安全
2. **由 PEP 标准化**——所有打包工具(setuptools/poetry/flit/hatch/PDM)都支持
3. **能容纳所有工具的配置**——pytest/mypy/ruff/black 等都能在 `[tool.xxx]` 段里配置

**现在 2026 年,新建 Python 项目都应该用 pyproject.toml**。setup.py 仍然能用,但已经被官方建议**只在有特殊编译需求时使用**(比如包含 C 扩展)。

### 1.2 它解决了什么问题

```
没有 pyproject.toml:                有了 pyproject.toml:
─────────────────────              ──────────────────────
setup.py                           pyproject.toml  ← 一个文件
setup.cfg                          
requirements.txt                   (其他配置都在 [tool.xxx] 段里)
MANIFEST.in                        
.flake8                            
mypy.ini                           
pytest.ini                         
.coveragerc                        
tox.ini                            
```

**直观感受**: 项目根目录从一团乱麻 → 一个干净的配置文件。

## 二、pyproject.toml 的整体结构

一个完整的 pyproject.toml 由这几个"顶级段"组成:

```toml
[build-system]
# 必须项:告诉 pip "用什么工具来构建这个包"
# 例如:setuptools / poetry / flit / hatchling

[project]
# 项目元信息:名字、版本、依赖、作者等
# PEP 621 标准格式,所有工具通用

[project.scripts]
# 命令行入口点:让 pip install 后能注册命令(如 odp-init)

[project.optional-dependencies]
# 可选依赖组:dev/test/docs 等

[tool.setuptools]
# setuptools 特有的配置(包路径、版本来源等)

[tool.ruff]
# ruff 这个 linter 的配置

[tool.mypy]
# mypy 类型检查器的配置

[tool.pytest.ini_options]
# pytest 的配置

# 还可以有 [tool.black]、[tool.isort]、[tool.coverage] ...
```

**两个核心命名空间**:

| 命名空间 | 谁定义 | 作用 |
|---|---|---|
| `[build-system]` `[project]` `[project.xxx]` | **PEP 标准定义** | 所有 Python 工具都能识别 |
| `[tool.xxx]` | **各工具自己定义** | 每个工具读自己的那一段,不读别人的 |

## 三、ODPlatform 的 apps/platform/pyproject.toml 逐字段解析

让我们把 D2 课程里的 platform 子项目 pyproject.toml,**一段一段**讲清楚。

### 3.1 `[build-system]` —— 必填,告诉 pip 用什么工具构建

```toml
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"
```

#### 逐字段解析

**`requires`**: 构建这个包**本身需要哪些工具**

- 这不是项目的运行依赖,是**构建依赖**
- pip 会先在隔离环境里装这些工具,再用它们来打包项目
- `setuptools>=61.0`: PEP 621 支持是 setuptools 61+ 引入的
- `wheel`: 用来生成 .whl 文件(pip 安装的标准格式)

**`build-backend`**: 用哪个工具的"打包后端"

- `setuptools.build_meta` = 用 setuptools 的现代构建后端
- 备选: `poetry.core.masonry.api`(poetry)、`hatchling.build`(hatch)、`flit_core.buildapi`(flit)

#### 不同打包工具对比

| 打包工具 | build-system 配置 | 风格 |
|---|---|---|
| **setuptools** | `setuptools.build_meta` | 经典,兼容性最好 |
| **poetry** | `poetry.core.masonry.api` | 一体化(包管理+构建+发布) |
| **hatchling** | `hatchling.build` | 现代,PyPA 推荐 |
| **flit** | `flit_core.buildapi` | 简洁,适合纯 Python 包 |
| **pdm** | `pdm.backend` | 快速 |

**ODPlatform 用 setuptools 的原因**:

- 兼容性最好,几乎所有 Python 教程都基于它
- 生态成熟,问题搜得到答案
- 性能不是教学项目的关键指标

**实际生产中的选择**:
- 内部项目: setuptools(够用) 或 hatchling(更现代)
- 发布到 PyPI 的库: hatchling 或 flit(更轻量)
- 应用项目(网站后端): poetry(有锁文件,部署可重现)

#### 这一段是必须的吗?

**是的,绝对必须**。没有 `[build-system]` 段,pip 不知道用什么工具来构建你的包,会直接报错。

### 3.2 `[project]` —— 项目元信息

```toml
[project]
name = "odp-platform"
dynamic = ["version"]
description = "ODPlatform - 目标检测开发平台核心引擎"
readme = "README.md"
requires-python = ">=3.10"
license = { text = "MIT" }
authors = [
    { name = "ODPlatform Team" },
]
keywords = ["object-detection", "yolo", "deep-learning", "ml-platform"]
```

这些字段都是 **PEP 621 标准定义的**,所有工具通用。

#### 必填字段(只有一个!)

| 字段 | 含义 | 必填? |
|---|---|---|
| `name` | 包名(在 PyPI 上的名字) | **✅ 必填** |

是的,**严格说只有 `name` 是必填的**。其他都是可选的。

但实际上 `version` 也基本是必填(要么直接写 `version = "1.0.0"`,要么像我们这样用 `dynamic = ["version"]` 动态获取)。否则 pip 不知道这是哪个版本。

#### 强烈推荐填的字段

| 字段 | 含义 | 推荐? |
|---|---|---|
| `version` 或 `dynamic = ["version"]` | 版本号 | **✅ 必备** |
| `description` | 一句话描述 | **✅ 强烈建议** |
| `readme` | README 文件路径 | **✅ 发布到 PyPI 必备** |
| `requires-python` | 支持的 Python 版本 | **✅ 强烈建议** |
| `dependencies` | 运行依赖 | **✅ 有依赖就必须填** |
| `license` | 许可证 | **✅ 公开发布必备** |
| `authors` | 作者 | **✅ 强烈建议** |

#### 锦上添花的字段

| 字段 | 含义 | 何时填 |
|---|---|---|
| `keywords` | 关键词,PyPI 搜索用 | 公开发布时填 |
| `classifiers` | 分类器(Trove classifiers) | 公开发布时填 |
| `urls` | 项目链接(主页/文档/源码) | 公开发布时填 |
| `maintainers` | 维护者 | 多人维护时填 |

#### `dynamic = ["version"]` 是什么?

```toml
dynamic = ["version"]
```

**意思**: "version 字段不在这里写死,会从其他地方动态读取——具体哪里见 `[tool.setuptools.dynamic]` 段"。

为什么要这样? 因为 D2 文档里讲过的**单一数据源原则**——版本号写在 `_version.py` 里,这里通过 dynamic 引用,Python 代码和打包配置共享一个版本号。

**对比两种写法**:

```toml
# 写法 A: 硬编码版本(简单但容易和代码不同步)
version = "0.1.0"

# 写法 B: 动态版本(我们用的,需要配合 [tool.setuptools.dynamic])
dynamic = ["version"]
```

#### `requires-python` 的作用

```toml
requires-python = ">=3.10"
```

声明这个包**需要哪个 Python 版本**才能跑。pip install 时如果当前 Python 版本不满足,会拒绝安装。

为什么我们写 `>=3.10`? 因为代码里用了 3.10 才有的语法,比如:

```python
def foo(model_name: str | None = None):  # 3.10+ 的 X | Y 联合类型
    pass
```

如果不写这个限制,Python 3.9 用户装了之后跑会报奇怪的语法错误,体验很差。

#### `license` 的几种写法

```toml
# 写法 1: 简单字符串(我们用的)
license = { text = "MIT" }

# 写法 2: 指向 LICENSE 文件
license = { file = "LICENSE" }

# 写法 3: 新版 PEP 639 的 SPDX 标识符(更现代,但需要新版工具)
license = "MIT"
```

新项目推荐写法 3(SPDX 格式),但需要 `setuptools >= 77.0` 或对应版本的其他后端。

### 3.3 `dependencies` —— 运行依赖

```toml
dependencies = [
    "colorlog>=6.7.0",
    "psutil>=5.9.0",
    "torch>=2.0.0",
    "ultralytics>=8.0.0",
    "pyyaml>=6.0",
    "pydantic>=2.0",
]
```

**这些是这个包【运行时】需要的依赖**。`pip install odp-platform` 时,pip 会自动安装这些。

#### 版本约束的写法

| 写法 | 含义 | 何时用 |
|---|---|---|
| `colorlog` | 任何版本 | 不推荐(可能装到不兼容的旧版/新版) |
| `colorlog>=6.7.0` | 至少 6.7.0 | **最常用**——保证最低能用的版本 |
| `colorlog>=6.7.0,<7.0.0` | 6.7.0 到 7.0.0 之间 | 担心 7.0 有破坏性更新时用 |
| `colorlog~=6.7.0` | 6.7.x(等价于 >=6.7.0,<6.8.0) | "兼容版本"约束 |
| `colorlog==6.7.0` | 必须正好这个版本 | **强烈不推荐**——太僵化 |

#### 应该如何选择版本约束?

**经验法则**:

1. **写最低版本要求**(`>=6.7.0`)——保证用户装到能用的版本
2. **不要写上限**(`<7.0.0`)——除非你**确定**新版有破坏性变更
3. **应用项目可以更严格**——比如 web 后端,确定的版本范围更稳定
4. **库项目要尽量宽松**——别人的项目可能有不同的依赖,你写太死会冲突

ODPlatform 现在写 `>=` 是合理的。如果未来上线生产服务,可以加锁文件(`requirements.lock`)固定具体版本。

#### dependencies 和 requirements.txt 的关系

很多老 Python 项目有 `requirements.txt`,新项目还需要它吗?

**简短回答**: 看场景。

| 场景 | 用什么 |
|---|---|
| 库(发布到 PyPI) | **只用 pyproject.toml 的 dependencies**,不要 requirements.txt |
| 应用(部署到服务器) | **dependencies 写"需要什么"** + **requirements.lock 锁定"具体哪些版本"** |
| 数据科学项目(notebook 为主) | requirements.txt 仍然常见,简单直接 |

ODPlatform 是库+应用的混合体,我们现在只用 pyproject.toml 就够了。未来部署 web-backend 时,会引入锁文件机制。

### 3.4 `[project.optional-dependencies]` —— 可选依赖组

```toml
[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-cov>=4.1.0",
    "ruff>=0.1.0",
    "mypy>=1.5.0",
]
```

**这是"分组的可选依赖"**——用户可以选择性安装。

#### 用法

```bash
# 只装运行依赖(适合最终用户)
pip install odp-platform

# 装运行依赖 + dev 组(适合开发者)
pip install odp-platform[dev]

# 装多个组(假设还有 docs 组)
pip install odp-platform[dev,docs]
```

#### 工业界常见的可选依赖组

| 组名 | 通常包含 |
|---|---|
| `dev` | 测试 + 代码质量工具(pytest/ruff/mypy/pre-commit) |
| `test` | 仅测试工具(pytest/coverage) |
| `docs` | 文档生成(sphinx/mkdocs/myst-parser) |
| `lint` | 仅 linter(ruff/black/flake8) |
| `gpu` | GPU 相关依赖(torch with CUDA) |
| `all` | 上面所有的合集 |

#### 一个常见做法:`all` 组

```toml
[project.optional-dependencies]
test = ["pytest", "pytest-cov"]
lint = ["ruff", "mypy"]
docs = ["sphinx"]
dev = [
    "odp-platform[test,lint,docs]",  # 引用其他组
    "pre-commit",                     # 加上额外的
]
```

`dev` 组通过引用 `[test,lint,docs]` 来包含所有内容——避免重复。

#### 必填吗?

**不必填**。如果你的项目没有需要"可选"的依赖,可以完全不写这一段。

### 3.5 `[project.scripts]` —— 命令行入口(关键!)

```toml
[project.scripts]
odp-init = "odp_platform.cli.init_project:initialize_project"
```

**这一行是 D2 阶段 11 的核心**——它让 `pip install` 后能在命令行用 `odp-init` 这个命令。

#### 语法

```
命令名 = "模块路径:函数名"
```

- 左边 `odp-init`: 用户在命令行输入的命令名
- 右边 `odp_platform.cli.init_project`: Python 模块路径(对应 `odp_platform/cli/init_project.py`)
- 右边 `:initialize_project`: 模块里的函数名

#### pip 在做什么?

`pip install -e ./apps/platform` 时,pip 会:

1. 读取 pyproject.toml 里的 `[project.scripts]` 段
2. 在 conda 环境的 `bin/`(Linux/macOS)或 `Scripts/`(Windows) 目录里,**生成一个小脚本**叫 `odp-init`
3. 这个小脚本的内容大致是:

```python
#!/path/to/python
import sys
from odp_platform.cli.init_project import initialize_project
sys.exit(initialize_project())
```

4. 把这个脚本设为可执行(Linux/macOS 加 +x 权限)

5. 因为 conda 环境的 bin/ 目录在 PATH 里,所以 `odp-init` 就成了能直接用的命令

#### 验证

```bash
# 装包后查看生成的命令位置
which odp-init       # Linux/macOS/Git Bash
Get-Command odp-init  # PowerShell
```

输出大概是:
- `/home/user/miniconda3/envs/odp/bin/odp-init`  (Linux)
- `C:\Users\user\miniconda3\envs\odp\Scripts\odp-init.exe`  (Windows)

#### 多个命令

可以注册多个命令:

```toml
[project.scripts]
odp-init = "odp_platform.cli.init_project:initialize_project"
odp-train = "odp_platform.cli.train:main"
odp-infer = "odp_platform.cli.infer:main"
odp-eval = "odp_platform.cli.eval:main"
```

每一行一个命令。这在大型 CLI 工具里很常见(如 `git` 有 `git status` `git push` 等子命令,但实现方式不同——这里是**多个独立命令**)。

#### 必填吗?

**不必填**。如果你的包不需要提供命令行工具(纯库),完全不用写这一段。

ODPlatform 写它是因为我们要做 `odp-init` 命令。

### 3.6 `[tool.setuptools]` —— setuptools 特有配置

```toml
[tool.setuptools]
package-dir = { "" = "src" }

[tool.setuptools.packages.find]
where = ["src"]
include = ["odp_platform*"]

[tool.setuptools.dynamic]
version = { attr = "odp_platform._version.__version__" }
```

**这一段不是 PEP 标准,而是 setuptools 自己的配置**——只有用 setuptools 作为构建后端时才有效。

#### `package-dir = { "" = "src" }`

**意思**: "所有包的根目录是 `src/`(不是项目根)"。

这就是著名的 **src/ 布局**——把 Python 代码放在 `src/` 子目录下,而不是直接放在项目根。

```
没有 src/ 布局:                有 src/ 布局:
─────────────────              ───────────────
my-project/                    my-project/
├── pyproject.toml             ├── pyproject.toml
├── tests/                     ├── tests/
└── my_package/                └── src/
    ├── __init__.py                └── my_package/
    └── main.py                        ├── __init__.py
                                       └── main.py
```

#### 为什么用 src/ 布局?

这是 PyPA(Python Packaging Authority)推荐的现代布局。**核心好处**: 强制隔离"源码"和"已安装版本"。

**没有 src/ 布局的坑**:

```
my-project/
├── my_package/         ← 源码
│   └── ...
└── tests/

# pip install -e . 后:
# my_package 同时存在于:
# - my-project/my_package/  (源码,sys.path 自动包含项目根)
# - site-packages/my_package.egg-link → my-project/my_package/

# 你 cd 到 my-project/ 跑 python,
# import my_package 拿到的是【源码版本】(因为项目根在 sys.path 第一位)
# cd 到别处跑 python,
# import my_package 拿到的是【site-packages 的链接】
# 这两个 90% 时候一样,但偶尔有不一致——非常难调试
```

**有 src/ 布局**:

```
my-project/
├── src/
│   └── my_package/     ← 源码
└── tests/

# 项目根没有 my_package/ 这个目录
# 所以"cd 到项目根 + python" 不会意外 import 到源码
# import my_package 必须通过 site-packages 的链接才能找到
# 强制了"装了才能用"的纪律
```

**ODPlatform 用 src/ 布局是对的**——这是 2026 年的现代最佳实践。

#### `[tool.setuptools.packages.find]`

```toml
[tool.setuptools.packages.find]
where = ["src"]
include = ["odp_platform*"]
```

**意思**: "去 `src/` 目录下找包,只把名字以 `odp_platform` 开头的当作包"。

`include = ["odp_platform*"]` 中的 `*` 是通配符,会匹配:
- `odp_platform`
- `odp_platform.common`
- `odp_platform.cli`
- 任何子包

#### `[tool.setuptools.dynamic]`

```toml
[tool.setuptools.dynamic]
version = { attr = "odp_platform._version.__version__" }
```

**意思**: "version 字段从 `odp_platform/_version.py` 文件的 `__version__` 变量动态读取"。

这就是上面 `dynamic = ["version"]` 的具体来源——**两段配合,实现"版本号单一数据源"**。

### 3.7 子项目 pyproject.toml 完整 checklist

ODPlatform 的 `apps/platform/pyproject.toml` 有这些部分:

| 段 | 内容 | 必须? | 备注 |
|---|---|---|---|
| `[build-system]` | 构建工具 | ✅ 必须 | 任何项目都要 |
| `[project] name` | 包名 | ✅ 必须 | 唯一标识 |
| `[project] version` 或 `dynamic` | 版本 | ✅ 必须 | 否则 pip 不认 |
| `[project] description` | 描述 | 🟡 强烈建议 | |
| `[project] readme` | README | 🟡 公开发布建议 | |
| `[project] requires-python` | Python 版本 | 🟡 强烈建议 | |
| `[project] license` | 许可证 | 🟡 公开发布建议 | |
| `[project] authors` | 作者 | 🟡 建议 | |
| `[project] keywords` | 关键词 | ⚪ 可选 | PyPI 公开时填 |
| `[project] classifiers` | 分类器 | ⚪ 可选 | PyPI 公开时填 |
| `[project] dependencies` | 运行依赖 | ✅ 有依赖必须 | |
| `[project.optional-dependencies]` | 可选依赖 | ⚪ 可选 | dev/test 等组 |
| `[project.scripts]` | CLI 命令 | ⚪ 可选 | 提供命令行工具时必须 |
| `[tool.setuptools]` 系列 | setuptools 配置 | 🟡 用 setuptools 建议 | src/ 布局必须配置 |

## 四、ODPlatform 的顶层 pyproject.toml 详解

### 4.1 顶层 pyproject.toml 的特殊角色

D2 课程里我们有两份 pyproject.toml:

```
ODPlatform/
├── pyproject.toml                       ← 顶层(workspace 级)
└── apps/platform/pyproject.toml         ← 子项目(app 级)
```

**它们的角色完全不同**:

| | 顶层 pyproject.toml | apps/platform/pyproject.toml |
|---|---|---|
| 主要职责 | **workspace 级开发工具配置** | **可发布的 Python 包配置** |
| 主要内容 | `[tool.ruff]` `[tool.mypy]` `[tool.pytest.ini_options]` | `[project]` `[build-system]` `[project.scripts]` |
| 会被 pip 安装吗 | ❌ 不会 | ✅ 会(`pip install -e ./apps/platform`) |
| 工具读取 | ruff/mypy/pytest 等开发工具 | pip/setuptools 等打包工具 |

### 4.2 顶层 pyproject.toml 的内容

```toml
[project]
name = "odplatform-workspace"
version = "0.1.0"
description = "ODPlatform - 通用目标检测开发平台 (Monorepo workspace root)"
readme = "README.md"
requires-python = ">=3.10"
```

#### 为什么顶层也要写 `[project]`?

**严格来说不写也行**——顶层这个 pyproject.toml 不会被 pip install 安装。但写一段 `[project]` 有几个好处:

1. **元信息记录**——告诉看到这个文件的人"这是 ODPlatform workspace 的根"
2. **某些工具会读取**——比如 IDE 可能会用项目名做显示
3. **未来扩展性**——如果未来想给整个 workspace 加一些特殊配置,有地方写

但**注意**: 顶层 pyproject.toml **不要写 `[build-system]`**——否则 pip 会以为这也是个能装的包,可能引起混乱。

#### 顶层的 `[tool.ruff]` 配置

```toml
[tool.ruff]
line-length = 100
target-version = "py310"
src = [
    "apps/platform/src",
    "packages/shared-schemas/src",
]

[tool.ruff.lint]
select = ["E", "W", "F", "I", "B", "C4", "UP"]
ignore = ["E501"]

[tool.ruff.lint.isort]
known-first-party = ["odp_platform", "shared_schemas"]
```

**为什么 ruff 配置在顶层而不是子项目?**

因为我们希望**整个 workspace 用同一套代码风格规则**——platform、web-backend、shared-schemas 等所有 app 的代码风格应该一致。

ruff 的工作方式:

1. ruff 启动时,从当前目录向上找 pyproject.toml
2. 找到第一个有 `[tool.ruff]` 段的就用它
3. **整个 monorepo 共享这一套配置**

#### `[tool.ruff.lint]` 的 select 是什么?

```toml
[tool.ruff.lint]
select = ["E", "W", "F", "I", "B", "C4", "UP"]
```

每个字母代表一类检查规则:

| 代码 | 含义 | 例子 |
|---|---|---|
| `E` | pycodestyle 错误(PEP 8 规则) | 缩进不一致 |
| `W` | pycodestyle 警告 | 行尾空格 |
| `F` | pyflakes(逻辑错误) | 未使用的 import、未定义的变量 |
| `I` | isort(import 排序) | import 顺序混乱 |
| `B` | flake8-bugbear(常见 bug) | 可变默认参数 |
| `C4` | flake8-comprehensions | 推导式优化 |
| `UP` | pyupgrade(用新语法) | 用 f-string 替代 .format() |

`ignore = ["E501"]` 是说 "不要检查 E501(行太长)"——因为 ruff 的格式化器自己会处理。

**企业里常见的 select 配置**:

```toml
# 严格模式(很多大厂用)
select = ["E", "W", "F", "I", "B", "C4", "UP", "N", "D", "S", "ANN"]
# N: 命名规范
# D: 文档字符串
# S: 安全检查(bandit)
# ANN: 类型注解检查

# 宽松模式(初创公司,优先开发速度)
select = ["E", "W", "F"]

# 我们的中等模式(教学项目)
select = ["E", "W", "F", "I", "B", "C4", "UP"]
```

#### `[tool.mypy]` 类型检查配置

```toml
[tool.mypy]
python_version = "3.10"
warn_return_any = true
warn_unused_ignores = true
no_implicit_optional = true

[[tool.mypy.overrides]]
module = ["colorlog.*", "psutil.*", "ultralytics.*", "torch.*"]
ignore_missing_imports = true
```

**逐字段**:

- `python_version = "3.10"`: 按 3.10 的语法和类型规则检查
- `warn_return_any = true`: 函数返回 Any 类型时警告(强制写明确的返回类型)
- `warn_unused_ignores = true`: 检测过期的 `# type: ignore` 注释(代码改了之后某些 ignore 不需要了)
- `no_implicit_optional = true`: 参数默认值是 None 时,必须显式标注 `Optional[X]` 或 `X | None`,不能写 `X = None`

**`[[tool.mypy.overrides]]` 是什么?**

双方括号 `[[...]]` 在 TOML 里表示"数组中的一个对象"。意思是:

> 对于 colorlog/psutil/ultralytics/torch 这些第三方库,如果它们没有类型注解(stub 文件),不要报错。

为什么需要这个? 因为很多老的或者没有维护类型注解的库,mypy 检查到它们的 import 时会抱怨"这个库没有类型信息"。这一段告诉 mypy "对这些库放宽要求"。

**企业里的常见配置**(更严格):

```toml
[tool.mypy]
python_version = "3.10"
strict = true                    # 启用所有严格检查
warn_return_any = true
warn_unreachable = true
disallow_untyped_defs = true     # 函数必须有类型注解
disallow_incomplete_defs = true
check_untyped_defs = true
disallow_untyped_decorators = true
no_implicit_optional = true
warn_redundant_casts = true
warn_unused_ignores = true
warn_no_return = true
```

`strict = true` 一行抵很多——它启用了大约 10 个严格选项。新项目建议直接用 strict 模式。

#### `[tool.pytest.ini_options]` 测试配置

```toml
[tool.pytest.ini_options]
minversion = "7.0"
testpaths = [
    "apps/platform/tests",
    "tests",
]
python_files = ["test_*.py"]
addopts = ["-v", "--strict-markers", "--tb=short"]

markers = [
    "unit: 单元测试 (快,无 IO)",
    "integration: 集成测试 (有 IO)",
    "slow: 慢测试 (> 1s)",
]
```

**逐字段**:

- `minversion`: 最低 pytest 版本要求
- `testpaths`: pytest 默认去这些目录找测试(支持 monorepo 里多个 app 的测试)
- `python_files`: 文件名模式,只把 `test_xxx.py` 当作测试文件
- `addopts`: 默认加这些选项
  - `-v`: verbose,显示每个测试的名字
  - `--strict-markers`: 用未注册的 marker 会报错(防止打错 marker 名)
  - `--tb=short`: 失败时只显示简短的 traceback

**`markers` 是什么?**

pytest 的 marker 是给测试打标签:

```python
import pytest

@pytest.mark.slow
def test_full_training():
    # 完整训练测试,跑 30 分钟
    ...

@pytest.mark.unit
def test_quick_function():
    # 快速单元测试,几毫秒
    ...
```

定义了之后,可以**只跑某一类测试**:

```bash
pytest -m unit         # 只跑单元测试(开发时)
pytest -m "not slow"   # 跳过慢测试
pytest -m integration  # 只跑集成测试(CI 时)
```

`markers = [...]` 段是把所有自定义 marker 名"注册"了——配合 `--strict-markers` 防止你打错 marker 名。

### 4.3 顶层 pyproject.toml 完整 checklist

| 段 | 内容 | 必须? | 备注 |
|---|---|---|---|
| `[project]` | workspace 元信息 | ⚪ 可选 | 不写也行,写了更清晰 |
| `[build-system]` | 不要写 | ❌ 不要 | 顶层不是包,写了反而冲突 |
| `[tool.ruff]` | linter 配置 | 🟡 强烈建议 | 统一全 workspace 风格 |
| `[tool.mypy]` | 类型检查配置 | 🟡 强烈建议 | |
| `[tool.pytest.ini_options]` | 测试配置 | 🟡 强烈建议 | |
| `[tool.coverage.run]` | 覆盖率配置 | ⚪ 可选 | |
| `[tool.black]` 或 `[tool.ruff.format]` | 代码格式化 | ⚪ 可选 | 用 ruff 就不需要 black |

## 五、企业里常见的 pyproject.toml 模式

让我们看看真实工业项目里 pyproject.toml 长什么样。

### 5.1 模式一:小型应用(Flask web 服务)

```toml
[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[project]
name = "myapp"
version = "1.2.3"
description = "Internal CRM service"
requires-python = ">=3.11"

dependencies = [
    "flask>=3.0",
    "sqlalchemy>=2.0",
    "redis>=5.0",
    "pydantic>=2.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7",
    "pytest-cov",
    "ruff",
    "mypy",
]

[project.scripts]
myapp-server = "myapp.main:run_server"
myapp-migrate = "myapp.db.migrate:main"

[tool.ruff]
line-length = 100
target-version = "py311"

[tool.ruff.lint]
select = ["E", "W", "F", "I", "B", "UP"]
```

**特征**:
- 单一 pyproject.toml(没有 monorepo 复杂性)
- 直接写 `version = "1.2.3"`,简单粗暴
- 有 CLI 入口(server / migrate 工具)
- 配置精简,直接用得上

### 5.2 模式二:开源库(发布到 PyPI)

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "awesome-lib"
dynamic = ["version"]
description = "An awesome data processing library"
readme = "README.md"
requires-python = ">=3.9"
license = "MIT"
authors = [
    { name = "Jane Doe", email = "jane@example.com" },
]
maintainers = [
    { name = "Awesome Team" },
]
keywords = ["data", "processing", "etl"]

classifiers = [
    "Development Status :: 5 - Production/Stable",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Topic :: Scientific/Engineering",
    "Typing :: Typed",
]

dependencies = [
    "numpy>=1.20",
    "pandas>=2.0",
]

[project.optional-dependencies]
test = ["pytest>=7", "pytest-cov", "hypothesis"]
docs = ["sphinx>=7", "myst-parser"]
dev = ["awesome-lib[test,docs]", "pre-commit", "ruff", "mypy"]

[project.urls]
Homepage = "https://github.com/awesome/awesome-lib"
Documentation = "https://awesome-lib.readthedocs.io"
Repository = "https://github.com/awesome/awesome-lib.git"
Issues = "https://github.com/awesome/awesome-lib/issues"
Changelog = "https://github.com/awesome/awesome-lib/blob/main/CHANGELOG.md"

[tool.hatch.version]
path = "src/awesome_lib/__about__.py"

[tool.ruff]
line-length = 100
target-version = "py39"

[tool.mypy]
strict = true
```

**特征**:
- 用 hatchling 而不是 setuptools(更现代)
- 完整的 PyPI 元信息(classifiers/urls/keywords/maintainers)
- 多组可选依赖,通过引用组合
- `strict = true` 严格类型检查

### 5.3 模式三:Monorepo(像 ODPlatform)

```toml
# 顶层 pyproject.toml(只有共享配置)
[project]
name = "company-platform-workspace"
version = "0.1.0"

[project.optional-dependencies]
dev = ["pytest", "ruff", "mypy", "pre-commit"]

# ===========================
# 仅 [tool.xxx] 共享配置
# ===========================
[tool.ruff]
# ... 全 workspace 共享的 lint 规则

[tool.mypy]
# ... 全 workspace 共享的类型检查

[tool.pytest.ini_options]
testpaths = ["apps/*/tests", "packages/*/tests", "tests"]


# 各 app 自己的 apps/web-backend/pyproject.toml
[build-system]
requires = ["setuptools>=61"]

[project]
name = "company-web-backend"
dependencies = ["fastapi", "uvicorn", "company-shared-schemas"]
# 注意: 引用了同 monorepo 的另一个包 "company-shared-schemas"

[project.scripts]
backend-server = "web_backend.main:run"
```

**特征**:
- 顶层只放共享配置,没有自己的发布
- 每个子 app 独立的 pyproject.toml,独立发布
- 子 app 之间可以互相依赖(通过包名)
- 用 `pip install -e ./apps/web-backend -e ./packages/shared-schemas` 一次装多个

### 5.4 模式四:Poetry 风格

如果用 poetry,语法略不同(在新版 poetry 中已逐步对齐 PEP 621):

```toml
[tool.poetry]
name = "myproject"
version = "1.0.0"
description = "..."
authors = ["Jane <jane@example.com>"]

[tool.poetry.dependencies]
python = "^3.10"
flask = "^3.0"

[tool.poetry.group.dev.dependencies]
pytest = "^7.0"
ruff = "^0.1"

[tool.poetry.scripts]
myapp = "myproject.main:run"

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"
```

**特征**:
- 大部分配置在 `[tool.poetry]` 段下(老 poetry 风格)
- 版本约束用 `^` 这种 caret 语法
- Poetry 自动管理 lockfile(`poetry.lock`)

新版 poetry(2.0+)逐步改用标准 PEP 621 格式,所以这种"老风格"在过渡。

## 六、配置文件的组合智慧

### 6.1 ODPlatform 双层配置的设计哲学

```
ODPlatform/
├── pyproject.toml                 ← workspace 配置(共享开发工具)
└── apps/platform/pyproject.toml   ← 子项目配置(发布信息)
```

**这种双层设计的精妙之处**:

```
关注点              位置                    原因
─────────────       ─────────────           ──────────────────
代码风格规则        顶层                    全 workspace 一致
类型检查规则        顶层                    全 workspace 一致
测试配置            顶层                    包含所有 app 的测试
                                            
包名               子项目                  每个 app 是独立可发布的包
版本               子项目                  每个 app 独立版本
依赖               子项目                  platform 用 torch,backend 用 flask
CLI 命令           子项目                  每个 app 注册自己的命令
打包配置           子项目                  src/ 布局等
```

**核心原则**: **共享的放上面,独立的放下面**。

### 6.2 未来扩展时的样子

当 V1.1 加上 web-backend 时,会变成:

```
ODPlatform/
├── pyproject.toml                       ← 顶层(配置不变)
├── apps/
│   ├── platform/pyproject.toml          ← 已有
│   ├── web-backend/pyproject.toml       ← 🆕
│   └── web-frontend/                    ← 不是 Python 项目,无 pyproject.toml
└── packages/
    └── shared-schemas/pyproject.toml    ← 🆕
```

**4 个 pyproject.toml,各管各的**。每个子 app 有独立的:
- 依赖
- 版本
- CLI 命令
- 发布权限

但**共享同一套**:
- 代码风格(ruff)
- 类型检查(mypy)
- 测试规范(pytest)

这就是为什么 D1 课程选 monorepo 是对的——**协作成本低,但隔离性好**。

## 七、实战:遇到问题怎么办?

### 7.1 常见错误及排查

#### 错误 1: `pip install -e .` 失败

```
ERROR: Project file:///xxx has a 'pyproject.toml' and its build backend is missing 
the 'build_editable' hook. Since it does not have the 'wheel' extra in 
'build-system.requires', pip cannot fall back to setuptools without 'wheel'.
```

**原因**: setuptools 版本太老。

**解决**:

```toml
[build-system]
requires = ["setuptools>=64.0", "wheel"]  # 64.0+ 才完整支持 editable install
build-backend = "setuptools.build_meta"
```

#### 错误 2: 装完包但 `odp-init` 命令找不到

```bash
$ odp-init
bash: odp-init: command not found
```

**可能原因**:

1. 没装上(检查 `pip show odp-platform`)
2. conda 环境没激活(检查 `which python`)
3. PATH 里没有 conda 环境的 bin/(检查 `echo $PATH`)
4. pyproject.toml 里 `[project.scripts]` 写错(对照模块路径)

**逐项排查**:

```bash
pip show odp-platform                   # 1
which python                            # 2
echo $PATH                              # 3
python -c "from odp_platform.cli.init_project import initialize_project"  # 4
```

#### 错误 3: 修改代码后 `odp-init` 没生效

**原因**: 你装的是 non-editable 模式,而不是 editable。

**解决**: 卸载重装,加 `-e`:

```bash
pip uninstall odp-platform
pip install -e ./apps/platform   # ← -e 是关键
```

`-e` 是 editable 模式,代码改了 import 就能立即看到新版,不用重装。

#### 错误 4: 版本号不同步

`odp_platform.__version__` 显示 `0.1.0`,但 `pip show odp-platform` 显示 `0.0.0`。

**原因**: 你修改了 `_version.py`,但没重装包。setuptools 的 dynamic version 是**安装时**读取的,不是运行时。

**解决**:

```bash
pip install -e ./apps/platform --force-reinstall --no-deps
```

或者更简单:删掉 `_version.py` 里 `__version__` 的旧值,重启 Python。

### 7.2 调试技巧

#### 看 pip 实际做了什么

```bash
pip install -e ./apps/platform -v
```

加 `-v` 会输出详细日志,包括"读取了哪个 pyproject.toml""调用了什么打包后端"。

#### 看打包出的包结构

```bash
pip install build
python -m build apps/platform
ls apps/platform/dist/
# odp_platform-0.1.0-py3-none-any.whl
# odp_platform-0.1.0.tar.gz
```

`.whl` 是个 zip,可以解压看里面到底打包了什么文件:

```bash
unzip -l apps/platform/dist/odp_platform-0.1.0-py3-none-any.whl
```

如果发现少了某些文件,说明 `[tool.setuptools.packages.find]` 配置漏了。

#### 验证 entry-point 注册

```bash
pip show -f odp-platform | grep entry_points
```

或者看生成的命令脚本:

```bash
cat $(which odp-init)   # Linux/macOS
notepad (Get-Command odp-init).Source   # Windows
```

应该能看到一段简单的 Python 脚本,内容是调用 `initialize_project`。

---

# 第三部分:回到 ODPlatform——把所有点串起来

## 八、ODPlatform 的工程化全景

我们花了很多篇幅讲单点知识,现在把它们串起来,看看 ODPlatform 的工程化是怎样一个整体:

```
ODPlatform/
│
├── 顶层 pyproject.toml              ← 协作层(workspace 共享)
│   ├── [project]                    ← workspace 元信息
│   ├── [tool.ruff]                  ← 全 workspace 代码风格
│   ├── [tool.mypy]                  ← 全 workspace 类型检查
│   └── [tool.pytest]                ← 全 workspace 测试规范
│
├── apps/platform/pyproject.toml     ← 包层(platform 这一个 app)
│   ├── [build-system]               ← 怎么构建
│   ├── [project] name/version/...   ← 包元信息
│   ├── [project.dependencies]       ← 运行依赖
│   ├── [project.scripts] odp-init   ← CLI 命令注册
│   └── [tool.setuptools]            ← 包路径、版本来源
│
├── apps/platform/src/odp_platform/  ← 实际的 Python 包
│   ├── _version.py                  ← 版本号单一数据源
│   ├── common/                      ← 基础设施(D2)
│   │   ├── paths.py
│   │   ├── logging_utils.py
│   │   ├── string_utils.py
│   │   ├── system_utils.py
│   │   └── performance_utils.py    ← @time_it 在这里
│   └── cli/
│       └── init_project.py          ← 被 odp-init 调用的入口
│
└── scripts/init_project.py          ← 开发阶段的临时入口
```

**信息流向**:

```
开发阶段:
    用户 → python scripts/init_project.py
         → sys.path.insert(...) 修复路径
         → 调用 odp_platform.cli.init_project.initialize_project
         → @time_it 装饰器记录耗时

工程化后:
    用户 → odp-init (命令)
         → pip 生成的小脚本
         → 调用 odp_platform.cli.init_project.initialize_project
         → @time_it 装饰器记录耗时

两条路殊途同归,都到了同一个业务函数。
```

## 九、关键收获总结

如果只能记 5 句话:

1. **performance_utils.py 用装饰器封装 timing 逻辑**——业务代码不变,加 `@time_it()` 就有了耗时报告

2. **pyproject.toml 是现代 Python 项目的【单一配置文件】**——取代了 setup.py + setup.cfg + requirements.txt 等一堆老文件

3. **`[build-system]`、`[project]`、`[project.scripts]` 三段是 PEP 标准**——所有打包工具都认

4. **`[tool.xxx]` 段是各工具自己的配置**——ruff/mypy/pytest 等读自己的那段

5. **Monorepo 用双层 pyproject.toml**——顶层管 workspace 共享(代码风格等),子层管包发布(依赖、版本、CLI)

如果能记更多:

- **`pip install -e .` 装 editable 包,`[project.scripts]` 注册的命令立即生效**
- **`dynamic = ["version"]` 配合 `[tool.setuptools.dynamic]` 实现版本号单一数据源**
- **src/ 布局强制"装了才能用",避免源码和已安装版本混淆**
- **企业项目常见三种模式: 小应用 / 开源库 / Monorepo,各有侧重**
- **所有配置都是【声明式】的,工具读了自己执行,你不需要管底层**

---

# 课后练习

## 练习 1: 装饰器实验

写一个 Python 文件,测试这几种 `@time_it()` 用法:

```python
from odp_platform.common.performance_utils import time_it
import time

@time_it()
def task_1():
    time.sleep(0.001)

@time_it(iterations=100, name="批量任务")
def task_2():
    sum(range(1000))

@time_it()
def task_3(x, y):
    time.sleep(x)
    return y * 2

task_1()
task_2()
result = task_3(0.5, 10)
print(f"task_3 返回: {result}")
```

观察输出格式,理解参数的影响。

## 练习 2: pyproject.toml 改造实验

修改 `apps/platform/pyproject.toml`,加一个新的 CLI 命令:

```toml
[project.scripts]
odp-init = "odp_platform.cli.init_project:initialize_project"
odp-version = "odp_platform.cli.version:show_version"   # ← 新加
```

然后:

1. 创建对应的 `apps/platform/src/odp_platform/cli/version.py`,定义 `show_version()` 函数(打印当前版本号)
2. 重新装包: `pip install -e ./apps/platform`
3. 测试: `odp-version`

如果一切正确,你会看到:

```
$ odp-version
ODPlatform v0.1.0
```

## 练习 3: 配置严格度对比

故意把代码风格搞乱:

```python
def foo( x,y ):
    z=x+y
    return z
```

然后跑:

```bash
ruff check apps/platform/src
```

观察 ruff 报告的问题。

接着把顶层 pyproject.toml 的 ruff 配置改成更严格:

```toml
select = ["E", "W", "F", "I", "B", "C4", "UP", "N", "D"]
```

再跑一次,看多了哪些检查项。

## 练习 4: 阅读真实项目

打开 GitHub 上几个明星 Python 项目,看它们的 pyproject.toml:

- [requests](https://github.com/psf/requests/blob/main/pyproject.toml) - 经典 HTTP 库
- [pydantic](https://github.com/pydantic/pydantic/blob/main/pyproject.toml) - 数据验证库
- [fastapi](https://github.com/tiangolo/fastapi/blob/master/pyproject.toml) - Web 框架
- [poetry](https://github.com/python-poetry/poetry/blob/master/pyproject.toml) - 包管理工具自己

看看它们的:
- 用什么 build-backend?
- dependencies 怎么写?
- 有哪些 optional-dependencies 组?
- `[tool.xxx]` 都配了哪些工具?

**对比自己的项目**,思考"我的配置缺了什么?多了什么?"

---

# 最后一段话

工程化的本质不是"把简单的事变复杂",而是"**把复杂度【一次性】解决,然后所有人享受简单**"。

`pyproject.toml` 看起来 100 行配置很多,但它**一次定义,永远生效**——以后所有团队成员、CI 服务器、部署机器,都用同一套规则。

`@time_it()` 装饰器看起来比手写 `time.time()` 复杂,但它**一次定义,处处使用**——业务代码再也不需要关心 timing 怎么测。

这就是基础设施的杠杆效应。**你今天理解透了这两个东西,以后每个 Python 项目都能用同一套思路搞定**——不再是每次都重新摸索"打包配置怎么写""装饰器怎么用"。

下一节(D3-D4)我们会进入配置管理系统(Pydantic + 三源合并),那时候你会发现——**Pydantic 也是用类似的"声明式配置"思路**,跟 pyproject.toml 一脉相承。

晚安,明天见。

---

*项目: ODPlatform | 对应文档: D2 阶段 9 + 阶段 11 深度补充*
