import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import requests


st.set_page_config(
    page_title = "Pulsechain Ratios",
    layout = "wide"
)

# _________________________________________________________________________________
# Functions

def get_pulse_chart(ca):
    url = f"https://www.dextools.io/shared/search/pair?chains=pulse&query={ca}&strict=true"

    headers = {
        "referer": "https://www.dextools.io/",
        "user-agent": "Niggachain Layer 2 Built on Solana",
    }

    response = requests.get(url, headers=headers)

    results = response.json()["results"][0]["id"]["pair"]

    name = response.json()["results"][0]['symbol']
    print(f"Fetching LP {results} for {name}...")
    url = f"https://api.geckoterminal.com/api/v2/networks/pulsechain/pools/{results}/ohlcv/{timeframe}"
    params = {
        "aggregate": aggregate,
        "limit": "1000",
        "currency": "usd",
        "token": ca
    }

    response = requests.get(url, headers={"accept": "application/json"}, params=params)
    values = response.json()['data']['attributes']['ohlcv_list']

    df = pd.DataFrame(values, columns=['time', 'o', 'h', 'l', 'c', 'v']).set_index('time').drop(columns=['v'])

    return df, name

def ratio(df1, df2):
    """
    Gets the ratio for 2 dataframes
    Trying to copy what TV does with custom tickers
    Not sure if i did it correctly (dont have premium to check) but it looks fine 
    """
    merged = pd.merge(df1, df2, on='time', suffixes=('_1', '_2'), how='outer')

    for index, row in merged.iterrows():
        for col in list(merged.columns):
            if pd.isna(row[col]):
                previous_index = merged.index.get_loc(index) - 1
                if previous_index < 0:
                    merged.at[index, col] = 0  # or some other default value
                else:
                    merged.at[index, col] = merged.iloc[previous_index][col]
    
    for col in ['o', 'h', 'l', 'c']:
        merged[f'{col}'] = merged[f'{col}_1'] / merged[f'{col}_2']

    # Adjust wicks
    for index, row in merged.iterrows():
        if row['l'] > row['h']:
            merged.at[index, 'l'] = row['h']
            merged.at[index, 'h'] = row['l']

    for index, row in merged.iterrows():
        if row['o'] < row['c']:  # Up candle
            if row['l'] > row['o']:
                merged.at[index, 'l'] = row['o']
            if row['h'] < row['c']:
                merged.at[index, 'h'] = row['c']
        else:  # Down candle
            if row['l'] > row['c']:
                merged.at[index, 'l'] = row['c']
            if row['h'] < row['o']:
                merged.at[index, 'h'] = row['o']

    # Remove the first bars that are 0 until a valid bar is found
    for i in range(len(merged)):
        if (merged.iloc[i]['o'] != 0) & (merged.iloc[i]['h'] != 0) & (merged.iloc[i]['l'] != 0) & (merged.iloc[i]['c'] != 0):
            merged = merged.iloc[i:]
            break

    return merged[[ 'o', 'h', 'l', 'c']]

#_________________________________________________________________________________
# Inputs

coins = ["T-Bill","FED","HOX","ATROPA","TEDDY BEAR", "GBABY", "BFF", "HUG", "pWBTC", "pDAI", "pUSDT"]

pairs = {
    "T-Bill": "0x463413c579d29c26d59a65312657dfce30d545a1",
    "FED": "0x1d177cb9efeea49a8b97ab1c72785a3a37abc9ff",
    "HOX": "0xf18b09a5b358b720f23d736163d328dba0bddf41",
    "ATROPA": "0xcc78a0acdf847a2c1714d2a925bb4477df5d48a6",
    "TEDDY BEAR": "0xd6c31ba0754c4383a41c0e9df042c62b5e918f6d",
    "GBABY": "0x9dc72e4ad4d11841993f6c0a087f5b9fb458aa7c",
    "BFF": "0xe35a842eb1edca4c710b6c1b1565ce7df13f5996",
    "KISS": "0x497625f04ce1788154cfb86ef31ce221194588ce",
    "HUG": "0x788d4d240c555e49fe45fec6d172babfff19a35d",
    "pWBTC": "0x2260fac5e5542a773aa44fbcfedf7c193bc2c599",
    "pDAI": "0x6b175474e89094c44da98b954eedeac495271d0f",
    "pUSDT": "0xdac17f958d2ee523a2206206994597c13d831ec7"
}


col1, col2, col3, col4 = st.columns(4)

with col1:
    asset1 = st.selectbox(label="1st Coin", options=coins)
with col2:
    asset2 = st.selectbox(label="2nd Coin", options=coins)
with col3:
    timeframe = st.selectbox(label="Timeframe", options=["day", "hour", "minute"])
with col4:
    aggregate = st.number_input(label="Period", min_value=1, max_value=60) # options : day 1 | hour 1, 4, 12 | minute 1, 5, 15 | Default is 1

asset1_ca = pairs[asset1]
asset2_ca = pairs[asset2]

#_________________________________________________________________________________
# Chart

if True:
    asset1_df, asset1_name = get_pulse_chart(asset1_ca) 
    asset2_df, asset2_name = get_pulse_chart(asset2_ca)

    df = ratio(asset1_df, asset2_df)

    index = pd.to_datetime(pd.Series(df.index), unit='s')

    fig = go.Figure(go.Candlestick(
        x=index,
        open=df['o'],
        high=df['h'],
        low=df['l'],
        close=df['c'],
        name=f'{asset1_name}/{asset2_name} Ratio'
    ))
    fig.update_layout(
        height=1000,  # Increase the height of the chart
        margin=dict(l=20, r=20, t=20, b=20),  # Remove all margins (left, right, top, bottom)
        xaxis_rangeslider_visible=True,
        plot_bgcolor='black',
        paper_bgcolor='black',
        font=dict(color="white", style="italic"),
        yaxis_type="log",
        yaxis2=dict(title="Volume"),
        yaxis3=dict(title="Equity"),
        showlegend=True,
        title={
            'text': f"<b>SkÅ«by's Shitty Ratio</b><br>{asset1_name}/{asset2_name} | TF: {aggregate}{timeframe}",
            'y': 0.97,
            'x': 0.5,
            'xanchor': 'center',
            'yanchor': 'top'
        },
    )

    fig.update_xaxes(showgrid=False, zeroline=False)
    fig.update_yaxes(showgrid=False, fixedrange=False)
    st.plotly_chart(fig)
