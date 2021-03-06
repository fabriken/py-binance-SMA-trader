# py-binance-SMA-trader

A simple trading bot written in python. Trade multiple coin pairs simultaneously on Binance using Simple Moving Average(SMA) signal.
Can be customized to fit your favorite signal (RSI, MA, EMA, MACD, BBANDS etc.), as the full TA-Lib is at your disposal.

Will sell if the configured profit margin is > last buy price.
Define as many pairs as you like to trade in the PAIRS variable.

Individual config for profit and sma low & high for each pair.

Before running, set the API_KEY and API_SECRET in the config.py file.

Test mode can be enabled by setting 'test_mode = 1'.

This will create a test order, so you can make sure your settings (mainly decimal places) plays niceley with Binance API.

# Required packages:

pip install TA-Lib (Use tar.gz from website if having trouble installing)

pip install python-binance

pip install numpy (numpy should be included in TA-Lib, but if not run this)

TA-Lib:
https://pypi.org/project/TA-Lib/

python-binance:
https://python-binance.readthedocs.io/en/latest/overview.html

# Run as systemd service:

Change 'User=user' to your linux user name under [Service] in sma-trader.service

Make script executable by running: sudo chmod +x install-as-systemd-service.sh

Then run: sudo ./install-as-systemd-service.sh to install the systemd service.

# DISCLAIMER: Free to use trading bot, use at your own risk!
# I do not take any responsibility for any losses.
