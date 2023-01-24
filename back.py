#!/usr/local/bin/python3.7
# -*- coding: utf-8 -*-
#本番用設定
import os
filepath = '/Users/username/Documents/python/'
local = True if os.path.exists(filepath) == True else False

if local == True:
    import sys
    sys.path.append('/Users/username/Library/Python/3.8/lib/python/site-packages')
    
from datetime import datetime, timezone
import pandas as pd
import ccxt
from pprint import pprint
import math

#--------------------------------
# 移動平均（MA）を取得する関数
#--------------------------------

def MA(m,c,t,l,s):#移動平均(マーケット,ペア,時間足,期間,何足前まで)
    now = datetime.now(timezone.utc)
    now = now.timestamp()

    if t == '1m':
        since_count = 60 * (l + s)
    if t == '3m':
        since_count = 60 * 3 * (l + s)
    if t == '5m':
        since_count = 60 * 5 * (l + s)
    if t == '15m':
        since_count = 60 * 15 * (l + s)
    elif t == '1h':
        since_count = 60 * 60 * (l + s)
    elif t == '1d':
        since_count = 60 * 60 * 24 * (l + s)

    since = int((now - since_count) * 1000)
    timest = m.fetch_ohlcv(c,timeframe=t,since=since,limit=l,params={'reverse': True})
    total = 0

    for index,item in enumerate(timest):
        total = total + item[4]
    ma = total / len(timest)
    return ma

#--------------------------------
# dataFrameを作成する関数
#--------------------------------
def getCCXTData(pear_coin,interval,exchange,since):

    dataFile = exchange.fetch_ohlcv(pear_coin, timeframe = interval,limit=200,since = since, params={'reverse': False})
    dataFrame = pd.DataFrame(data=dataFile, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    return dataFrame

#--------------------------------
# EMAを作成する関数
#--------------------------------
def createEMA(df,s,t):
    time = 199 - t
    df['e99'] = pd.Series.ewm(df['close'], span=s, adjust=False ).mean()
    return df['e99'][time]
#--------------------------------
# dataFrameからMACDを取得する関数
#--------------------------------
def createMACD(df,s1,s2,s,t):#dataFrame,長期スパン,短期スパン,シグナル,取得足
    st = 200 -1 - t
    ed = 200 - t
    df['e26'] = pd.Series.ewm(df['close'], span=s1, adjust=False ).mean()
    df['e12'] = pd.Series.ewm(df['close'], span=s2, adjust=False ).mean()
    df['MACD'] = df['e12'] - df['e26']

    signal = df['MACD'].ewm(span=s, adjust=False).mean()
    data_signal = signal[st:ed]#一個だけ取り出す
    data_signal = data_signal.iloc[-1]

    data_MACD = df[st:ed]['MACD']#一個だけ取り出す
    data_MACD = data_MACD.iloc[-1]

    return [munber(4,data_MACD),munber(4,data_signal)]

#--------------------------------
# rsi取得
#--------------------------------
def rsi(df, periods, ema, upper, under):
    sign = 0
    close_delta = df['close'].diff()

    up = close_delta.clip(lower=0)
    down = -1 * close_delta.clip(upper=0)
    
    if ema == True:
        ma_up = up.ewm(com = periods - 1, adjust=True, min_periods = periods).mean()
        ma_down = down.ewm(com = periods - 1, adjust=True, min_periods = periods).mean()
    else:
        ma_up = up.rolling(window = periods, adjust=False).mean()
        ma_down = down.rolling(window = periods, adjust=False).mean()
        
    rsi = ma_up / ma_down
    rsi = 100 - (100/(1 + rsi))
    rsi = rsi[199]

    if rsi >= upper:#上げすぎ
        sign = 1
    elif  rsi <= under:#下げすぎ
        sign = 2
    return sign

#--------------------------------
# 板での指値売買
#--------------------------------
#Bid=「売る」Ask=「買う」
def limit_order(setamount,pearcoin,markets,bidsasks):

    #ポジション確認
    position = markets.fetchPosition(pearcoin)
    position_size = float(position["info"]["size"])#ポジション
    end_amount = 0#購入分
    end_amount_price = 0#購入分最終価格
    count = 0
    value = markets.fetchOrderBook(pearcoin)#板取得

    if bidsasks == 'bids' :
        setamount = position_size

    while end_amount < setamount:
        end_amount = end_amount + value[bidsasks][count][1]#買値
        count = count + 1
        if count >= 10:
            break
    end_amount_price = value[bidsasks][count-1][0]

    return end_amount_price

#--------------------------------
# 小数点切り捨て数値を取得する関数
#--------------------------------
def munber(n,x):#指定小数点切り捨て(小数点,数字)
    y = math.floor(x * 10 ** n) / (10 ** n)
    return y

#--------------------------------
# historyファイルに記載
#--------------------------------
def Write(item,t):
    pprint(item)
    f = open(t, 'a')
    write = item + '  '
    f.write(write)
    f.close()