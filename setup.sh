#!/bin/bash

sudo mkdir /var/aodv-implementation/
sudo chmod 755 /var/aodv-implementation/
sudo cp -r . /var/aodv-implementation/

sudo cp ./services/* /etc/systemd/system/
sudo systemctl daemon-reload

sudo systemctl enable aodv
sudo systemctl enable aodv-api
sudo systemctl start aodv
sudo systemctl start aodv-api
