#!/bin/bash +x

cp sma-trader.service /etc/systemd/system/
cp sma-trader-app.py /etc/systemd/system/

systemctl enable sma-trader.service
systemctl start sma-trader.service

echo "Installed SMA trader systemd service successfully."
echo "Run sudo systemctl status sma-trader to check status."