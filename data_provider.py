from __future__ import annotations

import time
import pandas as pd
import requests


MARKET_FILTER = "m:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23"
HOSTS = (
    "https://82.push2.eastmoney.com",
    "https://push2.eastmoney.com",
    "https://33.push2.eastmoney.com",
)
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/124 Safari/537.36",
    "Referer": "https://quote.eastmoney.com/",
    "Accept": "application/json,text/plain,*/*",
}


def _normalize_code(series: pd.Series) -> pd.Series:
    return series.astype(str).str.extract(r"(\d{6})", expand=False).str.zfill(6)


def _fetch_pages(fields: str, sort_field: str, page_size: int = 800) -> list[dict]:
    """分批抓取并轮换线路，避免云服务器一次拉取全市场时被断开。"""
    last_error = None
    for host in HOSTS:
        session = requests.Session()
        session.headers.update(HEADERS)
        rows = []
        try:
            page = 1
            while True:
                response = session.get(
                    f"{host}/api/qt/clist/get",
                    params={
                        "pn": page, "pz": page_size, "po": 1, "np": 1,
                        "fltt": 2, "invt": 2, "fid": sort_field,
                        "fs": MARKET_FILTER, "fields": fields,
                    },
                    timeout=(6, 20),
                )
                response.raise_for_status()
                data = (response.json().get("data") or {})
                batch = data.get("diff") or []
                rows.extend(batch)
                total = int(data.get("total") or len(rows))
                if not batch or len(rows) >= total:
                    return rows
                page += 1
                time.sleep(0.15)
        except Exception as exc:
            last_error = exc
            time.sleep(0.5)
        finally:
            session.close()
    raise RuntimeError(f"行情多线路均连接失败：{last_error}")


def _to_numeric(df: pd.DataFrame, text_columns: set[str]) -> pd.DataFrame:
    for col in df.columns:
        if col not in text_columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def fetch_realtime_market() -> pd.DataFrame:
    rows = _fetch_pages(
        "f2,f3,f5,f6,f7,f8,f10,f12,f14,f15,f16,f17,f18", "f3"
    )
    df = pd.DataFrame(rows).rename(columns={
        "f12": "代码", "f14": "名称", "f2": "最新价", "f3": "涨跌幅",
        "f5": "成交量", "f6": "成交额", "f7": "振幅", "f8": "换手率",
        "f10": "量比", "f15": "最高", "f16": "最低",
        "f17": "今开", "f18": "昨收",
    })
    if df.empty:
        raise RuntimeError("实时行情接口未返回数据")
    required = ["代码", "名称", "最新价", "涨跌幅", "成交额", "量比", "换手率"]
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise RuntimeError(f"实时行情字段发生变化，缺少：{missing}")
    df["代码"] = _normalize_code(df["代码"])
    return _to_numeric(df, {"代码", "名称"})


def fetch_fund_flow_rank(indicator: str = "今日") -> pd.DataFrame:
    rows = _fetch_pages("f12,f14,f62,f184", "f62")
    df = pd.DataFrame(rows).rename(columns={
        "f12": "代码", "f62": "主力净流入_元", "f184": "主力净流入占比"
    })
    if df.empty:
        raise RuntimeError("资金流接口未返回数据")
    df["代码"] = _normalize_code(df["代码"])
    df = _to_numeric(df, {"代码", "名称"})
    return df[["代码", "主力净流入_元", "主力净流入占比"]].drop_duplicates("代码")
