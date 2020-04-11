# aodv-implementation
This project uses WANET to apply communication between mobile nodes that are constantly changing. Due to the ongoing changes, Ad hoc On-Demand Distance Vector (AODV) Routing must be used to manage the communication path between Node as follows: The previous statement was the reason why this project was started.
## Requirements
```
    -   OS      :   Linux_x86_64
    -   Python  :   3.xx
    -   IMDB    :   redis 
```

** This project prefer with Debian OS

## Prepare System

- Ad-hoc setup (this case i made on debian) config network at <b>/etc/network/interfaces</b>
```
auto wlan0
iface wlan0 inet6 static
    wireless-mode   ad-hoc
    wireless-essid  MESHNetwork
    address    2001:3234::<interface addr>
    netmask    64    
```
- Config hosts at <b>/etc/hosts</b>
```
link_local_ipv6                 hostname
2001:3234::<interface addr>     hostname
```
-   install module in requirements.txt
```
pip3 install requirements.txt 
```


## How to run

- Running scripts

```
python3 aodv_client.py
python3 aodvAPI.py
```

** Running script is prefer with systemd service

## API

- Send message to node || request to host with <b>port 8000</b>
at path <b>/sendMessage</b> in method <b>POST</b>

```json
{
	"toIp": "2001:3234::<interface addr>",
	"message": "Message here"
}
```

- Get routing from node || request to host with <b>port 8000</b>
at path <b>/getRoutingTable</b> in method <b>GET</b>

- Get message from node || request to host with <b>port 8000</b>
at path <b>/getMessage</b> in method <b>GET</b>

<hr>

Contact me: [Facebook: Chatdanai Phakaket ](https://www.facebook.com/Mr.Zack.official) can call me "MRZacK"