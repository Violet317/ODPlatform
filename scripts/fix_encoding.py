#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
精确修复项目文件中的中文乱码问题。
使用已知的乱码→正确的映射表进行替换。
"""
import os

BASE_DIR = r"f:\python_projects\class\ODPlatform"

# 已知乱码映射表（@Function 行 + 常见 docstring 乱码）
GARBLED_MAP = {
    # @Function 行
    '@Function  :鍏叡宸ュ叿瀛愭ā鍧椻€斺€旇矾寰勩€佹棩蹇椼€佸瓧绗︿覆銆佺郴缁熷伐鍏': '@Function  :公共工具子模块 —— 路径、日志、字符串、系统工具',
    '@Function  :鏁版嵁绠￠亾瀛愭ā鍧椻€斺€旀暟鎹泦鏍煎紡杞崲(VOC/COCO 鈫?YOLO)': '@Function  :数据管道子模块 —— 数据集格式转换(VOC/COCO → YOLO)',
    '@Function  :鏁版嵁绠￠亾鏍稿績 鈥斺€?VOC 鍜?COCO 鏍煎紡杞崲鍣': '@Function  :数据管道核心 —— VOC 和 COCO 格式转换器',
    '@Function  :閰嶇疆绠＄悊瀛愭ā鍧椻€斺€斿鍑洪厤缃被銆佸姞杞藉櫒銆佸悎骞跺櫒銆佺敓鎴愬櫒': '@Function  :配置管理子模块 —— 导出配置类、加载器、合并器、生成器',
    '@Function  :閰嶇疆鍩虹被 鈥斺€?鎵€鏈夐厤缃ā鍨嬬殑鍩虹被': '@Function  :配置基类 —— 所有配置模型的基类',
    '@Function  :璁粌閰嶇疆妯″瀷 鈥斺€?Pydantic 瀹氫箟璁粌鍙傛暟': '@Function  :训练配置模型 —— Pydantic 定义训练参数',
    '@Function  :鎺ㄧ悊閰嶇疆妯″瀷 鈥斺€?Pydantic 瀹氫箟鎺ㄧ悊鍙傛暟': '@Function  :推理配置模型 —— Pydantic 定义推理参数',
    '@Function  :楠岃瘉閰嶇疆妯″瀷 鈥斺€?Pydantic 瀹氫箟璇勪及鍙傛暟': '@Function  :验证配置模型 —— Pydantic 定义评估参数',
    '@Function  :閰嶇疆鍔犺浇鍣ㄢ€斺€?浠?YAML 鏂囦欢鍔犺浇骞堕獙璇侀厤缃': '@Function  :配置加载器 —— 从 YAML 文件加载并验证配置',
    '@Function  :閰嶇疆鍚堝苟鍣ㄢ€斺€?鍚堝苟澶氫釜鏉ユ簮鐨勯厤缃': '@Function  :配置合并器 —— 合并多个来源的配置',
    '@Function  :閰嶇疆鏂囦欢鐢熸垚鍣ㄢ€斺€?鍒涘缓榛樿閰嶇疆 YAML 鏂囦欢': '@Function  :配置文件生成器 —— 创建默认配置 YAML 文件',
    '@Function  :CLI 瀛愭ā鍧椻€斺€斿懡浠よ鍏ュ彛闆嗗悎': '@Function  :CLI 子模块 —— 命令行入口集合',
    '@Function  :鏁版嵁鏍￠獙 CLI 鈥斺€?odp-validate 鍛戒护鍏ュ彛': '@Function  :数据校验 CLI —— odp-validate 命令入口',
    '@Function  :璁粌瀛愭ā鍧': '@Function  :训练子模块',
    '@Function  :鎺ㄧ悊瀛愭ā鍧椻€斺€?妯″瀷鎺ㄧ悊鏈嶅姟銆佹祦姘寸嚎銆佺粨鏋滃鐞': '@Function  :推理子模块 —— 模型推理服务、流水线、结果处理',
    '@Function  :鎺ㄧ悊娴佹按绾裤€斺€?鎵归噺鎺ㄧ悊涓庡悗澶勭悊': '@Function  :推理流水线 —— 批量推理与后处理',
    '@Function  :鎺ㄧ悊缁勪欢 鈥斺€?妫€娴嬬粨鏋滃皝瑁呬笌澶勭悊': '@Function  :推理组件 —— 检测结果封装与处理',
    '@Function  :璇勪及瀛愭ā鍧': '@Function  :评估子模块',
    '@Function  :鏁版嵁鏍￠獙瀛愭ā鍧椻€斺€旀暟鎹泦楠岃瘉銆佸垎鏋愩€佹竻娲椼€佸彲瑙嗗寲銆佹姤鍛': '@Function  :数据校验子模块 —— 数据集验证、分析、清洗、可视化、报告',
    '@Function  :鏁版嵁鏍￠獙鏍稿績 鈥斺€?楠岃瘉鍣ㄣ€佸垎鏋愬櫒銆佹竻娲楀櫒銆佸彲瑙嗗寲鍣ㄣ€佹姤鍛婄敓鎴': '@Function  :数据校验核心 —— 验证器、分析器、清洗器、可视化器、报告生成',
    '@Function  :鏁版嵁闆嗘牎楠屽櫒 鈥斺€?楠岃瘉 YOLO 鏍煎紡鏁版嵁闆嗙殑瀹屾暣鎬': '@Function  :数据集校验器 —— 验证 YOLO 格式数据集的完整性',
    '@Function  :鏁版嵁闆嗗垎鏋愬櫒 鈥斺€?缁熻 YOLO 鏁版嵁闆嗙殑鍚勭被鎸囨爣': '@Function  :数据集分析器 —— 统计 YOLO 数据集的各种指标',
    '@Function  :鏁版嵁闆嗘竻娲楀櫒 鈥斺€?绉婚櫎鏃犳晥鏍锋湰骞惰緭鍑烘竻娲楀悗鐨勬暟鎹泦': '@Function  :数据集清洗器 —— 移除无效样本并输出清洗后的数据集',
    '@Function  :鎶ュ憡鐢熸垚鍣ㄢ€斺€?鐢熸垚鏁版嵁闆嗛獙璇佹姤鍛': '@Function  :报告生成器 —— 生成数据集验证报告',
    '@Function  :鏁版嵁闆嗗彲瑙嗗寲鍣ㄢ€斺€?鐢熸垚鏁版嵁闆嗗垎鏋愬浘琛': '@Function  :数据集可视化器 —— 生成数据集分析图表',
    '@Function  :鍥捐〃鐢熸垚鍣ㄢ€斺€?鐢熸垚鏁版嵁闆嗗垎鏋愬彲瑙嗗寲鍥捐〃': '@Function  :图表生成器 —— 生成数据集分析可视化图表',
    '@Function  :鐗堟湰淇℃伅': '@Function  :版本信息',
    
    # __init__.py 包文档中的乱码
    'ODPlatform - 閫氱敤鐨勭洰鏍囨娴嬪紑鍙戝钩鍙': 'ODPlatform - 通用的目标检测开发平台',
    'Public API 鍏ュ彛锛屽叿浣撶殑瀛愭ā鍧楋細': 'Public API 入口，具体的子模块：',
    'odp_platform.common       : 鍩虹宸ュ叿锛堣矾寰勩€佹棩蹇椼€佸瓧绗︿覆銆佺郴缁熴€佹€ц兘锛': 'odp_platform.common       : 基础工具（路径、日志、字符串、系统、性能）',
    'odp_platform.config       : 閰嶇疆绠＄悊锛堣缁?楠岃瘉/鎺ㄧ悊閰嶇疆 + 鍔犺浇/鍚堝苟锛': 'odp_platform.config       : 配置管理（训练/验证/推理配置 + 加载/合并）',
    'odp_platform.data_pipeline: 鏁版嵁绠￠亾锛圥ascal VOC / COCO 鈫?YOLO 鏍煎紡杞崲锛': 'odp_platform.data_pipeline: 数据管道（Pascal VOC / COCO → YOLO 格式转换）',
    'odp_platform.data_validation: 鏁版嵁鏍￠獙锛堥獙璇併€佸垎鏋愩€佹竻娲椼€佸彲瑙嗗寲銆佹姤鍛婏級': 'odp_platform.data_validation: 数据校验（验证、分析、清洗、可视化、报告）',
    'odp_platform.training     : 妯″瀷璁粌': 'odp_platform.training     : 模型训练',
    'odp_platform.evaluation   : 妯″瀷璇勪及': 'odp_platform.evaluation   : 模型评估',
    'odp_platform.inference    : 妯″瀷鎺ㄧ悊': 'odp_platform.inference    : 模型推理',
    'odp_platform.cli          : 鍛戒护琛屽叆鍙ｏ紙odp-* 绯诲垪鍛戒护锛': 'odp_platform.cli          : 命令行入口（odp-* 系列命令）',

    # config/base.py
    '"""鎵€鏈夊钩鍙版搷浣滅殑閰嶇疆鍩虹被銆?""': '"""所有平台操作的配置基类。"""',
    '"""灏嗛厤缃浆鎹负瀛楀吀銆?""': '"""将配置转换为字典。"""',
    '"""淇濆瓨閰嶇疆鍒?YAML 鏂囦欢銆?""': '"""保存配置到 YAML 文件。"""',
    '"""浠?YAML 鏂囦欢鍔犺浇閰嶇疆銆?""': '"""从 YAML 文件加载配置。"""',
    
    # config/train_config.py
    'class TrainConfig(BaseConfig):\n    """YOLO 妯″瀷璁粌閰嶇疆銆?""': 'class TrainConfig(BaseConfig):\n    """YOLO 模型训练配置。"""',
    'class TrainConfig(BaseConfig):\r\n    """YOLO 妯″瀷璁粌閰嶇疆銆?""': 'class TrainConfig(BaseConfig):\r\n    """YOLO 模型训练配置。"""',
    '    # 鏁版嵁涓庢ā鍨': '    # 数据与模型',
    '    # 璁粌瓒呭弬鏁': '    # 训练超参数',
    '    # 浼樺寲鍣': '    # 优化器',
    '    # 鏃╁仠': '    # 早停',
    
    # config/infer_config.py
    'class InferConfig(BaseConfig):\n    """YOLO 妯″瀷鎺ㄧ悊閰嶇疆銆?""': 'class InferConfig(BaseConfig):\n    """YOLO 模型推理配置。"""',
    'class InferConfig(BaseConfig):\r\n    """YOLO 妯″瀷鎺ㄧ悊閰嶇疆銆?""': 'class InferConfig(BaseConfig):\r\n    """YOLO 模型推理配置。"""',
    
    # config/val_config.py
    'class ValConfig(BaseConfig):\n    """YOLO 妯″瀷楠岃瘉/璇勪及閰嶇疆銆?""': 'class ValConfig(BaseConfig):\n    """YOLO 模型验证/评估配置。"""',
    'class ValConfig(BaseConfig):\r\n    """YOLO 妯″瀷楠岃瘉/璇勪及閰嶇疆銆?""': 'class ValConfig(BaseConfig):\r\n    """YOLO 模型验证/评估配置。"""',
    
    # config/loaders.py
    'def load_yaml(path: Path) -> dict:\n    """鍔犺浇 YAML 鏂囦欢骞惰繑鍥炲瓧鍏搞€?""': 'def load_yaml(path: Path) -> dict:\n    """加载 YAML 文件并返回字典。"""',
    'def load_yaml(path: Path) -> dict:\r\n    """鍔犺浇 YAML 鏂囦欢骞惰繑鍥炲瓧鍏搞€?""': 'def load_yaml(path: Path) -> dict:\r\n    """加载 YAML 文件并返回字典。"""',
    '        raise FileNotFoundError(f"閰嶇疆鏂囦欢涓嶅瓨鍦? {path}")': '        raise FileNotFoundError(f"配置文件不存在: {path}")',
    '        raise ValueError(f"涓嶆敮鎸佺殑閰嶇疆鏂囦欢鎵╁睍鍚? {path.suffix}")': '        raise ValueError(f"不支持的配置文件扩展名: {path.suffix}")',
    '            raise ValueError(f"閰嶇疆鏂囦负绌? {path}")': '            raise ValueError(f"配置文件为空: {path}")',
    '        raise ValueError(f"YAML 鏍煎紡鏃犳晥 ({path}): {e}")': '        raise ValueError(f"YAML 格式无效 ({path}): {e}")',
    'def _load_config(path: Path, config_class: type[BaseConfig]) -> BaseConfig:\n    """鍔犺浇骞堕獙璇侀厤缃€?""': 'def _load_config(path: Path, config_class: type[BaseConfig]) -> BaseConfig:\n    """加载并验证配置。"""',
    'def _load_config(path: Path, config_class: type[BaseConfig]) -> BaseConfig:\r\n    """鍔犺浇骞堕獙璇侀厤缃€?""': 'def _load_config(path: Path, config_class: type[BaseConfig]) -> BaseConfig:\r\n    """加载并验证配置。"""',
    '        raise ValidationError(f"閰嶇疆楠岃瘉澶辫触 ({path}):\\n{e}")': '        raise ValidationError(f"配置验证失败 ({path}):\\n{e}")',
    'def load_train_config(path: Path) -> TrainConfig:\n    """浠?YAML 鍔犺浇璁粌閰嶇疆銆?""': 'def load_train_config(path: Path) -> TrainConfig:\n    """从 YAML 加载训练配置。"""',
    'def load_train_config(path: Path) -> TrainConfig:\r\n    """浠?YAML 鍔犺浇璁粌閰嶇疆銆?""': 'def load_train_config(path: Path) -> TrainConfig:\r\n    """从 YAML 加载训练配置。"""',
    'def load_val_config(path: Path) -> ValConfig:\n    """浠?YAML 鍔犺浇楠岃瘉閰嶇疆銆?""': 'def load_val_config(path: Path) -> ValConfig:\n    """从 YAML 加载验证配置。"""',
    'def load_val_config(path: Path) -> ValConfig:\r\n    """浠?YAML 鍔犺浇楠岃瘉閰嶇疆銆?""': 'def load_val_config(path: Path) -> ValConfig:\r\n    """从 YAML 加载验证配置。"""',
    'def load_infer_config(path: Path) -> InferConfig:\n    """浠?YAML 鍔犺浇鎺ㄧ悊閰嶇疆銆?""': 'def load_infer_config(path: Path) -> InferConfig:\n    """从 YAML 加载推理配置。"""',
    'def load_infer_config(path: Path) -> InferConfig:\r\n    """浠?YAML 鍔犺浇鎺ㄧ悊閰嶇疆銆?""': 'def load_infer_config(path: Path) -> InferConfig:\r\n    """从 YAML 加载推理配置。"""',
    
    # config/merger.py - full docstring and comments
    'def merge_configs(base: BaseConfig, override: dict[str, Any]) -> BaseConfig:\n    """灏嗚鐩栧瓧鍏稿悎骞跺埌鍩虹閰嶇疆涓苟楠岃瘉銆?': 'def merge_configs(base: BaseConfig, override: dict[str, Any]) -> BaseConfig:\n    """将覆盖字典合并到基础配置中并验证。',
    'Args:\n        base: 鍩虹閰嶇疆瀹炰緥銆?        override: 瑕佽鐩栫殑瀛楁瀛楀吀銆?    Returns:\n        鍚堝苟鍚庣殑鏂伴厤缃疄渚嬨€?    Raises:\n        ValidationError: 濡傛灉鍚堝苟鍚庣殑鍊兼湭閫氳繃楠岃瘉銆?    """': '    Args:\n        base: 基础配置实例。\n        override: 要覆盖的字段字典。\n    Returns:\n        合并后的新配置实例。\n    Raises:\n        ValidationError: 如果合并后的值未通过验证。\n    """',
    
    # config/generator.py
    'def generate_train_config(output_path: Path) -> None:\n    """鐢熸垚榛樿璁粌閰嶇疆鏂囦欢銆?""': 'def generate_train_config(output_path: Path) -> None:\n    """生成默认训练配置文件。"""',
    'def generate_val_config(output_path: Path) -> None:\n    """鐢熸垚榛樿楠岃瘉閰嶇疆鏂囦欢銆?""': 'def generate_val_config(output_path: Path) -> None:\n    """生成默认验证配置文件。"""',
    'def generate_infer_config(output_path: Path) -> None:\n    """鐢熸垚榛樿鎺ㄧ悊閰嶇疆鏂囦欢銆?""': 'def generate_infer_config(output_path: Path) -> None:\n    """生成默认推理配置文件。"""',
    
    # cli/validate.py
    'def main():\n    """鏁版嵁鏍￠獙鍛戒护琛屽叆鍙ｃ€?""': 'def main():\n    """数据校验命令行入口。"""',
    
    # validate.py @Function
    '@Function  :鏁版嵁鏍￠獙 CLI 鈥斺€?odp-validate 鍛戒护鍏ュ彛': '@Function  :数据校验 CLI —— odp-validate 命令入口',
    
    # validation core files
    'class YOLODatasetValidator:\n    """YOLO 鏍煎紡鏁版嵁闆嗛獙璇佸櫒銆?""': 'class YOLODatasetValidator:\n    """YOLO 格式数据集验证器。"""',
    '"""鏁版嵁闆嗘牎楠屽櫒 鈥斺€?楠岃瘉 YOLO 鏍煎紡鏁版嵁闆嗙殑瀹屾暣鎬?': '"""数据集校验器 —— 验证 YOLO 格式数据集的完整性',
    'class DatasetAnalyzer:\n    """YOLO 鏁版嵁闆嗙粺璁″垎鏋愬櫒銆?""': 'class DatasetAnalyzer:\n    """YOLO 数据集统计分析器。"""',
    'class DatasetCleaner:\n    """YOLO 鏁版嵁闆嗘竻娲楀櫒銆?""': 'class DatasetCleaner:\n    """YOLO 数据集清洗器。"""',
    'class DatasetVisualizer:\n    """鏁版嵁闆嗗垎鏋愬彲瑙嗗寲鍣ㄣ€?""': 'class DatasetVisualizer:\n    """数据集分析可视化器。"""',
    'class ReportGenerator:\n    """鏁版嵁闆嗛獙璇佹姤鍛婄敓鎴愬櫒銆?""': 'class ReportGenerator:\n    """数据集验证报告生成器。"""',
    'class ChartGenerator:\n    """鏁版嵁闆嗗垎鏋愬浘琛ㄧ敓鎴愬櫒銆?""': 'class ChartGenerator:\n    """数据集分析图表生成器。"""',
    'class InferencePipeline:\n    """鎵归噺鎺ㄧ悊娴佹按绾裤€?""': 'class InferencePipeline:\n    """批量推理流水线。"""',
    'class DetectionResult:\n    """妫€娴嬬粨鏋滃皝瑁呫€?""': 'class DetectionResult:\n    """检测结果封装。"""',
    
    # Other garbled docstrings in validators.py
    '"""鎵ц鎵€鏈夋牎楠屾鏌ャ€?': '"""执行所有校验检查。',
    '"""妫€鏌ュ繀瑕佺殑鐩綍缁撴瀯鏄惁瀛樺湪銆?"': '"""检查必要的目录结构是否存在。"""',
    '"""妫€鏌ュ浘鐗囨枃浠舵槸鍚﹀瓨鍦ㄤ笖鎵╁睍鍚嶆湁鏁堛€?"': '"""检查图像文件是否存在且扩展名有效。"""',
    '"""妫€鏌ユ爣绛炬枃浠朵笌鍥剧墖鏂囦欢鏄惁鍖归厤銆?"': '"""检查标签文件与图像文件是否匹配。"""',
    '"""妫€鏌ユ爣绛炬枃浠舵牸寮忋€?"': '"""检查标签文件格式。"""',
    '"""楠岃瘉鍗曚釜鏍囩鏂囦欢銆?"': '"""验证单个标签文件。"""',

    # validators.py error messages
    '缂哄皯鐩綍': '缺少目录',
    '缂哄皯鏁版嵁闆嗛厤缃?data.yaml': '缺少数据集配置 data.yaml',
    '鏁版嵁闆嗛厤缃腑缂哄皯 ': '数据集配置中缺少 ',
    '鏁版嵁闆嗛厤缃棤鏁堬細': '数据集配置无效：',
    '涓嶆敮鎸佺殑鍥剧墖鎵╁睍鍚': '不支持的图片扩展名',
    '鍥剧墖缂哄皯鏍囩鏂囦欢': '图片缺少标签文件',
    
    # validators.py specific lines
    '闇€瑕?5 涓€硷紝瀹為檯': '需要 5 个值，实际',
    '鏃犳晥鐨勭被鍒?ID': '无效的类别 ID',
    '鍧愭爣鍊?': '坐标值 ',
    '瓒呭嚭 [0, 1] 鑼冨洿': '超出 [0, 1] 范围',
    '鏍煎紡瑙ｆ瀽澶辫触': '格式解析失败',
    
    # analyzers.py
    'def analyze(self) -> dict:\n        """\n        鍒嗘瀽鏁版嵁闆嗙殑缁熻淇℃伅銆?': 'def analyze(self) -> dict:\n        """\n        分析数据集的统计信息。',
    '鏁版嵁闆嗗垎鏋愬畬鎴?| 鍥剧墖': '数据集分析完成 | 图片',
    '鏍囩': '标签',
    '鏍囨敞妗?': '标注框',
    
    # cleaners.py
    'class DatasetCleaner:\n    """YOLO 鏁版嵁闆嗘竻娲楀櫒銆?"': 'class DatasetCleaner:\n    """YOLO 数据集清洗器。"""',
    'class DatasetCleaner:\r\n    """YOLO 鏁版嵁闆嗘竻娲楀櫒銆?"': 'class DatasetCleaner:\r\n    """YOLO 数据集清洗器。"""',
    '"""娓呮礂鏁版嵁闆嗗苟淇濆瓨鍒拌緭鍑虹洰褰曘€?"': '"""清洗数据集并保存到输出目录。"""',
    '"""娓呮礂鍗曚釜鏁版嵁鍒掑垎锛坱rain/val/test锛夈€?"': '"""清洗单个数据划分（train/val/test）。"""',
    '"""鏌ユ壘涓庢爣绛?stem 鍖归厤鐨勫浘鐗囥€?"': '"""查找与标签 stem 匹配的图像。"""',
    '"""妫€鏌ユ爣绛炬枃浠舵槸鍚︽湁鏁堛€?"': '"""检查标签文件是否有效。"""',
    
    # visualizers.py
    'class DatasetVisualizer:\n    """鏁版嵁闆嗗垎鏋愬彲瑙嗗寲鍣ㄣ€?"': 'class DatasetVisualizer:\n    """数据集分析可视化器。"""',
    '"""鐢熸垚鎵€鏈夊彲瑙嗗寲鍥捐〃銆?"': '"""生成所有可视化图表。"""',
    
    # reporters.py
    'class ReportGenerator:\n    """鏁版嵁闆嗛獙璇佹姤鍛婄敓鎴愬櫒銆?"': 'class ReportGenerator:\n    """数据集验证报告生成器。"""',
    '"""\n        灏嗗垎鏋愮粨鏋滀繚瀛樹负鏂囨湰鎶ュ憡銆?': '"""\n        将分析结果保存为文本报告。',
    '杈撳嚭鎶ュ憡鏂囦欢璺緞': '输出报告文件路径',
    '"""\n        灏嗗垎鏋愮粨鏋滀繚瀛樹负 HTML 鎶ュ憡銆?': '"""\n        将分析结果保存为 HTML 报告。',
    '杈撳嚭 HTML 鏂囦欢璺緞': '输出 HTML 文件路径',
    
    # chart_generator.py
    'class ChartGenerator:\n    """鏁版嵁闆嗗垎鏋愬浘琛ㄧ敓鎴愬櫒銆?"': 'class ChartGenerator:\n    """数据集分析图表生成器。"""',
    '"""鐢熸垚绫诲埆鍒嗗竷鏌辩姸鍥俱€?"': '"""生成类别分布柱状图。"""',
    'matplotlib 鏈畨瑁咃紝璺宠繃鍥捐〃': 'matplotlib 未安装，跳过图表',
    '娌℃湁绫诲埆鍒嗗竷鏁版嵁锛岃烦杩囧浘琛ㄣ€?': '没有类别分布数据，跳过图表。',
    '绫诲埆鍒嗗竷鍥惧凡淇濆瓨鑷?': '类别分布图已保存至',
    '"""鐢熸垚鍥剧墖灏哄鍒嗗竷鏁ｇ偣鍥俱€?"': '"""生成图像尺寸分布散点图。"""',
    '娌℃湁鎵惧埌鍥剧墖锛岃烦杩囧昂瀵稿垎甯冨浘琛ㄣ€?': '没有找到图像，跳过尺寸分布图表。',
    '鍥剧墖灏哄鍒嗗竷鍥惧凡淇濆瓨鑷?': '图像尺寸分布图已保存至',
    '"""鐢熸垚杈圭晫妗嗗昂瀵稿垎甯冪洿鏂瑰浘銆?"': '"""生成边界框尺寸分布直方图。"""',
    
    # pipeline.py
    '    def run(self, source: Path) -> list:\n        """杩愯瀹屾暣鎺ㄧ悊娴佹按绾裤€?""': '    def run(self, source: Path) -> list:\n        """运行完整推理流水线。"""',
    '    def to_dict(self) -> list[dict]:\n        """灏嗙粨鏋滆浆鎹负瀛楀吀鏍煎紡銆?""': '    def to_dict(self) -> list[dict]:\n        """将结果转换为字典格式。"""',
    
    # More general replacements
    '# -*- coding:utf-8 -*-\n# @FileName  :': '# -*- coding:utf-8 -*-\n# @FileName  :',
}

# Also add variants with single line gaps
additional_map = {}
for k, v in list(GARBLED_MAP.items()):
    # Add \r\n variants
    if '\n' in k:
        additional_map[k.replace('\n', '\r\n')] = v
    # Also add the text without @Function prefix
    if '@Function' in k:
        # Keep the @Function but add variations
        pass

GARBLED_MAP.update(additional_map)


def fix_file(filepath):
    """修复单个文件中的乱码。"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        return 0
    
    original = content
    for garbled, correct in GARBLED_MAP.items():
        if garbled in content:
            content = content.replace(garbled, correct)
    
    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        count = sum(1 for g in GARBLED_MAP if g in original)
        return count
    return 0


def main():
    src_dir = os.path.join(BASE_DIR, "apps", "platform", "src", "odp_platform")
    
    py_files = []
    for root, dirs, files in os.walk(src_dir):
        for f in files:
            if f.endswith('.py'):
                py_files.append(os.path.join(root, f))
    
    py_files.sort()
    
    total_count = 0
    fixed_files_list = []
    
    print("=" * 60)
    print("ODPlatform 中文乱码精确修复工具")
    print("=" * 60)
    print(f"\n共 {len(py_files)} 个 .py 文件\n")
    
    for filepath in py_files:
        count = fix_file(filepath)
        if count > 0:
            relpath = os.path.relpath(filepath, BASE_DIR)
            print(f"  [FIXED x{count}] {relpath}")
            fixed_files_list.append(relpath)
            total_count += count
    
    print(f"\n{'=' * 60}")
    print(f"修复完成！共修复 {len(fixed_files_list)} 个文件, {total_count} 处乱码")
    
    return fixed_files_list


if __name__ == "__main__":
    main()