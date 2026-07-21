from __future__ import annotations

import streamlit as st
import pandas as pd

from data_provider import fetch_realtime_market, fetch_fund_flow_rank
from screener import build_screen

st.set_page_config(page_title="A股手机选股 V1", layout="wide")
st.title("A股手机选股 V1")
st.caption("实时行情 + 资金面 + 技术/交易特征初筛。仅作研究工具，不构成投资建议。")

with st.sidebar:
    st.header("筛选条件")
    min_pct = st.number_input("最低涨幅 %", value=0.5, step=0.5)
    max_pct = st.number_input("最高涨幅 %", value=7.0, step=0.5)
    min_turnover = st.number_input("最低换手率 %", value=1.5, step=0.5)
    min_volume_ratio = st.number_input("最低量比", value=1.2, step=0.1)
    min_amount_yi = st.number_input("最低成交额（亿元）", value=1.0, step=0.5)
    min_main_inflow_wan = st.number_input("最低主力净流入（万元）", value=500.0, step=100.0)
    exclude_st = st.checkbox("排除 ST / *ST / 退市整理", value=True)
    top_n = st.slider("显示数量", 10, 100, 30, 10)

refresh = st.button("刷新并选股", type="primary", use_container_width=True)

@st.cache_data(ttl=20, show_spinner=False)
def load_data():
    market = fetch_realtime_market()
    fund = fetch_fund_flow_rank()
    return market, fund

if refresh:
    st.cache_data.clear()

try:
    with st.spinner("正在获取实时行情与资金流数据……"):
        market_df, fund_df = load_data()

    result = build_screen(
        market_df=market_df,
        fund_df=fund_df,
        min_pct=min_pct,
        max_pct=max_pct,
        min_turnover=min_turnover,
        min_volume_ratio=min_volume_ratio,
        min_amount_yi=min_amount_yi,
        min_main_inflow_wan=min_main_inflow_wan,
        exclude_st=exclude_st,
    ).head(top_n)

    c1, c2, c3 = st.columns(3)
    c1.metric("实时股票数", len(market_df))
    c2.metric("资金流记录数", len(fund_df))
    c3.metric("入选数量", len(result))

    if result.empty:
        st.warning("当前没有股票满足条件，请适当放宽筛选参数。")
    else:
        display_cols = [
            "代码", "名称", "最新价", "涨跌幅", "量比", "换手率",
            "成交额_亿元", "主力净流入_万元", "主力净流入占比",
            "技术评分", "资金评分", "综合评分"
        ]
        st.dataframe(
            result[display_cols],
            use_container_width=True,
            hide_index=True,
            column_config={
                "最新价": st.column_config.NumberColumn(format="%.2f"),
                "涨跌幅": st.column_config.NumberColumn(format="%.2f%%"),
                "量比": st.column_config.NumberColumn(format="%.2f"),
                "换手率": st.column_config.NumberColumn(format="%.2f%%"),
                "成交额_亿元": st.column_config.NumberColumn(format="%.2f"),
                "主力净流入_万元": st.column_config.NumberColumn(format="%.0f"),
                "主力净流入占比": st.column_config.NumberColumn(format="%.2f%%"),
                "综合评分": st.column_config.ProgressColumn(min_value=0, max_value=100),
            },
        )

        csv = result.to_csv(index=False).encode("utf-8-sig")
        st.download_button(
            "下载筛选结果 CSV",
            data=csv,
            file_name="a_share_screen_result.csv",
            mime="text/csv",
            use_container_width=True,
        )

        st.subheader("复制给 ChatGPT 的分析包")
        selected = st.selectbox(
            "选择股票",
            options=result["代码"].tolist(),
            format_func=lambda x: f"{x} {result.loc[result['代码'] == x, '名称'].iloc[0]}",
        )
        row = result.loc[result["代码"] == selected].iloc[0]
        prompt = f"""请按我的选股框架，对以下股票进行技术面及资金面二次分析：

股票：{row['代码']} {row['名称']}
最新价：{row['最新价']:.2f}
涨跌幅：{row['涨跌幅']:.2f}%
量比：{row['量比']:.2f}
换手率：{row['换手率']:.2f}%
成交额：{row['成交额_亿元']:.2f}亿元
主力净流入：{row['主力净流入_万元']:.0f}万元
主力净流入占比：{row['主力净流入占比']:.2f}%
技术评分：{row['技术评分']:.0f}
资金评分：{row['资金评分']:.0f}
综合评分：{row['综合评分']:.0f}

请重点判断：
1. 是否属于开盘后真实放量，而不是高开诱多；
2. 主力资金流入是否与价格、换手率匹配；
3. 是否适合列入当日尾盘候选池；
4. 主要风险及需要继续观察的确认条件。
"""
        st.code(prompt, language=None)

except Exception as exc:
    st.error(f"数据获取失败：{exc}")
    st.info("公开数据接口可能临时限流或变更。建议稍后重试，并在正式使用时部署备用数据源与本地缓存。")
