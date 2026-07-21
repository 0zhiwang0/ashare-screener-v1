from __future__ import annotations

import pandas as pd
import akshare as ak


def _normalize_code(series: pd.Series) -> pd.Series:
    return series.astype(str).str.extract(r"(\d{6})", expand=False).str.zfill(6)


def fetch_realtime_market() -> pd.DataFrame:
    """获取沪深京 A 股实时行情。"""
    df = ak.stock_zh_a_spot_em()
    if df is None or df.empty:
        raise RuntimeError("实时行情接口未返回数据")

    rename_map = {
        "代码": "代码",
        "名称": "名称",
        "最新价": "最新价",
        "涨跌幅": "涨跌幅",
        "成交量": "成交量",
        "成交额": "成交额",
        "振幅": "振幅",
        "最高": "最高",
        "最低": "最低",
        "今开": "今开",
        "昨收": "昨收",
        "量比": "量比",
        "换手率": "换手率",
        "市盈率-动态": "市盈率_动态",
        "市净率": "市净率",
        "总市值": "总市值",
        "流通市值": "流通市值",
        "涨速": "涨速",
        "5分钟涨跌": "五分钟涨跌",
        "60日涨跌幅": "六十日涨跌幅",
        "年初至今涨跌幅": "年初至今涨跌幅",
    }
    df = df.rename(columns=rename_map)
    required = ["代码", "名称", "最新价", "涨跌幅", "成交额", "量比", "换手率"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise RuntimeError(f"实时行情字段发生变化，缺少：{missing}")

    df["代码"] = _normalize_code(df["代码"])
    for col in df.columns:
        if col not in {"代码", "名称"}:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def fetch_fund_flow_rank(indicator: str = "今日") -> pd.DataFrame:
    """获取个股资金流排名。AKShare 支持的 indicator 通常包括 今日、3日、5日、10日。"""
    try:
        df = ak.stock_individual_fund_flow_rank(indicator=indicator)
    except TypeError:
        df = ak.stock_individual_fund_flow_rank(indicator)

    if df is None or df.empty:
        raise RuntimeError("资金流接口未返回数据")

    df["代码"] = _normalize_code(df["代码"])
    rename_candidates = {
        "主力净流入-净额": "主力净流入_元",
        "主力净流入-净占比": "主力净流入占比",
        "今日主力净流入-净额": "主力净流入_元",
        "今日主力净流入-净占比": "主力净流入占比",
        "主力净流入": "主力净流入_元",
        "主力净流入占比": "主力净流入占比",
    }
    df = df.rename(columns={k: v for k, v in rename_candidates.items() if k in df.columns})

    if "主力净流入_元" not in df.columns:
        possible = [c for c in df.columns if "主力净流入" in str(c) and ("净额" in str(c) or str(c).endswith("流入"))]
        if possible:
            df = df.rename(columns={possible[0]: "主力净流入_元"})
    if "主力净流入占比" not in df.columns:
        possible = [c for c in df.columns if "主力净流入" in str(c) and "占比" in str(c)]
        if possible:
            df = df.rename(columns={possible[0]: "主力净流入占比"})

    for col in df.columns:
        if col not in {"代码", "名称", "所属板块"}:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    if "主力净流入_元" not in df.columns:
        raise RuntimeError(f"资金流字段发生变化，当前字段：{list(df.columns)}")
    if "主力净流入占比" not in df.columns:
        df["主力净流入占比"] = pd.NA

    return df[["代码", "主力净流入_元", "主力净流入占比"]].drop_duplicates("代码")
