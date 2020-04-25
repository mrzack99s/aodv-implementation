#!/bin/bash

sudo systemctl stop aodv
sudo systemctl stop aodv-api
sudo systemctl disable aodv
sudo systemctl disable aodv-api
sudo systemctl daemon-reload

sudo sudo rm -rf /var/aodv-implementation/
sudo sudo rm -f /etc/systemd/system/aodv*

