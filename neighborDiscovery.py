import socket
import subprocess

globalPort = 20001

interfaceName = subprocess.check_output("iw dev | awk '$1==\"Interface\"{print $2}'", shell=True).decode().replace("\n","")

hostname = socket.gethostname()
allIp = [socket.getaddrinfo(hostname, None, socket.AF_INET6, socket.SOCK_DGRAM)[0][4][0],
           socket.getaddrinfo(hostname, None, socket.AF_INET6, socket.SOCK_DGRAM)[1][4][0]]

for ip in allIp:
    if ip[:4] == "fe80":
        link_local_IPv6 = ip
    elif ip[:4] == "2001":
        ownIpv6 = ip


# Process

def neighborDiscovery():
    ipDiscovery = subprocess.check_output("ping6 -c 3 ff02::1%"+interfaceName+" | grep from | awk '{print $4\" \"$7}' | sed 's/time=//'",
                                          shell=True)
    ipDiscovery = ipDiscovery.decode().split("\n")
    ipDiscovery.remove('')

    for ip in ipDiscovery:
        if ip.find(link_local_IPv6) != -1:
            ipDiscovery.remove(ip)

    listNeighborProcess = dict()
    listNeighbor = list()
    for ip in ipDiscovery:
        ip = ip.split(' ')
        ip[0] = ip[0].replace("%" + interfaceName + ":", "")

        try:
            listNeighborProcess[ip[0]]["count"] += 1
            listNeighborProcess[ip[0]]["delay"] = (listNeighborProcess[ip[0]]["delay"] + float(ip[1])) / \
                                                  listNeighborProcess[ip[0]]["count"]

            if listNeighborProcess[ip[0]]["delay"] > 6:
                listNeighborProcess.pop(listNeighborProcess[ip[0]])
                if ip[0] in listNeighbor:
                    listNeighbor.remove(ip[0])

            else:
                if ip[0] not in listNeighbor:
                    listNeighbor.append(ip[0])

        except:
            listNeighborProcess.update({
                ip[0]: {
                    "ipAddr": ip[0],
                    "delay": float(ip[1]),
                    "count": 1
                }
            })

    return listNeighbor
