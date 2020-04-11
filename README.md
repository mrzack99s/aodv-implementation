# aodv-implementation

## Requirements
```
    -   OS      :   Linux_x86_64
    -   Python  :   3.xx
    -   IMDB    :   redis 
```

** This project prefer with Debian OS

## Prepare System

- Ad-hoc setup (this case i made on debian) config network at /etc/network/interfaces
```
auto wlan0
iface wlan0 inet6 static
    wireless-mode   ad-hoc
    wireless-essid  MESHNetwork
    address    2001:3234::<interface addr>
    netmask    64    
```
- Config hosts at /etc/hosts
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

Contact me: [Facebook: Chatdanai Phakaket ](https://www.facebook.com/Mr.Zack.official) can call me "MRZacK"