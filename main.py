#python main2_c.py
#!/usr/local/bin/python3.7
# -*- coding: utf-8 -*-

#本番用設定
import os
filepath = '/Users/username/Documents/python/'
local = True if os.path.exists(filepath) == True else False

if local == True:
    import sys
    sys.path.append('/Users/username/Library/Python/3.8/lib/python/site-packages')

import datetime
import ccxt
from pprint import pprint
import back
import history
import pandas as pd

history.createHistory()

# 過去データを読み込む。
fname = "ETHUSDT" + ".csv"
df_list = pd.read_csv(fname)
set_df_range = 4000
set_df_range_old = 200#過去統計分
n = 0

#-------------------------------------------------------
#API
#-------------------------------------------------------
market = ccxt.bybit()
market.apiKey = ''
market.secret = ''
market.set_sandbox_mode(True)#テストネットモード

if local == True:
    logfile = "/log.txt"
    hisfile = "/history.txt"
else:
    logfile = "/log.txt"
    hisfile = "/history.txt"

#テキスト初期化
#総利益、売買、保持数、ポジション位置、日付, トレード数、勝数
row = '0/short/0/0/0/0/0'
f = open(logfile, "w")
f.write(str(row))
f.close()

row = ''
f = open(hisfile, "w")
f.write(str(row))
f.close()

entry = 0#エントリー数
entry_re = 0#勝数

#-------------------------------------------------------
#初期化
#-------------------------------------------------------
for num in range(0,set_df_range-set_df_range_old):
    mun_time = num + set_df_range_old

    #初期設定
    lock = False#購入フラグ
    pear_coin = "ETHUSDT"
    set_amount = 10.0#購入数量

    trend = 0#トレンド(上昇1,下降2)
    cross = 0#クロス(デッド1,ゴールデン2)
    set_side_create = ''#ポジション注文用
    set_side_close = ''#ポジション決済用

    is_result = 0#固定された利益損益確定用フラグ
    get_result = 20#固定された利益
    out_result = -10#固定された損益

    #時間の選択
    interval = "5m"
    interval_15m = "1d"
    #EMA用
    range_span_now =0
    up1_duwn2 = 0 
    follow = 0
    #移動平均線用
    chart_range_1 = 12
    chart_range_2 = 64
    chart_range_3 = 99
    chart_range_4 = 60
    #MACD用
    macd_range_1 = 30
    macd_range_2 = 90
    macd_signal = 12
    #rsi計算用
    rsi_top = 70
    rsi_bottom = 30
    rsi_span = 14
    #レンジ判定用
    range_span_long_now =1
    range_span_long_old =11
    range_diff = 2.5
    chart_range_long = 99
    
    dt_now = df_list['timestamp'][mun_time]
    dt_now_time = datetime.datetime.fromtimestamp(dt_now/1000)
    dt_price_now = df_list['close'][mun_time]

    #EMA用
    s = 0 + mun_time - set_df_range_old
    e = s + set_df_range_old

    #-------------------------------------------------------
    #分析
    #-------------------------------------------------------
    #t_result = 0#利益
    t_position_num_old = 0

    #テキスト更新
    f = open(logfile, "r")
    row_list = f.read()
    f.close()
    row_list = row_list.split('/')
    #総利益、売買、保持数、ポジション値、日付

    t_result_all = float(row_list[0])#総利益
    t_side = row_list[1]#売買　売り(short)か買いか(long)
    t_position = float(row_list[2])#保持数
    t_position_num = float(row_list[3])#ポジション値

    if t_position_num == 0 :
        t_position_num_old = dt_price_now
    else:
        t_position_num_old = t_position_num

    position_size = t_position
    position_side = t_side

    #ポジション決済用変数
    if position_side == 'long':
        set_side_close = 'sell'
        position_close = 'bids'
        position_result = float(dt_price_now) - t_position_num_old
    else:
        set_side_close = 'buy'
        position_close = 'asks'
        position_result = t_position_num_old - float(dt_price_now)
        
    #200日のdataFrameを作成する関数
    df = df_list[s:e].copy()
    df = df.reset_index()

    #EMA判定
    ema60 = back.createEMA(df,chart_range_4,range_span_now)
    ema99 = back.createEMA(df,chart_range_3,range_span_now)

    #上昇下降
    if ema60 < ema99:#下降
        back.Write("ema_short",hisfile)
        up1_duwn2 = 2
    else:
        back.Write("ema_long",hisfile)
        up1_duwn2 = 1

    #macd計算
    macd_set = back.createMACD(df,macd_range_2,macd_range_1,macd_signal,1)
    macd_set_old = back.createMACD(df,macd_range_2,macd_range_1,macd_signal,2)
    macd = macd_set[0]#macd
    signal = macd_set[1]#シグナル
    macd_old = macd_set_old[0]#過去のmacd
    signal_old = macd_set_old[1]#過去のシグナル
    
    #rsi計算
    rsi_set = back.rsi(df, rsi_span, True, rsi_top, rsi_bottom)#1=上がりすぎ、2=下がりすぎ
    
    #長期足でのレンジ判定
    ema_long = back.createEMA(df,chart_range_long,range_span_long_now)
    ema_long2 = back.createEMA(df,chart_range_long,range_span_long_old)
    isrange = abs(ema_long - ema_long2)

    #macdクロス判定
    if macd < signal :#下降
        back.Write("macd_down",hisfile)
        trend = 1
        set_side_create = 'sell'
        position_create = 'bids'
        if macd_old > signal_old :#デッドクロス
            cross = 1
            back.Write("deadCross",hisfile)

    elif macd > signal:#上昇
        back.Write("macd_up",hisfile)
        trend = 2
        set_side_create = 'buy'
        position_create = 'asks'
        if macd_old < signal_old :#ゴールデンクロス
            cross = 2
            back.Write("goldenCloss",hisfile)

    else:
        trend = 0
        cross = 0
    
    #順張り
    if set_side_create == 'sell' and up1_duwn2 == 1 or set_side_create == 'buy' and up1_duwn2 == 2 :
        follow = 0#逆張り
    else :
        follow = 1#順張り

    #固定された利益損益にタッチした場合
    if position_result >= get_result:
        is_result = 1#利益確定のフラグ
        back.Write("price_result!",hisfile)
    if position_result <= out_result:
        is_result = 2#損益確定のフラグ
        back.Write("price_break!",hisfile)
    
    #-------------------------------------------------------
    #注文
    #-------------------------------------------------------
    t_position_num = dt_price_now#ポジション値

    if lock == False:
        #---------- 購入処理 -----------
        #ゴールデンクロス、デッドクロス、固定利益確定、固定損益確定、rsi範囲外
        if cross == 1 or cross == 2 or is_result == 1 or is_result == 2 or rsi_set != 0:
            back.Write("set_entry!",hisfile)

            #rsi範囲外の場合
            if rsi_set != 0 :
                back.Write("rsi_break!",hisfile)

            #決済注文(ポジションがある場合もしくは固定された利益損益にタッチの場合)
            #----------
            if position_size > 0 or is_result != 0:
                entry = entry + 1
                set_result = set_side_close + " : " + str(position_result)
                back.Write("close " + set_result + position_close,hisfile)

                if set_side_close == 'sell':#総利益
                    t_result_all = t_result_all + (float(dt_price_now) - t_position_num_old)
                    if float(dt_price_now) - t_position_num_old > 0:
                        entry_re = entry_re + 1
                else:
                    t_result_all = t_result_all + (t_position_num_old - float(dt_price_now))
                    if t_position_num_old - float(dt_price_now) > 0:
                        entry_re = entry_re + 1
                t_side = 'other'#売り(short)か買いか(long)
                t_position = 0#ポジション
                position_size = 0

            #新規注文(ポジションがない場合かつ固定利益損益未確定かつrsi範囲内かつ順張りの場合)
            #----------
            if position_size <= 0 and is_result == 0 and rsi_set == 0 and follow == 1:
                back.Write("entry " + set_side_create + position_create,hisfile)

                if set_side_create == 'sell':
                    t_side = 'short'
                else:
                    t_side = 'long'
                t_position = set_amount#ポジション
            
        #---------- 購入処理 -----------

        #---------- 例外処理 -----------
        #---------- 例外処理 -----------

    #出力
    mes1 = "position : " + str(position_size)
    back.Write(mes1,hisfile)

    back.Write(str(dt_now_time) + "\n",hisfile)

    #テキスト更新
    #総利益、売買、保持数、ポジション位置、日付
    row = str(t_result_all) + "/" + str(t_side) + "/" + str(t_position) + "/" + str(t_position_num) + "/" + str(dt_now) + "/" + str(entry) + "/" + str(entry_re)
    f = open(logfile, "w")
    f.write(str(row))
    f.close()
        

#---end