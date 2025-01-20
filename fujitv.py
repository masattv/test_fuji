import streamlit as st
import yfinance as yf
import pandas as pd
import altair as alt
from datetime import datetime

st.title("テレビ局株価モニター（可変期間＆チェックボックス切替）")

# -------------------------------
# 1. パラメータ選択UI
# -------------------------------
# 期間と足を選択ボックスで可変にする
period_options = ["1mo", "3mo", "6mo", "1y", "5y"]  # 例
interval_options = ["1d", "1wk", "1mo"]             # 例

period = st.selectbox("期間（period）を選択", period_options, index=0)
interval = st.selectbox("足（interval）を選択", interval_options, index=0)

# -------------------------------
# 2. チェックボックスで表示するテレビ局を選択
# -------------------------------
all_stocks = {
    "フジテレビ (Fuji Media Holdings)": "4676.T",
    "日本テレビ (Nippon Television)": "9404.T",
    "テレビ朝日 (TV Asahi)": "9409.T",
    "TBSホールディングス (TBS)": "9401.T",
}

selected_stocks = {}
for company_name, symbol in all_stocks.items():
    # 第3引数で default=True にしておくと最初からチェック入り
    if st.checkbox(company_name, value=True):
        selected_stocks[company_name] = symbol

# -------------------------------
# 3. 選択された銘柄の株価をまとめて取得
# -------------------------------
df_list = []
for company_name, symbol in selected_stocks.items():
    ticker = yf.Ticker(symbol)
    data = ticker.history(period=period, interval=interval)

    if data.empty:
        continue
    
    # 日付を列に (reset_index)
    data = data.reset_index()

    # 会社名を列に追加
    data["Company"] = company_name

    # 必要な列だけ抽出
    data = data[["Date", "Close", "Company"]]
    data = data.rename(columns={"Close": "Price"})

    df_list.append(data)

if len(df_list) == 0:
    st.warning("株価データを取得できませんでした。銘柄選択または期間の設定を見直してください。")
else:
    # concatして一つのDataFrameに
    df_combined = pd.concat(df_list, ignore_index=True)

    # -------------------------------
    # 4. Altairで重ね描画 (縦軸0固定)
    # -------------------------------
    min_price = df_combined["Price"].min()
    max_price = df_combined["Price"].max()

    # 縦軸の下限を0に固定しつつ、上限は自動または少しマージン
    # 例: domain = [0, max_price * 1.05]
    y_scale = alt.Scale(domain=[0, max_price * 1.05])

    chart = (
        alt.Chart(df_combined)
        .mark_line()
        .encode(
            x=alt.X("Date:T", title="日付"),
            y=alt.Y("Price:Q", title="株価（円）", scale=y_scale),
            color=alt.Color("Company:N", title="会社名"),
            tooltip=["Date:T", "Company:N", "Price:Q"]
        )
        .properties(width=700, height=400)
        .interactive()  # グラフ上でドラッグして拡大などできる
    )

    st.altair_chart(chart, use_container_width=True)

    # -------------------------------
    # 5. 表示するテーブルなど
    # -------------------------------
    # 最新値を表示（Companyごとに groupby して最新日付の行を抽出）
    df_latest = df_combined.groupby("Company").tail(1)
    df_latest = df_latest[["Company", "Date", "Price"]].sort_values("Company")
    st.write("**各社の最新株価**", df_latest)

    # 最終更新時刻
    st.write(f"最終更新: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
