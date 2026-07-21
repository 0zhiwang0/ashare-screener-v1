from __future__ import annotations

import numpy as np
import pandas as pd


def _clip_score(value: pd.Series) -> pd.Series:
    return value.fillna(0).clip(lower=0, upper=100)


def build_screen(
    market_df: pd.DataFrame,
    fund_df: pd.DataFrame,
    min_pct: float,
    max_pct: float,
    min_turnover: float,
    min_volume_ratio: float,
    min_amount_yi: float,
    min_main_inflow_wan: float,
    exclude_st: bool = True,
) -> pd.DataFrame:
    df = market_df.merge(fund_df, on="代码", how="left")
    df["成交额_亿元"] = df["成交额"] / 1e8
    df["主力净流入_万元"] = df["主力净流入_元"] / 1e4

    if exclude_st:
        bad_name = df["名称"].astype(str).str.contains(r"ST|退", case=False, regex=True, na=False)
        df = df.loc[~bad_name].copy()

    # 排除明显不可交易或数据异常项目
    df = df.loc[
        df["最新价"].notna()
        & (df["最新价"] > 0)
        & df["涨跌幅"].between(min_pct, max_pct, inclusive="both")
        & (df["换手率"] >= min_turnover)
        & (df["量比"] >= min_volume_ratio)
        & (df["成交额_亿元"] >= min_amount_yi)
        & (df["主力净流入_万元"] >= min_main_inflow_wan)
    ].copy()

    # 第一版评分：重视量价活跃度、涨幅位置与主力流入匹配。
    pct_center = 3.5
    pct_score = 100 - (df["涨跌幅"] - pct_center).abs() * 18
    volume_score = (df["量比"] - 1) * 35 + 45
    turnover_score = np.log1p(df["换手率"].clip(lower=0)) / np.log(11) * 100
    amount_score = np.log1p(df["成交额_亿元"].clip(lower=0)) / np.log(31) * 100

    df["技术评分"] = _clip_score(
        pct_score * 0.30
        + volume_score * 0.35
        + turnover_score * 0.20
        + amount_score * 0.15
    )

    inflow_score = np.sign(df["主力净流入_万元"]) * np.log1p(df["主力净流入_万元"].abs()) / np.log(100001) * 100
    ratio_score = df["主力净流入占比"] * 4 + 50
    df["资金评分"] = _clip_score(inflow_score * 0.65 + ratio_score * 0.35)

    # 资金与技术双确认，资金面稍微更高权重。
    df["综合评分"] = _clip_score(df["技术评分"] * 0.45 + df["资金评分"] * 0.55)

    return df.sort_values(
        ["综合评分", "主力净流入_万元", "成交额_亿元"],
        ascending=[False, False, False],
    ).reset_index(drop=True)
