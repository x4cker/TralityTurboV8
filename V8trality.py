#!/bin/bash/python3
# // By Eddie Z. V8 + Cooldown Update And Cancel Pending Orders.
# // Built to use with Trality 1 Minute Interval.
# // Created to backtest the original Standalone Script. (Private Only)
# // Cooldown's are set to 1 in order to backtest. to run live with cooldowns, limits most be changed from 1 to 120 for two minute symbol cooldown.

import time

SYMBOLS = ["VETUSDT", "BNBUSDT",  "DOTUSDT", "NEOUSDT"]
SYMBOLS2 = ["DASHUSDT","LTCUSDT"]

SIGNAL_BUY = 1
SIGNAL_SELL = 2
SIGNAL_IGNORE = 3
cross = 0

cooler = {'LTCUSDT' : 0, 'ADAUSDT' : 0 , 'DASHUSDT' : 0, 'LINKUSDT' : 0, 'FIOUSDT' : 0, 'VETUSDT' : 0 , 'BNBUSDT' : 0, 'ETHUSDT' : 0, 'DOTUSDT' : 0, 'NEOUSDT' : 0}

buyer = {'LTCUSDT' : 0, 'ADAUSDT' : 0 , 'DASHUSDT' : 0, 'LINKUSDT' : 0, 'FIOUSDT' : 0, 'VETUSDT' : 0 , 'BNBUSDT' : 0, 'ETHUSDT' : 0, 'DOTUSDT' : 0, 'NEOUSDT' : 0}

tp_newposition =  {'LTCUSDT' : False, 'ADAUSDT' : False, 'DASHUSDT' : False, 'LINKUSDT' : False, 'FIOUSDT' : False, 'VETUSDT' : False , 'BNBUSDT' : False, 'ETHUSDT' : False, 'DOTUSDT' : False, 'NEOUSDT' : False}
tp_position =  {'LTCUSDT' : 0, 'ADAUSDT' : 0 , 'DASHUSDT' : 0, 'LINKUSDT' : 0, 'FIOUSDT' : 0, 'VETUSDT' : 0 , 'BNBUSDT' : 0, 'ETHUSDT' : 0, 'DOTUSDT' : 0, 'NEOUSDT' : 0}

def initialize(state):
   state.signals = {}
   state.signal_parameters = [22, 30, 100, 14, 9]



def compute_signal(data, short_n, medium_n, long_n, rsi_n, adx_n):
    macd_ind = data.macd(12,26,9)
    if macd_ind is None:
        return
    macdsignal = macd_ind['macd_signal'].as_np()[0,:]
    macd = macd_ind['macd'].as_np()[0,:]
    rsibuy = False
    adxbuy = False
    cross = 0
    macdcross = 0
    orderID = 0
    rsi = data.rsi(14).as_np()[0,:]
    adx = data.adx(adx_n).as_np()[0,:]
    roc = data.roc(4).last
    #stoch = data.stoch(14).as_np()[0,:]
    if  rsi[-1] < rsi[0] < 38:
        rsibuy = True

    if adx[-2] < adx[-1] < 25:
        adxbuy = True

    has_position = has_open_position(data.symbol, include_dust=False)
    portvalue = float(query_portfolio_value())
    portfolio = query_portfolio()
    liquidity = portfolio.excess_liquidity_quoted
    position = query_open_position_by_symbol(data.symbol,include_dust=False)
    worst = portfolio.worst_trade_return * 100
    best = portfolio.best_trade_return * 100
    now = time.time()

############################################################## DEBUG ##################################################################

    if position is not None:
        print(f"● {position.symbol} : Entry Price: {position.entry_price} - Price Now : {data.close_last} - Portofolio : {portvalue} - ADX : {adx[0]} - RSI : {rsi[0]}")

        
########################################################### BUY RULES ##################################################################

    # // Check Liquidity For Buy Rules
    if liquidity > portvalue * 0.98 and position is None:
        # // Buy Rule for ETH
        if cooler[data.symbol] != 0 and now - cooler[data.symbol] >= 1 and now - cooler[data.symbol] < 10000 or cooler[data.symbol] == 0:
            if buyer[data.symbol] != 0 and now - buyer[data.symbol] >= 1 or buyer[data.symbol] == 0: #// Checking if cooldown time passed.
                if not has_position and rsibuy and (42 > adx[0] > 25 or adxbuy):
                    buy_value = float(portvalue) * 0.98 / data.close_last
                    order_market_target(symbol=data.symbol,target_percent=0.98)      
                    order_stop_loss(symbol=data.symbol, amount=buy_value, stop_percent=0.025,subtract_fees=False)
                    print(f"● Buy Rule 1 for {data.symbol} , Value: {buy_value} at Current market price: {data.close_last}")
                    print(f"● Wallet Value: {portvalue}")
                    print(f"● Buy Values - ADX: {adx[0]} // RSI: {rsi[0]} // // TIME DIFF : {now - cooler[data.symbol]}")
                    buytime = time.time()
                    buyer[data.symbol] = buytime

        else:
    # // Buy Cooldown
            pass


######################################################### SELL RULES ###################################################################

    if position is not None:
        diff = 100 - ((float(position.entry_price) / float(data.close_last)) * 100)
        if diff >= 0.01 or diff <= -0.01:

            if rsi[0] > 74 and adxbuy == False and diff > 0.55:
                close_position(data.symbol)
                print(f"!!!!!!! SELL SIGNAL {data.symbol}  Price: {data.close_last} - Diff: {diff} !!!!!!!!!")

            if not tp_newposition[data.symbol]:
                if data.close_last >= float(position.entry_price) + (float(position.entry_price) * 0.009):
                    print(f"Position Initiated for {data.symbol} Price: {data.close_last} - Diff: {diff}")
                    tp_newposition[data.symbol] = True
                    tp_position[data.symbol] = data.close_last
                    
                    
            # // DYNAMIC TP - Stage 2 Every 0.08% And Dynamic STOP LOSS Section.
            elif tp_newposition[data.symbol]:
                if data.close_last >= float(tp_position[data.symbol]) + (float(position.entry_price) * 0.006):
                    print(f"Position Upgrade for {data.symbol} Price: {data.close_last} - Diff: {diff}")
                    tp_position[data.symbol] = data.close_last

             # // DYNAMIC SL - Stop Loss for Position Change -0.014%
                elif data.close_last <= float(tp_position[data.symbol]) - (float(position.entry_price) * 0.003):
                    print(f"!!!!!!! STOP LOSS AFTER POSITION CHANGE Initiated for {data.symbol}  Price: {data.close_last} - Diff: {diff} !!!!!!!!!")
                    close_position(data.symbol)
                    tp_newposition[data.symbol] = False
                    tp_position[data.symbol] = 0
                    selltime = time.time()
                    cooler[data.symbol] = selltime





################################################ Cancel Pending Orders Over 300 Seconds #######################################

        try:
            if position is None:
                for order1 in query_open_orders():
                    if data.symbol in order1.symbol:
                        cancel_order(order1.id)
                        print(f"{order1.id} Canceled for {data.symbol}")
        except RuntimeError:
           print(f"Failed to Cancel {order1.id} for {data.symbol}")

############################################# SAVE EMA SIGNAL IN STATE ######################################################

def resolve_ema_signal(state, data):
    if data is None:
        return
    state.signals[data.symbol] = compute_signal(data, *state.signal_parameters)

################################################# INTERVALS 1TIK ############################################################

@schedule(interval= "1m", symbol=SYMBOLS, window_size=150)
def handler(state, dataMap):
    for symbol, data in dataMap.items():
        resolve_ema_signal(state, data)

@schedule(interval= "1m", symbol=SYMBOLS2, window_size=150)
def handler2(state, dataMap):
    for symbol, data in dataMap.items():
        resolve_ema_signal(state, data)

############################################################################################################################
