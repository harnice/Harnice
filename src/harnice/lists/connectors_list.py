def disconnects_in_net(net):
    disconnects = []
    for connector in fileio.read_tsv("system connector list"):
        if connector.get("net") == net:
            if connector.get("disconnect") == "TRUE":
                disconnects.append(connector.get("device_refdes"))
    return disconnects