import csv
import os
import datetime
from dotenv import load_dotenv
from pprint import pprint
import talib
import numpy
from binance.client import Client
from binance.enums import *
from binance import ThreadedWebsocketManager

api_key = os.environ.get('binance_key')
api_secret = os.environ.get('binance_secret')
user = Client(api_key, api_secret) # Client for user endpoints.
public = Client()                  # Client for public endpoints.
FEE = 0.00075                      # 0.075% in decimal. Set trading fee here, differs between different VIP levels.

load_dotenv()

PAIRS = {
    'GALAUSDT': {
        'kline': '@kline_1m',
        'price': '@bookTicker',
        'decPrice': 5,
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
        'symbol': 'GALA',
        'base': 'USDT',
        'awaitOrder': False,
        'hodl': 0,
        'lastPrice': 0,
        'profit': 1.01 + FEE, # Set profit margin here.
        'closes': []
    },
    'CELRUSDT':    {
        'kline': '@kline_1m',
        'price': '@bookTicker',
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
        'symbol': 'CELR',
        'base': 'USDT',
        'awaitOrder': False,
        'hodl': 0,
        'lastPrice': 0,
        'profit': 1.01 + FEE, # Set profit margin here.
        'closes': []
    },
    'DYDXUSDT':    {
        'kline': '@kline_1m',
        'price': '@bookTicker',
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
        'symbol': 'DYDX',
        'base': 'USDT',
        'awaitOrder': False,
        'hodl': 0,
        'lastPrice': 0,
        'profit': 1.01 + FEE, # Set profit margin here.
        'closes': []
    },
    'SHIBUSDT':    {
        'kline': '@kline_1m',
        'price': '@bookTicker',
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
        'hodl': 0,
        'lastPrice': 0,
        'profit': 1.01 + FEE, # Set profit margin here.
        'closes': []
    }
}

dec = 0
def truncate(num: float, n: int = dec) -> float:
    return int(num*10**n)/10**n

def currtime():
    time = datetime.datetime.now().strftime('%Y-%d-%m %H:%M:%S')
    return time

def min_notional():
    print('Fetching min notionals.')
    for i in PAIRS.keys():
        info = public.get_symbol_info(i)
        PAIRS[i]['minNotional'] = float(info['filters'][3]['minNotional'])
        # print(PAIRS[i]['symbol'], PAIRS[i]['minNotional'])

def open_orders(): # Check what's currently in order.
    print('Fetching open orders.')
    global div
    countBase = []
    count = 0
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
    print('Number of pairs with the same base:', div)

def account_balance(): # Get all balances at once instead of one query per symbol, saves API payload.
    print('Fetching account balance.')
    global div
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

def history():
    print('Fetching history.')
    for i in PAIRS.keys():
        candlesticks = public.get_historical_klines(i, PAIRS[i]['kline'][-2:], "Yesterday", "Today")
        for closes in candlesticks:
            PAIRS[i]['closes'].append(float(closes[4]))

def save_csv(side, symbol, price, qty):
    if side == 'BUY':
        with open(f'{side}-{symbol}.csv', 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([side, symbol, price, qty])
            print(f'Saving {side, symbol, price, qty} to CSV.')
        return True
    else:
        with open(f'{side}-{symbol}.csv', 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([side, symbol, price, qty])
            print(f'Saving {side, symbol, price, qty} to CSV.')
        return True

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
        print(f'No log file found for {pair}')
        return False

def order(side, symbol, price, qty):
    for i in PAIRS.keys():
        dec = PAIRS[i]['decPrice']

    if float(price) < float(0.00001):
        price = f"{price:.{dec}f}"

    print('Placing order: ' + side, symbol, price, qty)
    try:
        # order = user.create_test_order( # Test order
        order = user.create_order( # Real order
            symbol=symbol,
            side=side,
            type=ORDER_TYPE_LIMIT,
            timeInForce=TIME_IN_FORCE_GTC,
            quantity=qty,
            price=price)               
        # print(order)
    except Exception as e:
        print(e)
        return False
    return True

def ws():

    print('WebSocket connected.')

    twm = ThreadedWebsocketManager(api_key=api_key, api_secret=api_secret)
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
                        print('FILLED')
                        if side == 'BUY':
                            print('BUY Order filled.')
                            div = div - 1
                            try: # Load last order.
                                with open(f"{side}-{pair}.csv") as f:
                                    csv_reader = csv.reader(f)
                                    for line in csv_reader:
                                        last_side = line[0]
                                        last_price = float(line[2])
                                        last_qty = float(line[3])

                                    diffQty = float(qty) - float(last_qty)
                                    diffPercent = (float(diffQty) / float(qty)) * 100
                                    diffPrice = float(last_price) - float(price)
                                    percentCalc = (float(diffPrice) / float(last_price)) * 100
                                    percentChange = '{:.2f}'.format(percentCalc - FEE)
                                    
                                    PAIRS[i]['lastPrice'] = price

                                    print(f'\nTrade gain: {percentChange}% Qty diff: {diffQty}, {diffPercent}%s')
                                    
                                    save_csv(side, pair, price, qty)

                            except FileNotFoundError:
                                print(f'FILLED - But no log file found for {pair}')
                                print('No stats..')
                                save_csv(side, pair, price, qty)

                        else:
                            print('SELL Order filled.')
                            div = div + 1
                            try: # Load last order.
                                with open(f"{side}-{pair}.csv") as f:
                                    csv_reader = csv.reader(f)
                                    for line in csv_reader:
                                        last_side = line[0]
                                        last_price = float(line[2])
                                        last_qty = float(line[3])

                                    PAIRS[i]['lastPrice'] = price
                                    save_csv(side, pair, price, qty)

                            except FileNotFoundError:
                                print(f'FILLED - But no log file found for {pair}')
                                save_csv(side, pair, price, qty)

    def market(msg):
        global div
        # pprint(msg)
        for i in PAIRS.keys():
            symbol = PAIRS[i]['symbol']
            base = PAIRS[i]['base']
            minNotional = PAIRS[i]['minNotional']
            price = (PAIRS[i]['symbol'].lower() + PAIRS[i]['base'].lower() + PAIRS[i]['price'])
            kline = (PAIRS[i]['symbol'].lower() + PAIRS[i]['base'].lower() + PAIRS[i]['kline'])

            if msg['stream'] == price:
                PAIRS[i]['bid'] = truncate(float(str(msg['data']['b'])), PAIRS[i]['decPrice'])
                PAIRS[i]['ask'] = truncate(float(str(msg['data']['a'])), PAIRS[i]['decPrice'])

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

                    if PAIRS[i]['order'] == 0: # If not in order, create an inital order, buy or sell, but await signal first:
                        assetBal = float(PAIRS[i]['assetBal'])
                        ask = PAIRS[i]['ask']
                            # div = div - 1
                        
                    if assetBal * ask > minNotional: # Place sell order if true.
                        # div = div - 1
                        if PAIRS[i]['decOrder'] == 0:
                            qty = int(assetBal)
                        else:
                            qty = truncate(assetBal, PAIRS[i]['decOrder'])
                            
                        if PAIRS[i]['awaitOrder'] == False:
                            if last_sma_low < last_sma_high:
                                if PAIRS[i]['lastPrice'] == 0:
                                    pair = symbol + base
                                    load = load_csv('BUY', pair)
                                    if load: # If load is successful, base the order from past trade:
                                        print(f'Bought {pair} at', load)
                                        PAIRS[i]['lastPrice'] = load
                                        # if load < ask * PAIRS[i]['profit']:
                                        PAIRS[i]['awaitOrder'] = True
                                        print(PAIRS[i]['symbol'], last_sma_low, last_sma_high)
                                        print(f'\nSelling: {assetBal} {symbol} at {ask}')
                                        order(SIDE_SELL, PAIRS[i]['symbol'] + PAIRS[i]['base'], ask, qty)
                                    else: # Just place and order, this will be the starting point for the trading:
                                            PAIRS[i]['awaitOrder'] = True
                                            print(f'\nSelling: {assetBal} {symbol} at {ask}')
                                            order(SIDE_SELL, PAIRS[i]['symbol'] + PAIRS[i]['base'], ask, qty)
                                else:
                                    if PAIRS[i]['lastPrice'] < ask * PAIRS[i]['profit']:
                                        PAIRS[i]['awaitOrder'] = True
                                        print(PAIRS[i]['symbol'], last_sma_low, last_sma_high)
                                        print(f'\nSelling: {assetBal} {symbol} at {ask}')
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
                            if last_sma_low > last_sma_high:
                                if baseBal > minNotional:
                                    # print(PAIRS[i]['symbol'], last_sma_low, last_sma_high)
                                    if PAIRS[i]['lastPrice'] == 0:
                                        pair = symbol + base
                                        load = load_csv('SELL', pair)
                                        if load:
                                            print(f'Sold {pair} for', load)
                                            PAIRS[i]['lastPrice'] = load
                                            # if load > bid * PAIRS[i]['profit']:
                                            PAIRS[i]['awaitOrder'] = True
                                            print('Dividend Load:', div)
                                            print(f'\nBuying: {qty} {symbol} with {baseBal} {base} at {bid}')
                                            order(SIDE_BUY, PAIRS[i]['symbol'] + PAIRS[i]['base'], bid, qty)
                                        else:
                                                PAIRS[i]['awaitOrder'] = True
                                                print('Dividend No load:', div)
                                                print(f'\nBuying: {qty} {symbol} with {baseBal} {base} at {bid}')
                                                order(SIDE_BUY, PAIRS[i]['symbol'] + PAIRS[i]['base'], bid, qty)
                                    else:
                                            if PAIRS[i]['lastPrice'] > bid * PAIRS[i]['profit']:

                                                PAIRS[i]['awaitOrder'] = True
                                                print('Dividend Last:', div)
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

# history()
# min_notional()
open_orders()
# account_balance()
# ws()
