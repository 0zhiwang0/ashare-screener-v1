# A股手机选股 V1

这是一个无需 MCP 的手机端 A 股选股原型：

- AKShare 获取沪深京 A 股实时行情
- AKShare 获取个股资金流排名
- Streamlit 提供手机网页
- 根据涨幅、量比、换手率、成交额、主力净流入进行第一轮筛选与评分
- 自动生成可复制给 ChatGPT 的结构化分析包

## 本地运行

建议 Python 3.11：

```bash
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

浏览器打开终端显示的地址。

## 部署到 Streamlit Community Cloud

1. 新建一个 GitHub 仓库。
2. 将本目录所有文件上传至仓库根目录。
3. 登录 Streamlit Community Cloud。
4. 选择该仓库，入口文件填 `app.py`。
5. Python 版本建议选择 3.11。
6. 部署完成后，用手机打开生成的网址。

## 当前版本的边界

1. 公开行情源可能限流、滑块验证或临时改变字段。
2. “主力资金”是数据供应商根据成交单分类估算，不等同于可核验的机构真实账户流向。
3. V1 只做盘中横截面初筛，尚未加入历史 K 线、均线、MACD、突破形态、板块联动和分时持续性。
4. 不建议仅凭单次主力净流入进行交易。
5. 本工具仅用于研究，不构成投资建议。

## 下一版建议

- 历史 K 线缓存
- MA5/10/20、MACD、RSI、20 日突破
- 9:35、9:45、10:00 多时点快照比较
- 资金流连续性而非单点值
- 板块强度和个股相对强度
- 东方财富接口失败时自动切换新浪或付费数据源
- 用户自定义选股规则和评分权重
