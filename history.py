#python history.py
import os
import pandas as pd
import ccxt
import json
import time
import datetime

def createHistory():
    # 取引所に接続する
    market = eval("ccxt." + "bybit" + "()")
    market.apiKey = ''
    market.secret = ''
    market.set_sandbox_mode(True)#テストネットモード
    symbol_pair  = 'ETHUSDT'
    timeframe = '5m'
    loop = 20#何周分(200*?)
    old_day = 200#何日前から(標準0)

    if timeframe == '1m':
        time_sum = 60 * 1000
    if timeframe == '3m':
        time_sum = 60 * 3 * 1000
    if timeframe == '5m':
        time_sum = 60 * 5 * 1000
    if timeframe == '15m':
        time_sum = 60 * 15 * 1000
    elif timeframe == '1h':
        time_sum = 60 * 60 * 1000
    elif timeframe == '1d':
        time_sum = 60 * 60 * 24 * 1000
    time_sum = time_sum * 200#200足

    old_day = old_day * 60 * 60 * 24 * 1000

    # CSVファイルが既にあれば読み出す。
    fname = symbol_pair + ".csv"
    os.remove(fname)
    if os.path.exists(fname):
        dfcsv = pd.read_csv(fname)
    else:
        dfcsv = pd.DataFrame()

    # pandasでローソク足を読み込む。
    ldata = list()
    candles = ""
    candle = market.fetch_ohlcv(symbol_pair, timeframe = timeframe, since=None, limit=1)
    time = candle[0][0]#現在
    time_old = time - (time_sum * loop) - old_day#最過去

    for num in range(loop):
        try:
            candles = market.fetch_ohlcv(symbol_pair, timeframe = timeframe, since=time_old, limit=200)
        except:
            print(market, "ローソク足を取得できません。")
            exit()
        time_old = time_old + time_sum

        for c in candles:
            ldata.append([float(c[0]), float(c[1]), float(c[2]), float(c[3]), float(c[4]), float(c[5])])

        col = ["timestamp", "open", "high", "low", "close", "volume"]
        dfcandles = pd.DataFrame(ldata, columns=col)

        # CSVとローソク足を結合し、重複データを削除する。
        # これにより、新しいレコードが日々追加されていく。
        dfnew = pd.concat([dfcsv, dfcandles])
        print("重複行数", dfnew.duplicated().sum())
        dfnew = dfnew.drop_duplicates()

    # データをCSVに保存する。ヘッダあり、索引なし。
    dfnew.to_csv(fname, header=True, index=False)

#end