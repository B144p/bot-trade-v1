# Super Trend Indicator
# For timeframe < 1 day

#Login
import ccxt
apiKey    = ""
secret    = "" 
exchange = ccxt.binance  ({'apiKey' : apiKey ,'secret' : secret ,'enableRateLimit': True})

Pair          = "BTC/USDT"        # คู่เทรด
#timeframe     = "5m"              # ช่วงเวลาของกราฟที่จะดึงข้อมูล
limit         = 100               # จำนวนข้อมูลย้อนหลัง       # This indicator must be limit >= 31
Unit_trade    = 0.0001            # ปริมาณการเทรด

################################################################################
#Offset all input
Total_PNL = 1
Buy_Value = 1.0
Sell_Value = 1.0

In_Stock = 0
Out_Stock = 1
Status_Order = "Out_Stock"

first_scan = 0
mult = 1.9
Period_ST = 7

#offset_total_vol = -63599.70            # เอาค่า total spread_vol[-61] มาจาก TradingView  60*5 นาที = ดูย้อน 5 hr
#offset_vpt = 29031.66                   # ย้อนหลัง vpt[-10] แท่งที่ 10 นับจากหลัง  => 9*5 = 45 นาที
#offset_trend = -1                       # ย้อนหลัง trend[-9] => 8*5 = 40 นาที

print("Input Offset Value")
timeframe = input("Timeframe = ")
offset_total_vol = float(input("Offset_Total_Volume [-60] = "))            # เอาค่า total spread_vol[-61] มาจาก TradingView  60*5 นาที = ดูย้อน 5 hr
offset_vpt = float(input("Offset_vpt [-9] = "))                   # ย้อนหลัง vpt[-10] แท่งที่ 10 นับจากหลัง  => 9*5 = 45 นาที
offset_trend = int(input("Offset_Trend [-8] = "))                       # ย้อนหลัง trend[-9] => 8*5 = 40 นาที
sleep = int(input("Sleep (sec) = "))

smooth_lenght = 14
v_spread_lenght = 28
price_spread_lenght = 28

ATR_Period = 14
ATR_Factor = 2

import re
tf=int(re.findall("\d+",timeframe)[0])    #เป็นการแยกเลขออกจาก String #ใช้ได้ในกรณีหน่วย min
#if ... == "h" :                #กรณีหน่วยเป็น hour
# tf *= 60

while True :
  # เรียก ข้อมูลราคา ของสินค้ามาไว้ในรูปแบบ ตาราง 
  import pandas as pd

  # เรียกข้อมูลจาก exchange
  df_ohlcv  = exchange.fetch_ohlcv(Pair ,timeframe=timeframe,limit=limit)                                       # ข้อมูลดิบ
  df_ohlcv  = pd.DataFrame(df_ohlcv, columns =['datetime', 'open','high','low','close','volume'])               # จัด + มีหัวข้อ
  df_ohlcv['datetime']  = pd.to_datetime(df_ohlcv['datetime'], unit='ms')                                       # แปลงเวลา

################################################################################
# Prepare zero array
  src = df_ohlcv
  zero_list = src['close']*0
  small_zero_list = src['close'][0:10]*0
  count = len(src)
  if first_scan == 0 :
    temp_time = src['datetime'][count-1]
    hilow = zero_list
    hilow = zero_list
    vol = zero_list
    openclose = zero_list
    spread_vol = zero_list
    total_spread_vol = zero_list
    temp_total_spread = zero_list
    smooth = zero_list
    '''
    v_spread = small_zero_list
    price_spread = small_zero_list
    shadow = small_zero_list
    out = small_zero_list
    vpt = small_zero_list
    up_lev = small_zero_list
    down_lev = small_zero_list
    mult_lev = small_zero_list
    up_trend = small_zero_list
    down_trend = small_zero_list
    trend = small_zero_list
    st_line = small_zero_list
    '''
    v_spread = src['close'][0:10]*0                 # ถ้าไม่ใช้แบบนี้ ค่า v_spread หลังผ่าน part price_spread ค่าจะเพี้ยน เพราะอะไร ยังไม่ทราบ
    price_spread = src['close'][0:10]*0
    shadow = src['close'][0:10]*0
    out = src['close'][0:10]*0
    vpt = src['close'][0:10]*0
    up_lev = src['close'][0:10]*0
    down_lev = src['close'][0:10]*0
    mult_lev = src['close'][0:10]*0
    up_trend = src['close'][0:10]*0
    down_trend = src['close'][0:10]*0
    trend = src['close'][0:10]*0
    st_line = src['close'][0:10]*0
  else:
    pass
  src = pd.concat([ src , hilow , vol , openclose , spread_vol , total_spread_vol ], axis=1)                                      # รวมข้อมูล
  src.columns = ['datetime', 'open','high','low','close','volume','hilow','vol','openclose','spread_vol','total_spread_vol']      # เปลี่ยนชื่อ column

  ################################################################################
# All Basic Function
  src['hilow'] = ( src['high'] - src['low'] ) * 100
  src['vol'] = src['volume'] / src['hilow']
  src['openclose'] = ( src['close']-src['open'] ) * 100
  src['spread_vol'] = src['openclose'] * src['vol']
  src['total_spread_vol'] = temp_total_spread

  #print(src['spread_vol'])

  ###########################################
# Total Spread_vol
  if first_scan == 0 :                                        # มีไว้ทำ list ของ Total_Spread_vol ย้อนหลัง 60 แท่ง สำหรับการรันครั้งแรก
    temp_total_spread = (src['close']*0) + offset_total_vol                 # มีไว้เพื่อไม่ให้ขึ้น Warning เฉยๆ
    for j in range(60,0,-1) :
      temp_total_spread[count-j] = temp_total_spread[count-j-1] + src['spread_vol'][count-j]
    src['total_spread_vol'] = temp_total_spread
  else:
    pass

  #Change Bar Check
  if temp_time == src['datetime'][count-1] :
    temp_total_spread[count-1] = temp_total_spread[count-2] + src['spread_vol'][count-1]  # ถ้าเป็นแท่งเดิม ให้บวกค่า all spread volume realtime
    src['total_spread_vol'] = temp_total_spread
  
  else :
    for j in range(0,count-1,1) :
      temp_total_spread[j] = temp_total_spread[j+1]
    temp_total_spread[count-2] = temp_total_spread[count-3] + src['spread_vol'][count-2]
    src['total_spread_vol'] = temp_total_spread
    #temp_time = src['datetime'][count-1]
  #print(src['total_spread_vol'])

  v = src['total_spread_vol'] + src['spread_vol']
  #print(v)

  ###########################################
# smooth
  import pandas_ta as ta
  smooth = ta.sma(close = v , length = 14)
  #print(smooth)  

  ###########################################
# v_spread
  v_spread_data = v-smooth
  import math
  import statistics as stat
  for i in range(10,0,-1):
    temp_data = v_spread_data[count-v_spread_lenght-i+1 : count-i+1]
    temp_data = stat.stdev(temp_data)
    temp_data = temp_data**2
    temp_data = temp_data*(v_spread_lenght-1)/v_spread_lenght
    temp_data = math.sqrt(temp_data)
    v_spread[10-i] = temp_data
  #print(v_spread)

  ###########################################
# price_spread
  price_spread_data = src['high'] - src['low']
  for i in range(10,0,-1):
    temp_data = price_spread_data[count-price_spread_lenght-i+1 : count-i+1]
    temp_data = stat.stdev(temp_data)
    temp_data = temp_data**2
    temp_data = temp_data*(price_spread_lenght-1)/price_spread_lenght
    temp_data = math.sqrt(temp_data)
    price_spread[10-i] = temp_data
  #print(price_spread)
  
  ###########################################
# shadow
  shadow_data = (v - smooth)/(v_spread * price_spread)
  for i in range(10,0,-1):
    temp_data = ( (v[count-i] - smooth[count-i]) * price_spread[10-i] ) / v_spread[10-i] 
    shadow[10-i] = temp_data
  #print(shadow)

  ###########################################
# Out
  for i in range(10,0,-1):
    if shadow[10-i] > 0 :
      out[10-i] = shadow[10-i] + src['high'][count-i]
    else:
      out[10-i] = shadow[10-i] + src['low'][count-i]
  #print(out)

  ###########################################
# vpt
  tf_multiplier = tf
  vpt_length = tf * 7 / tf_multiplier
  #vpt = ta.ema(close = out , length = vpt_length )

  if first_scan == 0:
    i = 10
    vpt[i-10] = offset_vpt       # แท่งที่ 10 จากหลังสุด
    for i in range(9,0,-1):
      ema_mult = 2 / (vpt_length+1)
      vpt[10-i] = (out[10-i] * ema_mult) + ((1 - ema_mult) * vpt[10-i-1])
  else:
    pass

  #Change Bar Check
  if temp_time == src['datetime'][count-1] :
    vpt[9] = (out[9] * ema_mult) + ((1 - ema_mult) * vpt[8])
  else :
    for i in range(0,9,1) :
      vpt[i] = vpt[i+1]
    vpt[8] = (out[8] * ema_mult) + ((1 - ema_mult) * vpt[7])    # เนื่องจากเวลาที่รันรอบก่อนหน้า กับข้อมูลจริง อาจไม่เท่ากัน จึงต้องแทนค่าใหม่อีกรอบ ควรทำกับทุกข้อมูล และทุกครั้งก่อนเลื่อนข้อมูล
    vpt[9] = (out[9] * ema_mult) + ((1 - ema_mult) * vpt[8])
  #print(vpt)

  ###########################################
# Up-Down lev
  temp_mult_lev = ta.atr(high = src['high'], low = src['low'], close = src['close'], length = Period_ST)
  for i in range(10,0,-1):
    mult_lev[10-i] = temp_mult_lev[count-i]
  #print(mult_lev)

  for i in range(10,0,-1):
    up_lev[10-i] = vpt[10-i] - (mult * mult_lev[10-i])
    down_lev[10-i] = vpt[10-i] + (mult * mult_lev[10-i])
  #print(up_lev)
  #print(down_lev)

  ###########################################
# Up-Down Trend
  if first_scan == 0 :
    for i in range(9,1,-1):
      if src['close'][count-i-1] > up_trend[10-i-1] :
        up_trend[10-i] = max(up_lev[10-i] , up_trend[10-i-1])
      else:
        up_trend[10-i] = up_lev[10-i]

      if src['close'][count-i-1] < down_trend[10-i-1] :
        down_trend[10-i] = min(down_lev[10-i] , down_trend[10-i-1])
      else:
        down_trend[10-i] = down_lev[10-i]
  else:
    pass

  #Change Bar Check
  if temp_time == src['datetime'][count-1] :
    if src['close'][count-2] > up_trend[8] :
      up_trend[9] = max(up_lev[9] , up_trend[8])
    else:
      up_trend[9] = up_lev[9]

    if src['close'][count-2] < down_trend[8] :
      down_trend[9] = min(down_lev[9] , down_trend[8])
    else:
      down_trend[9] = down_lev[9]

  else :
    for i in range(0,9,1):                                            # Shift_data
      up_trend[i] = up_trend[i+1]
      down_trend[i] = down_trend[i+1]

    if src['close'][count-2] > up_trend[8] :
      up_trend[9] = max(up_lev[9] , up_trend[8])
    else:
      up_trend[9] = up_lev[9]

    if src['close'][count-2] < down_trend[8] :
      down_trend[9] = min(down_lev[9] , down_trend[8])
    else:
      down_trend[9] = down_lev[9]

  #print(up_trend)
  #print(down_trend)
  
  ###########################################
# trend
  if first_scan == 0 :
    for i in range(8,1,-1):
      if src['close'][count-i] > down_trend[10-i-1] :
        trend[10-i] = 1
      elif src['close'][count-i] < up_trend[10-i-1] :
        trend[10-i] = -1
      else:
        #trend[10-i] = trend[10-i-1]
        if trend[10-i-1] == 0 :
          trend[10-i-1] = 1
          trend[10-i] = 1
        else:
          trend[10-i] = trend[10-i-1]
    trend[10-8-1] = offset_trend
  else:
    pass

  #Change Bar Check
  if temp_time == src['datetime'][count-1] :
    if src['close'][count-1] > down_trend[8] :
      trend[9] = 1
    elif src['close'][count-1] < up_trend[8] :
      trend[9] = -1
    else:
      trend[9] = trend[8]
  else :
    for i in range(0,9,1) :
      trend[i] = trend[i+1]                                 # shift data

    for i in range(2,0,-1) :
      if src['close'][count-i] > down_trend[10-i-1] :
        trend[10-i] = 1
      elif src['close'][count-i] < up_trend[10-i-1] :
        trend[10-i] = -1
      else:
        trend[10-i] = trend[10-i-1]
  #print(trend)

  ###########################################
# st_line
  for i in range(0,10,1) :
    if trend[i] == 1 :
      st_line[i] = up_trend[i]
    else :
      st_line[i] = down_trend[i]
  #print(st_line)

  ########################################### 
# find cross position
  cross = "None"
  close_A = src['close'][count-2]
  close_B = src['close'][count-1]

  st_line_A = st_line[10-2]
  st_line_B = st_line[10-1]

  if close_B > st_line_B and close_A < st_line_A :
    cross = "cross_over"
  elif close_B < st_line_B and close_A > st_line_A :
    cross = "cross_under"

# SuperTrend Output
  ST_signal = "None"
  ema_open = ta.ema(close = src['open'] , length = vpt_length )

  if cross == "cross_over" and src['close'][count-1] > ema_open[count-1] :
    ST_signal = "ST_Buy"

  elif cross == "cross_under" and src['close'][count-1] < ema_open[count-1] :
    ST_signal = "ST_Sell"

  else:
    pass

################################################################################
# ATR Trailing Stop
  ATR = src.ta.atr(high = src['high'], low = src['low'], close = src['close'], length=ATR_Period)     # ATR
  nLoss = ATR_Factor * ATR                                                                              # nLoss
  ATRTrailingStop = 0 * ATR                                                                             # สร้าง Array เปล่าของ ATRTrailingStop เตรียมไว้
  src_c = src['close']

  for j in range(ATR_Period+1,count,1):                                 # เริ่มข้อมูลที่ตำแหน่ง 15 เพราะใช้ข้อมูล 14 ตัวก่อนหน้า
    if src_c[j] > ATRTrailingStop[j-1] and src_c[j-1] > ATRTrailingStop[j-1] :
      ATRTrailingStop[j] = max( ATRTrailingStop[j-1], src_c[j] - nLoss[j] )
    elif src_c[j] < ATRTrailingStop[j-1] and src_c[j-1] < ATRTrailingStop[j-1]:
      ATRTrailingStop[j] = min( ATRTrailingStop[j-1], src_c[j] + nLoss[j] )
    elif src_c[j] > ATRTrailingStop[j-1] :
      ATRTrailingStop[j] = src_c[j] - nLoss[j]
    else :
      ATRTrailingStop[j] = src_c[j] + nLoss[j]

  # ATR แบ่งโซน เขียว-แดง
  ATR = "None"
  if ATRTrailingStop[count-2] < src['close'][count-2] :
    ATR = "Green"
  else :
    ATR = "Red"

##############################################################################
### Buy-Sell Signal ###
# Buy-Sell signal
  signal = "None"
  if ST_signal == "ST_Buy" and ATR == "Green" and Out_Stock == 1 :
    signal = "Buy_Signal"

  elif ( ST_signal == "ST_Sell" or ATR == "Red" ) and In_Stock == 1 :
    signal = "Sell_Signal"

  else:
    pass
  
################################################################################

  print("Time         = ",src['datetime'][count-1])
  print("Pair         = ",Pair)
  print("Timeframe    = ",timeframe)

  print("\n""######### All Status #########")
  print("ST_Signal    = ",ST_signal)
  print("ATR     = ",ATR)
  print("Status_Order = ",Status_Order)
  print("Signal       = ",signal)

  print("\n""######## Trade Status ########")
  if signal == "Buy_Signal" :
    print("Action       = BUY-Trade")
    Buy_Value = src['close'][count-1]
    Temp_PNL = Total_PNL
    print("Temp_PNL     = ",Temp_PNL*100-100," %")
    #create_order_buy
    In_Stock = 1
    Out_Stock = 0
    Status_Order = "In_Stock"

  elif signal == "Sell_Signal" :
    print("Action       = SELL-Trade")
    Sell_Value = src['close'][count-1]
    Total_PNL = Total_PNL * Sell_Value / Buy_Value
    print("Total_PNL    = ",Total_PNL*100-100," %")
    #create_order_sell
    In_Stock = 0
    Out_Stock = 1
    Status_Order = "Out_Stock"

  else :
    print("Action       = Non-Trade")
    if Status_Order == "Out_Stock" :
      print("Total_PNL    = ",Total_PNL*100-100," %")
    elif Status_Order == "In_Stock" :
      Temp_PNL = src['close'][count-1] / Buy_Value
      print("Temp_PNL     = ",Temp_PNL*100-100," %")

################################################################################
  first_scan = 1
  temp_time = src['datetime'][count-1]

  #Round += 1
  import time
  #sleep = 60 
  print("\n""Sleep",sleep,"sec.")
  print("------------------------------------------------------")
  time.sleep(sleep) # Delay for 1 minute (60 seconds).