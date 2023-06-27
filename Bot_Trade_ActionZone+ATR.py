# CDC Action Zone + ATR Trailing Stop

#Login
import ccxt
apiKey    = ""
secret    = "" 
exchange = ccxt.binance  ({'apiKey' : apiKey ,'secret' : secret ,'enableRateLimit': True})

# Setting
EMA_F_set    = 12
EMA_S_set    = 26

Pair          = "BTC/USDT"        # คู่เทรด
timeframe     = "1m"              # ช่วงเวลาของกราฟที่จะดึงข้อมูล
limit         = 100               # จำนวนข้อมูลย้อนหลัง
Unit_trade    = 0.0001            # ปริมาณการเทรด

################################################################################
#Offset Value
Round = 1
Total_PNL = 1
i = 0
Buy_Value = 1.0
Sell_Value = 1.0

ATR_Period = 14
ATR_Factor = 2

In_Stock = 0
Out_Stock = 1
Status_Order = "Out_Stock"

while True:
  # เรียก ข้อมูลราคา ของสินค้ามาไว้ในรูปแบบ ตาราง 
  import pandas as pd

  # เรียกข้อมูลจาก exchange
  df_ohlcv  = exchange.fetch_ohlcv(Pair ,timeframe=timeframe,limit=limit)                               				# ข้อมูลดิบ
  df_ohlcv  = pd.DataFrame(df_ohlcv, columns =['datetime', 'open','high','low','close','volume'])       				# จัด + มีหัวข้อ
  df_ohlcv['datetime']  = pd.to_datetime(df_ohlcv['datetime'], unit='ms')                               				# แปลงเวลา

  ##############################################################################
  # ATR Trailing Stop
  import pandas_ta as ta  
  src = df_ohlcv                                                                                        				# Original Data เผื่อเรียกใช้
  count = len(src)                                                                                      				# ขนาด Array ส่วนนี้เขียนทีหลัง เป็นการเขียนทับซ้อนกับส่วน Action Zone => ว่างๆก็ไล่เขียนใหม่

  ATR = df_ohlcv.ta.atr(high = df_ohlcv['high'], low = df_ohlcv['low'], close = df_ohlcv['close'], length=ATR_Period)   # ATR
  nLoss = ATR_Factor * ATR                                                                              				# nLoss
  ATRTrailingStop = 0 * ATR                                                                             				# สร้าง Array เปล่าของ ATRTrailingStop เตรียมไว้
  src_c = src['close']

  j=ATR_Period+1                                                                                        				# เริ่มข้อมูลที่ตำแหน่ง 15 เพราะใช้ข้อมูล 14 ตัวก่อนหน้า
  while j < count :
    if src_c[j] > ATRTrailingStop[j-1] and src_c[j-1] > ATRTrailingStop[j-1] :
      ATRTrailingStop[j] = max( ATRTrailingStop[j-1], src_c[j] - nLoss[j] )

    elif src_c[j] < ATRTrailingStop[j-1] and src_c[j-1] < ATRTrailingStop[j-1] :
      ATRTrailingStop[j] = min( ATRTrailingStop[j-1], src_c[j] + nLoss[j] )

    elif src_c[j] > ATRTrailingStop[j-1] :
      ATRTrailingStop[j] = src_c[j] - nLoss[j]

    else :
      ATRTrailingStop[j] = src_c[j] + nLoss[j]

    j+=1

  src = pd.concat([ src , ATR , nLoss , ATRTrailingStop ], axis=1)                                      # รวมข้อมูล
  src.columns = ['datetime', 'open','high','low','close','volume','ATR','nLoss','ATRTrailingStop']      # เปลี่ยนชื่อ column

  # ATR แบ่งโซน เขียว-แดง
  ATR = "None"
  if src['ATRTrailingStop'][count-2] < src['close'][count-2] :
    ATR = "Green"
  else :
    ATR = "Red"

  ##############################################################################
  # CDC Action Zone
  src_ohlcv = ( df_ohlcv['open'] + df_ohlcv['high'] + df_ohlcv['low'] + df_ohlcv['close'] ) / 4
  df_ohlcv['close'] = src_ohlcv                                                                         # นำ src ไปแทน close ใน df_ohlcv เพื่อเตรียมทำ AP
  src_ohlcv = df_ohlcv                                                                                  # เปลี่ยนชื่อให้จำง่าย เผื่อเรียกใช้

  AP = df_ohlcv.ta.ema(2)
  df_ohlcv['close'] = AP                                                                                # นำ AP ไปแทน close ใน df_ohlcv เพื่อเตรียมทำ EMA
  AP = df_ohlcv                                                                                         # เปลี่ยนชื่อให้จำง่าย เผื่อเรียกใช้

  EMA_F     = AP.ta.ema(EMA_F_set)                                                                      # EMA Fast All
  EMA_S     = AP.ta.ema(EMA_S_set)                                                                      # EMA Slow All
  AP = pd.concat([df_ohlcv,EMA_F,EMA_S], axis=1)                                                        # รวมข้อมูล

  #EMA Cross
  count = len(AP)                                                                                       # ขนาดข้อมูล
  EMA_F_A = AP['EMA_12'][count-2]                                                                 		# ใช้ข้อมูล Fast ก่อนล่าสุด 1 ตำแหน่ง
  #EMA_F_B = AP['EMA_12'][count-3]                                                                 		# ใช้ข้อมูล Fast ก่อนล่าสุด 2 ตำแหน่ง
  EMA_F_B = AP['EMA_12'][count-4]

  EMA_S_A = AP['EMA_26'][count-2]                                                                 		# ใช้ข้อมูล Slow ก่อนล่าสุด 1 ตำแหน่ง
  #EMA_S_B = AP['EMA_26'][count-3]                                                                 		# ใช้ข้อมูล Slow ก่อนล่าสุด 2 ตำแหน่ง
  EMA_S_B = AP['EMA_26'][count-4]

  print("Round		= ",Round)
  print("Time 		= ",AP['datetime'][count-1])
  print("Pair      	= ",Pair)
  print("Timeframe 	= ",timeframe)

  # Signal and Trend
  Signal = "none"
  Trend = "none"

  if EMA_F_A > EMA_S_A :
    Trend = "Up_trend"                                    				# Fast อยู่บน Slow
  elif EMA_F_A < EMA_S_A :
    Trend = "Down_trend"                                  				# Fast อยู่ล่าง Slow
    

  # 4 Zone
  if Trend == "Up_trend"  and AP['close'][count-2] > EMA_F_A:          	# Green
    Zone = "Green"
  elif Trend == "Up_trend"  and AP['close'][count-2] < EMA_F_A:       	# Yellow
    Zone = "Yellow"
  elif Trend == "Down_trend" and AP['close'][count-2] > EMA_S_A:       	# Blue 
    Zone = "Blue"
  elif Trend == "Down_trend" and AP['close'][count-2] < EMA_S_A:       	# Red 
    Zone = "Red"

################################################################################
  # Buy - Sell Signal
  if Zone == "Green" and ATR == "Green" and Out_Stock == 1 :          	# Bullish + ATR(Green)
    Signal = "Buy_Signal"

  elif ATR == "Red" and In_Stock == 1 :       # ATR(Red)
    Signal = "Sell_Signal"

#  if Zone == "Green"  and EMA_F_B < EMA_S_B:          					# Bullish
#    Signal = "Buy_Signal"

#  elif Zone == "Yellow" and EMA_F_B > EMA_S_B:       					# Bearlish 
#    Signal = "Sell_Signal"

  # System_Check_All_Status

  print("\n","####### Up-Down Trend Check #####")
  print("EMA_F_A   = ",EMA_F_A)
  print("EMA_S_A   = ",EMA_S_A)

  print("\n","####### Color Zone Check #####")
  print("Previous Close   = ",AP['close'][count-2])
  print("Fast             = ",EMA_F_A)
  print("Slow             = ",EMA_S_A)

  print("\n","####### ATR Color Check #####")
  print("Previous_C_Price = ",src['close'][count-2])
  print("ATRTrailingStop  = ",ATRTrailingStop[count-2])

#  print("\n""Buy-Sell Signal Check")
#  print("EMA_S_B   = ",EMA_S_B)
#  print("EMA_F_B   = ",EMA_F_B)

  print("\n####### Signal and Trend #####")
  print("Trend        = ",Trend)
  print("Zone         = ",Zone)
  print("ATR          = ",ATR)
  print("Status_Order = ",Status_Order)
  print("Signal       = ",Signal)

  # Trade_Status
  print("\n""####### Trade Status #####")
  if Signal  == "Buy_Signal" :
    print("BUY-Trade")
    Buy_Value = AP['close'][count-1]
    Temp_PNL = Total_PNL
    print("Temp_PNL = ",Temp_PNL*100-100," %")
    #### @ exchange.create_order( Pair ,'market','buy',Unit_trade )
    In_Stock = 1
    Out_Stock = 0
    Status_Order = "In_Stock"
    i+=1
    
  elif Signal  == "Sell_Signal" : 
    if i == 0 :
      print("No-Action")
    else:
      print("SELL-Trade")
      Sell_Value = AP['close'][count-1]
      Total_PNL = Total_PNL * Sell_Value / Buy_Value
      print("Total_PNL = ",Total_PNL*100-100," %")
      ########@#$$$#  exchange.create_order( Pair ,'market','sell',Unit_trade )
      In_Stock = 0
      Out_Stock = 1
      Status_Order = "Out_Stock"
      i=0

  else :
    print("Non-Trade")
    if i == 0:
      print("Total_PNL = ",Total_PNL*100-100," %")
    else:
      Temp_PNL = df_ohlcv['close'][count-1] / Buy_Value
      print("Temp_PNL = ",Temp_PNL*100-100," %")
    

  Round += 1
  import time
  sleep = 30 
  print("\n""Sleep",sleep,"sec.")
  print("------------------------------------------------------")
  time.sleep(sleep) # Delay for 1 minute (60 seconds).  