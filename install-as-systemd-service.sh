#!/bin/bash +x

mkdir /etc/systemd/system/sma-trader

cp sma-trader.service /etc/systemd/system/
cp sma-trader-app.py /etc/systemd/system/sma-trader/
cp config.py /etc/systemd/system/sma-trader/

systemctl enable sma-trader.service
systemctl start sma-trader.service

echo "Installed SMA trader systemd service successfully."
systemctl status sma-trader.service
