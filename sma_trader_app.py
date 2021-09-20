import config, csv, datetime, numpy, os, sys, talib
from binance.client import Client
from binance.enums import *
from binance import ThreadedWebsocketManager

api_key = config.API_KEY           # Set key and secret in the config.py file.
api_secret = config.API_SECRET
twm = ThreadedWebsocketManager(api_key=api_key, api_secret=api_secret)

user = Client(api_key, api_secret) # Client for user endpoints.
public = Client()                  # Client for public endpoints.
fee = 0.00075                      # 0.075% in decimal. Set trading fee here, differs between different VIP levels.

test_mode = 0                      # Place a test order instead of a real one. 0 = off | 1 = 0 on

PAIRS = {                          # Define pairs to trade here:
    'GALAUSDT': {                  # PAIRS.keys()
        'symbol': 'GALA',          # Make sure symbol and base are set to the same as the PAIRS.keys().
        'base': 'USDT',            # Make sure symbol and base are set to the same as the PAIRS.keys().
        'kline': '@kline_15m',     # Set kline interval here.
        'price': '@bookTicker',    # Set price ticker here.
        'profit': 2 + fee,         # Set profit margin here.
        'decPrice': 5,             # Count how many decimals the price has and set here.
        'decOrder': 0,             # Same as decPrice, but for the order.
        'smaLow': 5,               # Set the sma low here, default 5.
        'smaHigh': 10,             # Set the sma low here, default 10.
        'bid': 0,
        'ask': 0,
        'baseBal': 0,
        'assetBal': 0,
        'minNotional': 0,
        'order': 0,
        'qty': 0,
        'awaitOrder': False,
        'lastPrice': 0,
        'closes': []
    },
    'CELRUSDT':    {
        'symbol': 'CELR',
        'base': 'USDT',
        'kline': '@kline_1h',
        'price': '@bookTicker',
        'profit': 2 + fee, # Set profit margin here.
        'decPrice': 5,
        'decOrder': 1,
        'bid': 0,
        'ask': 0,
        'baseBal': 0,
        'assetBal': 0,
        'minNotional': 0,
        'order': 0,
        'smaLow': 5,
        'smaHigh': 10,
        'qty': 0,
        'awaitOrder': False,
        'lastPrice': 0,
        'closes': []
    },
    'DYDXUSDT':    {
        'symbol': 'DYDX',
        'base': 'USDT',
        'kline': '@kline_1h',
        'price': '@bookTicker',
        'profit': 2 + fee, # Set profit margin here.
        'decPrice': 3,
        'decOrder': 2,
        'bid': 0,
        'ask': 0,
        'baseBal': 0,
        'assetBal': 0,
        'minNotional': 0,
        'order': 0,
        'smaLow': 5,
        'smaHigh': 10,
        'qty': 0,
        'awaitOrder': False,
        'lastPrice': 0,
        'closes': []
    },
    'SHIBUSDT':    {
        'kline': '@kline_15m',
        'price': '@bookTicker',
        'profit': 2 + fee, # Set profit margin here.
        'decPrice': 8,
        'decOrder': 0,
        'bid': 0,
        'ask': 0,
        'baseBal': 0,
        'assetBal': 0,
        'minNotional': 0,
        'order': 0,
        'smaLow': 5,
        'smaHigh': 10,
        'qty': 0,
        'symbol': 'SHIB',
        'base': 'USDT',
        'awaitOrder': False,
        'lastPrice': 0,
        'closes': []
    }
}

dec = 0
def truncate(num: float, n: int = dec) -> float: # Limits decimal points, to fit binance filters
    return int(num*10**n)/10**n

def currtime():
    time = datetime.datetime.now().strftime('%Y-%d-%m %H:%M:%S')
    return time

def history():
    print('\n[+] Fetching history.')
    for i in PAIRS.keys():
        candlesticks = public.get_historical_klines(i, PAIRS[i]['kline'][-2:], "Yesterday", "Today")
        for closes in candlesticks:
            PAIRS[i]['closes'].append(float(closes[4]))

def min_notional():
    print('[+] Fetching min notionals.')
    for i in PAIRS.keys():
        try:
            info = public.get_symbol_info(i)
            PAIRS[i]['minNotional'] = float(info['filters'][3]['minNotional'])
            # print(PAIRS[i]['symbol'], PAIRS[i]['minNotional'])
        except Exception as e:
            print(e)
        return False
    # return True

def open_orders(): # Check what's currently in order.
    global div
    countBase = []
    count = 0
    try:
        orders = user.get_open_orders()
        for i in PAIRS.keys():
            countBase.append(PAIRS[i]['base'])
            calcDiv = len(countBase)
            if orders:
                for index in range(len(orders)):
                    if i == orders[index]['symbol']:
                        PAIRS[i]['order'] = orders[index]
                        if PAIRS[i]['order']['side'] == 'SELL':
                            count += 1
            div = calcDiv - count            
        print('[-] Fetching open orders: \n    Base dividend:', div)
    except Exception as e:
        print(e)
        return False

def account_balance(): # Get all balances at once instead of one query per symbol, saves API payload.
    print('[+] Fetching account balance.')
    global div
    try:
        get_bal = user.get_account()
        balance = get_bal['balances']
        if balance:
            for i in PAIRS.keys():
                for asset in balance:
                    if asset['asset'] == PAIRS[i]['symbol']:
                        PAIRS[i]['assetBal'] = float(asset['free'])
                        if float(asset['free']) > 0.001:
                            div = div - 1

                    if asset['asset'] == PAIRS[i]['base']:
                        PAIRS[i]['baseBal'] = float(asset['free'])
    except Exception as e:
        print(e)
        return False

def save_csv(side, symbol, price, qty):
    if side == 'BUY':
        try:
            with open(f'{side}-{symbol}.csv', 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([side, symbol, price, qty])
                print(f'Saving {side, symbol, price, qty} to CSV.')
            return True
        except Exception as e:
            print(e)
        return False
    else:
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
    try: # Load last order.
        with open(f"{side}-{pair}.csv") as f:
            csv_reader = csv.reader(f)
            for line in csv_reader:
                last_side = line[0]
                last_price = float(line[2])
                last_qty = float(line[3])

            return last_price
    except FileNotFoundError:
        print(f'No log file found for {side}-{pair}')
        # for i in PAIRS.keys():
        #     if i == pair:
        #         PAIRS[i]['lastPrice'] = 1
        return False

def order(side, symbol, price, qty):
    for i in PAIRS.keys():
        dec = PAIRS[i]['decPrice']
    # Binance API won't accept scientific notation.
    # If price has been formatted to scientific notation, format back to decimal. Ex. 8.04e-06 to 0.00000804.
    # * Python formats numbers with more than 5 decimals to scientific notation.
    if float(price) < float(0.00001):
        price = f"{price:.{dec}f}"
    try:
        if test_mode == 1:
            print('TEST MODE ACTIVE, NO ORDERS WILL BE EXECUTED! Disable by setting test_mode = 0')
            order = user.create_test_order( # Test order
                symbol=symbol,
                side=side,
                type=ORDER_TYPE_LIMIT,
                timeInForce=TIME_IN_FORCE_GTC,
                quantity=qty,
                price=price)
            print(order)
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
        return False

def ws():
    
    print('[+] WebSocket connected.')

    try:
        twm.start()

        def userData(msg):
            global div
            for i in PAIRS.keys():
                symbol = PAIRS[i]['symbol']
                base = PAIRS[i]['base']
                pair = symbol + base

                if msg['e'] == 'executionReport':
                    # pprint(msg)
                    side = msg['S']
                    # symbol = ['s']
                    price = msg['p']
                    qty = msg['q']
                    if pair == msg['s']:

                        if msg['X'] == 'NEW':
                            print('\nNEW ORDER PLACED: ' + pair, side, price, qty)

                        if msg['X'] == 'FILLED':

                            if side == 'BUY':
                                print('\nBUY ORDER FILLED:', pair, price, qty)
                                div = div - 1
                                save_csv(side, pair, price, qty)

                            else:
                                print('\nSELL ORDER FILLED:', pair, price, qty)
                                div = div + 1
                                
                                if os.path.exists(f"BUY-{pair}.csv"): 
                                    os.remove(f"BUY-{pair}.csv") # Remove last buy file, so a new buy in can happen.

        def market(msg):
            global div
            # pprint(msg)
            for i in PAIRS.keys():
                symbol = PAIRS[i]['symbol']
                base = PAIRS[i]['base']
                minNotional = PAIRS[i]['minNotional']
                price = (PAIRS[i]['symbol'].lower() + PAIRS[i]['base'].lower() + PAIRS[i]['price'])
                kline = (PAIRS[i]['symbol'].lower() + PAIRS[i]['base'].lower() + PAIRS[i]['kline'])

                try:
                    if msg['stream'] == price:
                        PAIRS[i]['bid'] = truncate(float(str(msg['data']['b'])), PAIRS[i]['decPrice'])
                        PAIRS[i]['ask'] = truncate(float(str(msg['data']['a'])), PAIRS[i]['decPrice'])
                except Exception as e:
                    print('\nSocket Error!')
                    print(e)
                    os.execv(sys.executable, [sys.executable] + sys.argv) # Restarts script completely, on error.

                if msg['stream'] == kline:
                    candle = msg['data']['k']
                    close = float(candle['c'])
                    is_candle_closed = candle['x']

                    if is_candle_closed:
                        PAIRS[i]['closes'].append(truncate(float(close) , PAIRS[i]['decPrice']))

                if len(PAIRS[i]['closes']) >= PAIRS[i]['smaHigh']:
                        np_closes = numpy.array(PAIRS[i]['closes'])
                        sma_low = talib.SMA(np_closes, timeperiod=PAIRS[i]['smaLow'])
                        sma_high = talib.SMA(np_closes, timeperiod=PAIRS[i]['smaHigh'])
                        last_sma_low = truncate(sma_low[-1], PAIRS[i]['decPrice'])
                        last_sma_high = truncate(sma_high[-1],  PAIRS[i]['decPrice'])
                        # last_sma_low = 60 # Test values
                        # last_sma_high = 55 # Test values
                        
                        if PAIRS[i]['bid'] and PAIRS[i]['ask']: # Make sure we have prices.
                            assetBal = float(PAIRS[i]['assetBal'])
                            bid = PAIRS[i]['bid']
                            ask = PAIRS[i]['ask']


                            if PAIRS[i]['order'] == 0: # If not in order, create an inital order, buy or sell, but await signal first:
                                assetBal = float(PAIRS[i]['assetBal'])
                                bid = PAIRS[i]['bid']
                                ask = PAIRS[i]['ask']
                                # div = div - 1
                                
                            if assetBal * ask > minNotional: # Place SELL ORDER if true.
                                # div = div - 1
                                if PAIRS[i]['decOrder'] == 0:
                                    qty = int(assetBal)
                                else:
                                    qty = truncate(assetBal, PAIRS[i]['decOrder'])
                                    
                                if PAIRS[i]['awaitOrder'] == False:
                                    if last_sma_low < last_sma_high: # SELL SIGNAL - if true
                                        # if PAIRS[i]['lastPrice'] == 0:
                                            pair = symbol + base
                                            load_buy = load_csv('BUY', pair)
                                            if load_buy: # If load_buy is successful, base the order from past trade:

                                                if (ask - load_buy) / ask * 100 > PAIRS[i]['profit']:
                                                    PAIRS[i]['awaitOrder'] = True
                                                    gain = '{:.2f}'.format((ask - load_buy) / ask * 100)

                                                    print(f'\nSelling {assetBal} {symbol} at: {ask}, bought at: {load_buy}')
                                                    print(f'Potential gain: {gain}%')

                                                    order(SIDE_SELL, PAIRS[i]['symbol'] + PAIRS[i]['base'], ask, qty)

                                            else: # Just place an order, this will be the starting point for the trading:
                                                    PAIRS[i]['awaitOrder'] = True
                                                    print(f'\nSelling: {assetBal} {symbol} at {ask}, no past buy trade logged.')
                                                    order(SIDE_SELL, PAIRS[i]['symbol'] + PAIRS[i]['base'], ask, qty)

                            else: # place BUY ORDER
                                if div > 1:
                                    baseBal = float(PAIRS[i]['baseBal']) / div
                                    bid = PAIRS[i]['bid']
                                else:
                                    baseBal = float(PAIRS[i]['baseBal'])
                                    bid = PAIRS[i]['bid']

                                if PAIRS[i]['decOrder'] == 0:
                                    qty = int(baseBal / bid)
                                else:
                                    qty = truncate(baseBal / bid, PAIRS[i]['decOrder'])

                                if PAIRS[i]['awaitOrder'] == False:
                                    if last_sma_low > last_sma_high: # BUY SIGNAL - if true
                                        if baseBal > minNotional:
                                            PAIRS[i]['awaitOrder'] = True
                                            print('Dividend:', div)
                                            print(f'\nBuying: {qty} {symbol} with {baseBal} {base} at {bid}')
                                            order(SIDE_BUY, PAIRS[i]['symbol'] + PAIRS[i]['base'], bid, qty)

        twm.start_user_socket(callback=userData)
        join_streams = []
        for i in PAIRS.keys():
            price = (PAIRS[i]['symbol'].lower() + PAIRS[i]['base'].lower() + PAIRS[i]['price'])
            kline = (PAIRS[i]['symbol'].lower() + PAIRS[i]['base'].lower() + PAIRS[i]['kline'])
            join_streams.append(price)
            join_streams.append(kline)

        streams = ['/'.join(join_streams)]
        twm.start_multiplex_socket(callback=market, streams=streams)
        twm.join()

    except Exception as e:
        print('\nSocket Error!')
        print(e)
        print('\nAttempting to restart script!')
        os.execv(sys.executable, [sys.executable] + sys.argv) # Restarts script completely, on error.
    # return False

history()
min_notional()
open_orders()
account_balance()
ws()
