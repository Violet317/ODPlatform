from __future__ import annotations

import logging

from sklearn.model_selection import train_test_split

from odp_platform.common.constants import DEFAULT_RANDOM_STATE, RATE_EPSILON
from odp_platform.data_pipeline.split.manifest import PairList, SplitManifest

logger = logging.getLogger(__name__)


def split_pairs(
    pairs: PairList,
    train_rate: float = 0.8,
    val_rate: float = 0.1,
    random_state: int = DEFAULT_RANDOM_STATE,
) -> SplitManifest:
    """把 pairs 划分为 train / val / test 三组。

    test_rate 由 1.0 - train_rate - val_rate 自动算出。
    """
    test_rate = 1.0 - train_rate - val_rate
    if not (0 <= train_rate <= 1 and 0 <= val_rate <= 1 and 0 <= test_rate <= 1):
        raise ValueError(
            f"比例越界: train={train_rate}, val={val_rate}, test={test_rate:.4f}"
        )

    manifest = SplitManifest(
        train_rate=train_rate,
        val_rate=val_rate,
        test_rate=test_rate,
        random_state=random_state,
    )

    n = len(pairs)
    if n == 0:
        return manifest

    # 边界1: 样本数小于3
    if n < 3:
        logger.warning(f"split_pairs: 样本数 {n} 小于3, 全部划分为 train")
        manifest.train = list(pairs)
        return manifest

    # 边界2: train_rate = 1
    if train_rate >= 1 - RATE_EPSILON:
        manifest.train = list(pairs)
        return manifest

    # 第一次划分: train / temp
    images = [p[0] for p in pairs]
    labels = [p[1] for p in pairs]

    train_i, temp_i, train_l, temp_l = train_test_split(
        images, labels, train_size=train_rate, random_state=random_state,
    )
    manifest.train = list(zip(train_i, train_l))

    if not temp_i:
        return manifest

    # 边界3: val + test = 0 (rare)
    remaining = val_rate + test_rate
    if remaining < RATE_EPSILON or len(temp_i) < 2:
        manifest.val = list(zip(temp_i, temp_l))
        return manifest

    # 边界4: test_rate = 0
    if test_rate < RATE_EPSILON:
        manifest.val = list(zip(temp_i, temp_l))
        return manifest

    # 边界5: val_rate = 0
    if val_rate < RATE_EPSILON:
        manifest.test = list(zip(temp_i, temp_l))
        return manifest

    # 第二次划分: val / test
    val_size = val_rate / remaining
    val_i, test_i, val_l, test_l = train_test_split(
        temp_i, temp_l, train_size=val_size, random_state=random_state,
    )
    manifest.val = list(zip(val_i, val_l))
    manifest.test = list(zip(test_i, test_l))

    return manifest