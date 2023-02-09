from prometheus_client import start_http_server, Gauge, Info
import prometheus_client
import random
import time
import json
from urllib.request import urlopen
import base64
import urllib.request


# token= base64.b64encode("admin:Uh68bJcGJithBQl87Q9bp1SW0jZ0kfwht4ZV6u45".encode("ascii"))

# urlOltpInstance="https://cpd-zen1.apps.dgsvt5.cp.fyre.ibm.com/icp4data-databases/dg-1672018833030580/zen1/clone_system/clone_engine/status?force_refresh=true"
 

# req = urllib.request.Request( urlOltpInstance,headers={"Authorization": "ZenApiKey %s" % token,"Content-Type": "application/json"}, method="GET", unverifiable=True)

# print(req)
# print(req.headers)
# with urllib.request.urlopen(req) as f:
#     jsonstr = json.load(f)
f = open("instance-level-metrics.txt","r")
jsonstr = json.load(f)
ary = jsonstr["result"]

nameAry = []
metricAry = []
for key in ary:
    nameAry.append(key)
for i in range(0,len(nameAry)-1):
    metricAry.append( Info(nameAry[i],nameAry[i]))

prometheus_client.REGISTRY.unregister(prometheus_client.GC_COLLECTOR)
prometheus_client.REGISTRY.unregister(prometheus_client.PLATFORM_COLLECTOR)
prometheus_client.REGISTRY.unregister(prometheus_client.PROCESS_COLLECTOR)

def get_Value():
    """A dummy function that takes some time."""
    return(ary["result"])

if __name__ == '__main__':
    # Start up the server to expose the metrics.
    start_http_server(8081)
    # Generate some requests.
    #generalInfo.set_function(get_Value)
    while True:
        i = 0
        for metric in metricAry:
            metric.info({nameAry[i]:ary[nameAry[i]]})
            i+=1
        time.sleep(5)
