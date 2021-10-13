import config, csv, datetime, numpy, os, sys, talib, asyncio
from binance.client import Client
from binance.enums import *
from binance import ThreadedWebsocketManager
from pprint import pprint
from time import sleep
from datetime import date, timedelta

api_key = config.API_KEY           # Set key and secret in the config.py file.
api_secret = config.API_SECRET
twm = ThreadedWebsocketManager(api_key=api_key, api_secret=api_secret)

user = Client(api_key, api_secret) # Client for user endpoints.
public = Client()                  # Client for public endpoints.
fee = 0.00075                      # 0.075% in decimal. Set trading fee here, differs between different VIP levels.
profit =  1.5

test_mode = 0                      # Place test orders instead of a real ones. 0 = off | 1 = Buy | 2 = Sell
test_signal = 0

PAIRS = {                          # Define pairs to trade here:
    'GALAUSDT': {                  # PAIRS.keys()
        'symbol': 'GALA',          # Make sure symbol and base are set to the same as the PAIRS.keys().
        'base': 'USDT',            # Make sure symbol and base are set to the same as the PAIRS.keys().
        'kline': '@kline_3m',     # Set kline interval here.
        'price': '@bookTicker',    # Set price ticker here.
        'profit': fee,             # Set profit margin here, this will be the minimum it sells for.
        'decPrice': 5,             # Count how many decimals the price has and set here.
        'decOrder': 0,             # Same as decPrice, but for the order.
        'smaLow': 5,               # Set the sma low here, default 5.
        'smaHigh': 10,             # Set the sma low here, default 10.
        'last_sma_low': 0,
        'last_sma_high': 0,
        'bid': 0,
        'ask': 0,
        'baseBal': 0,
        'assetBal': 0,
        'minNotional': 0,
        'order': 0,
        'qty': 0,
        'awaitOrder': False,
        'lastPrice': 0,
        'load_last': 0,
        'checkLogOnce': 0,
        'dividend': 0,
        'hodl': 0,
        'closes': []
    },
    'CELRUSDT':    {
        'symbol': 'CELR',
        'base': 'USDT',
        'kline': '@kline_1h',
        'price': '@bookTicker',
        'profit': fee, # Set profit margin here.
        'decPrice': 5,
        'decOrder': 1,
        'smaLow': 5,
        'smaHigh': 10,
        'last_sma_low': 0,
        'last_sma_high': 0,
        'bid': 0,
        'ask': 0,
        'baseBal': 0,
        'assetBal': 0,
        'minNotional': 0,
        'order': 0,
        'qty': 0,
        'awaitOrder': False,
        'lastPrice': 0,
        'load_last': 0,
        'checkLogOnce': 0,
        'dividend': 0,
        'hodl': 0,
        'closes': []
    },
    'DYDXUSDT':    {
        'symbol': 'DYDX',
        'base': 'USDT',
        'kline': '@kline_5m',
        'price': '@bookTicker',
        'profit': fee, # Set profit margin here.
        'decPrice': 3,
        'decOrder': 2,
        'smaLow': 5,
        'smaHigh': 10,
        'last_sma_low': 0,
        'last_sma_high': 0,
        'bid': 0,
        'ask': 0,
        'baseBal': 0,
        'assetBal': 0,
        'minNotional': 0,
        'order': 0,
        'qty': 0,
        'awaitOrder': False,
        'lastPrice': 0,
        'load_last': 0,
        'checkLogOnce': 0,
        'dividend': 0,
        'hodl': 0,
        'closes': []
    },
    'SHIBUSDT':    {
        'symbol': 'SHIB',
        'base': 'USDT',
        'kline': '@kline_3m',
        'price': '@bookTicker',
        'profit': fee, # Set profit margin here.
        'decPrice': 8,
        'decOrder': 0,
        'smaLow': 5,
        'smaHigh': 10,
        'last_sma_low': 0,
        'last_sma_high': 0,
        'bid': 0,
        'ask': 0,
        'baseBal': 0,
        'assetBal': 0,
        'minNotional': 0,
        'order': 0,
        'qty': 0,
        'awaitOrder': False,
        'lastPrice': 0,
        'load_last': 0,
        'checkLogOnce': 0,
        'dividend': 0,
        'hodl': 0,
        'closes': []
    }
}

dec = 0
def truncate(num: float, n: int = dec) -> float: # Limits decimal points, to fit binance filters
    return int(num*10**n)/10**n

def currtime():
    time = datetime.datetime.now().strftime('%Y-%d-%m %H:%M:%S')
    print(f'\n{time}')
    return time

def history():
    number_of_days = 10 # Set how many days back you want to grab history for.
    current_date = date.today().isoformat()   
    days_before = (date.today()-timedelta(days=number_of_days)).isoformat()
    print('\n[+] Fetching history.')
    for i in PAIRS.keys():
        # candlesticks = public.get_historical_klines(i, PAIRS[i]['kline'][-2:], "Yesterday", "Today") # Fetch candles from yesterday - today, as default. Change to whatever range you need.
        candlesticks = public.get_historical_klines(i, PAIRS[i]['kline'][-2:], days_before, current_date) # Fetch candles from 10 days back - today, as default. Change to whatever range you need.
        for closes in candlesticks:
            PAIRS[i]['closes'].append(float(closes[4]))

def min_notional():
    print('[-] Fetching min notionals.')
    for i in PAIRS.keys():
        try:
            info = public.get_symbol_info(i)
            PAIRS[i]['minNotional'] = float(info['filters'][3]['minNotional'])
        except Exception as e:
            print(e)
    for i in PAIRS.keys():
        print('   ',i, PAIRS[i]['minNotional'], 'Trading:', PAIRS[i]['kline'])

def open_orders(): # Check what's currently in order.
    global div, base
    base = {}
    countBase = []
    in_order = []
    for i in PAIRS.keys():
        countBase.append(PAIRS[i]['base'])
        for i in countBase:
            count = countBase.count(i)
            base[i] = count
    for i in PAIRS.keys():
        PAIRS[i]['dividend'] = base[PAIRS[i]['base']]
    try:
        orders = user.get_open_orders()
        for i in PAIRS.keys():
            countBase.append(PAIRS[i]['base'])
            if orders:
                for index in range(len(orders)):
                    if i == orders[index]['symbol']:
                        in_order.append(orders[index]['symbol'])
                        PAIRS[i]['order'] = orders[index]
                        # pprint(PAIRS[i]['order']['side'])
                        if orders[index]['side'] == 'BUY':
                            if PAIRS[orders[index]['symbol']]['base'] in base:
                                base[PAIRS[orders[index]['symbol']]['base']] -= 1
                                for i in PAIRS.keys():
                                    if PAIRS[orders[index]['symbol']]['base'] in PAIRS[i]['base']:
                                        PAIRS[i]['dividend'] = base[PAIRS[orders[index]['symbol']]['base']]
        print(f'[-] Fetching open orders: \n    {in_order}\n    Base dividend:', base)
    except Exception as e:
        print(e)
        return False

def account_balance(): # Get all balances at once instead of one query per symbol, saves API payload.
    print('[-] Fetching account balance.')
    global div, base_div
    in_asset = []
    try:
        get_bal = user.get_account()
        balance = get_bal['balances']
        if balance:
            base_once = 0
            for i in PAIRS.keys():
                for asset in balance:
                    if asset['asset'] == PAIRS[i]['symbol']:
                        PAIRS[i]['assetBal'] = float(asset['free'])
                        if float(asset['free']) > 0.001:
                            PAIRS[i]['hodl'] = 1
                            in_asset.append(i)
                            print('   ',PAIRS[i]['symbol'], asset['free'])
                            base_div = PAIRS[i]['base']
                        else:
                            in_asset = []
                            base_div = PAIRS[i]['base']
                            
                    if asset['asset'] == PAIRS[i]['base']:
                        PAIRS[i]['baseBal'] = float(asset['free'])
                        if base_once == 0:
                            base_once = 1
                            print('   ',PAIRS[i]['base'], asset['free'])

        for i in PAIRS.keys():
            if PAIRS[i]['hodl'] == 1:
                base_once = 0
                for b in PAIRS.keys():
                    if PAIRS[i]['base'] == PAIRS[b]['base']:
                        if PAIRS[i]['dividend'] < 2:
                            PAIRS[b]['dividend'] = 1
                        else:
                            PAIRS[b]['dividend'] -= 1
        print('\n   ',PAIRS[i]['base'], 'Dividend:', PAIRS[i]['dividend'])
    except Exception as e:
        print(e)
        return False

def save_csv(side, symbol, price, qty):
        try:
            with open(f'{side}-{symbol}.csv', 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([side, symbol, price, qty])
                print(f'Saving {side, symbol, price, qty} to CSV.')
            return True
        except Exception as e:
            print(e)
        return False

def load_csv(side, pair):
    try:
        with open(f"{side}-{pair}.csv") as f:
            csv_reader = csv.reader(f)
            for line in csv_reader:
                # last_side = line[0]
                last_qty = float(line[3])
                last_price = float(line[2])
            return last_price, last_qty
    except FileNotFoundError:
        return 0

def await_order_delay(symbol):
    sleep(5)
    PAIRS[symbol]['order'] = 0
    PAIRS[symbol]['awaitOrder'] = False

def order(side, symbol, price, qty):
    dec = PAIRS[symbol]['decPrice']
    # Binance API won't accept scientific notation.
    # If price has been formatted to scientific notation, format back to decimal. Ex. 8.04e-06 to 0.00000804.
    # * Python formats numbers with more than 5 decimals to scientific notation.
    if float(price) < float(1):
        price = f"{price:.{dec}f}"
    
    # print('Placing order:', side, symbol, price, qty)

    try:
        if test_mode == 1:
            print('\nTEST MODE ACTIVE, NO ORDERS WILL BE EXECUTED! Disable by setting test_mode = 0')
            print('Test order for:', side, symbol, price, qty)
            order = user.create_test_order( # Test order
                symbol=symbol,
                side=side,
                type=ORDER_TYPE_LIMIT,
                timeInForce=TIME_IN_FORCE_GTC,
                quantity=qty,
                price=price)
            print(order)
            print('Test order successful!')
        elif test_mode == 2:
            print('\nTEST MODE ACTIVE, NO ORDERS WILL BE EXECUTED! Disable by setting test_mode = 0')
            print('Test order for:', side, symbol, price, qty)
            order = user.create_test_order( # Test order
                symbol=symbol,
                side=side,
                type=ORDER_TYPE_LIMIT,
                timeInForce=TIME_IN_FORCE_GTC,
                quantity=qty,
                price=price)
            print(order)
            print('Test order successful!')
        else:
            user.create_order( # Real order
                symbol=symbol,
                side=side,
                type=ORDER_TYPE_LIMIT,
                timeInForce=TIME_IN_FORCE_GTC,
                quantity=qty,
                price=price)
    except Exception as e:
        print(e)
        # os.execv(sys.executable, [sys.executable] + sys.argv) # Restarts script completely, on error.
    return False

def userData(msg):
    try:
        if msg['e'] == 'executionReport':
            side = msg['S']
            symbol = msg['s']
            price = float(msg['p'])
            quantity = float(msg['q'])

            if PAIRS[symbol]['decOrder'] == 0:
                qty = int(quantity)
            else:
                qty = truncate(quantity, PAIRS[symbol]['decOrder'])

            if msg['X'] == 'NEW':
                currtime()
                print(f'New {side} order of {qty} {symbol} placed at: {price}')
                PAIRS[symbol]['order'] = msg

            if msg['X'] == 'FILLED':
                if side == 'BUY':
                    PAIRS[symbol]['hodl'] = 1
                    PAIRS[symbol]['order'] = 0
                    PAIRS[symbol]['awaitOrder'] = False
                    PAIRS[symbol]['assetBal'] = float(qty)
                    currtime()
                    print(f'Buy order with {qty} {symbol} filled at: {price}')
                    save_csv(side, symbol, price, qty)
                elif side == 'SELL':
                    PAIRS[symbol]['hodl'] = 0
                    PAIRS[symbol]['order'] = 0
                    PAIRS[symbol]['awaitOrder'] = False
                    # PAIRS[symbol]['assetBal'] = float(qty)
                    sold_base_qty = float(msg['Z'])
                    load_last = load_csv('BUY', symbol)

                    for i in PAIRS.keys():
                        if PAIRS[symbol]['base'] == PAIRS[i]['base']:
                            PAIRS[i]['baseBal'] = PAIRS[i]['baseBal'] + sold_base_qty
                    base_balance = PAIRS[symbol]['baseBal']
                    if load_last == 0:
                        currtime()
                        print(f'Sell order for {qty} {symbol} filled at: {price}. Base balance: {base_balance}')
                        save_csv(side, symbol, price, qty)
                    else:
                        gain = '{:.2f}'.format((price - load_last[0]) / price * 100)
                        currtime()
                        print(f'Sell order for {qty} {symbol} filled at: {price}, bought at: {load_last[0]}. Base balance: {base_balance}')
                        print(f'Gain: {gain}%')
                        save_csv(side, symbol, price, qty)
                elif side == 'CANCELED':
                    PAIRS[symbol]['awaitOrder'] = False
                    print(f'{symbol} {side} order cancelled.')

    except Exception:
        currtime()
        print('\nUser stream lost connection, reconnecting...')
        twm.stop_socket(userData)
        sleep(3)
        twm.start_user_socket(callback=userData)
        currtime()
        print('\nUser stream connected.')

        if msg['X'] == 'CANCELED':
            if side == 'BUY':
                base_qty = float(msg['q']) * float(msg['p'])
                for i in PAIRS.keys():
                    if PAIRS[symbol]['base'] == PAIRS[i]['base']:
                        PAIRS[i]['baseBal'] = PAIRS[i]['baseBal'] + base_qty
                        PAIRS[i]['dividend'] += 1
            else:
                for i in PAIRS.keys():
                    if PAIRS[symbol]['base'] == PAIRS[i]['base']:
                        PAIRS[i]['dividend'] -= 1

            PAIRS[symbol]['order'] = 0
            currtime()
            print(f'{side} order cancelled manually for: {symbol}')

def candles(msg):
    global test_signal
    # pprint(msg)
    try:
        symbol = msg['data']['s']
        candle = msg['data']['k']
        close = float(candle['c'])
        is_candle_closed = candle['x']

        if is_candle_closed:
            PAIRS[symbol]['closes'].append(truncate(float(close) , PAIRS[symbol]['decPrice']))

        if len(PAIRS[symbol]['closes']) >= PAIRS[symbol]['smaHigh']:
                np_closes = numpy.array(PAIRS[symbol]['closes'])
                sma_low = talib.SMA(np_closes, timeperiod=PAIRS[symbol]['smaLow'])
                sma_high = talib.SMA(np_closes, timeperiod=PAIRS[symbol]['smaHigh'])

                if test_mode == 1: # Test value, buy signal
                    last_sma_low = 60
                    last_sma_high = 50
                    PAIRS[symbol]['last_sma_low'] = last_sma_low
                    PAIRS[symbol]['last_sma_high'] = last_sma_high
                    if test_signal == 0:
                        print('test buy mode', PAIRS[symbol]['last_sma_low'], PAIRS[symbol]['last_sma_high'])
                        test_signal = 1
                elif test_mode == 2: # Test value, sell signal
                    last_sma_low = 50
                    last_sma_high = 60
                    PAIRS[symbol]['last_sma_low'] = last_sma_low
                    PAIRS[symbol]['last_sma_high'] = last_sma_high
                    if test_signal == 0:
                        print('test sell mode', PAIRS[symbol]['last_sma_low'], PAIRS[symbol]['last_sma_high'])
                        test_signal = 1
                else:
                    last_sma_low = truncate(sma_low[-1], PAIRS[symbol]['decPrice'])
                    last_sma_high = truncate(sma_high[-1],  PAIRS[symbol]['decPrice'])
                    PAIRS[symbol]['last_sma_low'] = last_sma_low
                    PAIRS[symbol]['last_sma_high'] = last_sma_high
                    # print(PAIRS[symbol]['last_sma_low'], PAIRS[symbol]['last_sma_high'])
    except Exception:
        currtime()
        print('\nCandle stream lost connection, reconnecting...')
        twm.stop_socket(candles)
        sleep(3)
        twm.start_multiplex_socket(callback=candles, streams=kline_streams)
        currtime()
        print('\nCandle stream connected.')

def prices(msg):
    try:
        symbol = msg['data']['s']
        PAIRS[symbol]['bid'] = truncate(float(str(msg['data']['b'])), PAIRS[symbol]['decPrice'])
        PAIRS[symbol]['ask'] = truncate(float(str(msg['data']['a'])), PAIRS[symbol]['decPrice'])
        trade(symbol)
    except Exception:
        currtime()
        print('\nPrice stream lost connection, reconnecting...')
        twm.stop_socket(prices)
        sleep(3)
        twm.start_multiplex_socket(callback=prices, streams=price_streams)
        currtime()
        print('\nPrice stream connected.')

def trade(symbol):
    try:
        if PAIRS[symbol]['bid'] and PAIRS[symbol]['ask']: # Make sure we have prices.

            assetBal = float(PAIRS[symbol]['assetBal'])
            bid = PAIRS[symbol]['bid']
            ask = PAIRS[symbol]['ask']

            if PAIRS[symbol]['order'] == 0:
                if PAIRS[symbol]['awaitOrder'] == False:
                    if PAIRS[symbol]['hodl'] == 1:
                        if PAIRS[symbol]['last_sma_low'] <  PAIRS[symbol]['last_sma_high']: # SELL SIGNAL if true
                            if (assetBal * ask) >  PAIRS[symbol]['minNotional']: # Place SELL ORDER if true.

                                if PAIRS[symbol]['decOrder'] == 0:
                                    qty = int(assetBal)
                                else:
                                    qty = truncate(assetBal, PAIRS[symbol]['decOrder'])

                                load_last = load_csv('BUY', symbol)
                                if load_last == 0:
                                    for i in PAIRS.keys():
                                        if PAIRS[symbol]['base'] == PAIRS[i]['base']:
                                            PAIRS[i]['dividend'] += 1

                                    PAIRS[symbol]['awaitOrder'] = True
                                    currtime()
                                    print('No log, selling based on signal.')
                                    order(SIDE_SELL, symbol, ask, qty)
                                
                                else:
                                    if (ask - load_last[0]) / ask * 100 > (profit + fee):
                                        for i in PAIRS.keys():
                                            if PAIRS[symbol]['base'] == PAIRS[i]['base']:
                                                PAIRS[i]['dividend'] += 1

                                        PAIRS[symbol]['awaitOrder'] = True
                                        currtime()
                                        print(f'\nSelling: {qty} {symbol} at {ask}.')
                                        print('Div:', PAIRS[symbol]['dividend'])
                                        order(SIDE_SELL, symbol, ask, qty)

                    else:
                        if  PAIRS[symbol]['last_sma_low'] >  PAIRS[symbol]['last_sma_high']: # BUY SIGNAL if true
                            if PAIRS[symbol]['dividend'] > 1:
                                baseBal = float(PAIRS[symbol]['baseBal']) / PAIRS[symbol]['dividend']
                            if PAIRS[symbol]['dividend'] == 1:
                                baseBal = float(PAIRS[symbol]['baseBal'])
                                PAIRS[symbol]['baseBal'] = baseBal
                            if PAIRS[symbol]['decOrder'] == 0:
                                qty = int(baseBal / bid)
                            else:
                                qty = truncate(baseBal / bid, PAIRS[symbol]['decOrder'])

                            for i in PAIRS.keys():
                                if PAIRS[symbol]['base'] == PAIRS[i]['base']:
                                    PAIRS[i]['baseBal'] = PAIRS[i]['baseBal'] - baseBal

                            
                            if baseBal > PAIRS[symbol]['minNotional']:
                                for i in PAIRS.keys():
                                    if PAIRS[symbol]['base'] == PAIRS[i]['base']:
                                        if PAIRS[symbol]['dividend'] < 2:
                                            PAIRS[i]['dividend'] = 1
                                        else:
                                            PAIRS[i]['dividend'] -= 1
                                            
                            load_last = load_csv('SELL', symbol)
                            if load_last == 0:
                                PAIRS[symbol]['awaitOrder'] = True
                                currtime()
                                print('No log, buying based on signal.')
                                order(SIDE_BUY, symbol, bid, qty)
                            else:
                                # if (bid - load_last[0]) / bid * 100 > (profit + fee): # Enable for 'no loss' trading.
                                    PAIRS[symbol]['awaitOrder'] = True
                                    base = PAIRS[symbol]['base']
                                    currtime()
                                    print(f'\nBuying: {qty} {symbol} with {baseBal} {base} at {bid}')
                                    print('New div:', PAIRS[symbol]['dividend'])
                                    order(SIDE_BUY, symbol, bid, qty)


                    # If BUY order has not filled until a SELL signal comes, cancel BUY order:
                else:
                    if PAIRS[symbol]['awaitOrder'] == False:
                        if PAIRS[symbol]['order']['side'] == 'BUY':
                            if PAIRS[symbol]['last_sma_low'] <  PAIRS[symbol]['last_sma_high']: # SELL SIGNAL if true
                                PAIRS[symbol]['awaitOrder'] = True
                                cancel = user.cancel_order(symbol=symbol, orderId=PAIRS[symbol]['order']['orderId'])
    
                # If SELL order has not filled until a BUY signal comes, cancel SELL order:
                        if PAIRS[symbol]['order']['side'] == 'SELL':
                            pprint(PAIRS[symbol]['order'])
                            if  PAIRS[symbol]['last_sma_low'] >  PAIRS[symbol]['last_sma_high']: # BUY SIGNAL if true
                                PAIRS[symbol]['awaitOrder'] = True
                                cancel = user.cancel_order(symbol=symbol, orderId=PAIRS[symbol]['order']['orderId'])
    except Exception as e:
        print(e)

def ws():
    global price_streams, kline_streams

    print('[+] WebSockets connected.')
    if test_mode == 1:
        print('\nBuy test mode active. Disable by changing test_mode to 0')
    elif test_mode == 2:
        print('\nSell test mode active. Disable by changing test_mode to 0')
    try:
        twm.start()
        twm.start_user_socket(callback=userData)

        join_price_streams = []
        join_kline_streams = []
        for i in PAIRS.keys():
            price = i.lower() + PAIRS[i]['price']
            kline = i.lower() + PAIRS[i]['kline']
            join_price_streams.append(price)
            join_kline_streams.append(kline)

        price_streams = ['/'.join(join_price_streams)]
        kline_streams = ['/'.join(join_kline_streams)]
        twm.start_multiplex_socket(callback=candles, streams=kline_streams)
        twm.start_multiplex_socket(callback=prices, streams=price_streams)
        twm.join()
    except Exception:
        print('-------------------------------------------WEBSOCKET ERROR-------------------------------------------')
        twm.stop_socket(candles)
        twm.stop_socket(prices)
        sleep(5)
        print('Restarting websocket')
        twm.start_multiplex_socket(callback=prices, streams=price_streams)
        twm.start_multiplex_socket(callback=candles, streams=kline_streams)
    # except Exception as e:
    #     print('\nSocket Error!')
    #     print(e)
    #     print('\nRestarting script!')
    #     os.execv(sys.executable, [sys.executable] + sys.argv) # Restarts script completely, on error.
    # return False

currtime()
history()
min_notional()
open_orders()
account_balance()
ws()
