from prometheus_client import start_http_server, Gauge, Info, make_wsgi_app
import prometheus_client
import time
import base64
import pycurl
import certifi
from io import BytesIO
import sys
import json


prometheus_client.REGISTRY.unregister(prometheus_client.GC_COLLECTOR)
prometheus_client.REGISTRY.unregister(prometheus_client.PLATFORM_COLLECTOR)
prometheus_client.REGISTRY.unregister(prometheus_client.PROCESS_COLLECTOR)

def refresh_instance_metrics():
    print("refreshing...")
    token= base64.b64encode("admin:Uh68bJcGJithBQl87Q9bp1SW0jZ0kfwht4ZV6u45".encode("UTF-8"))
    buffer = BytesIO()
    c = pycurl.Curl()
    customheaders = ["Authorization: ZenApiKey {0}".format(base64.b64encode("admin:Uh68bJcGJithBQl87Q9bp1SW0jZ0kfwht4ZV6u45".encode("ascii")).decode('UTF8'))]
    c.setopt(c.URL, "https://cpd-zen1.apps.dgsvt5.cp.fyre.ibm.com/icp4data-databases/dg-1672018833030580/zen1/clone_system/clone_engine/status?force_refresh=true")
    c.setopt(c.HTTPHEADER, customheaders)
    c.setopt(c.SSL_VERIFYPEER, 0)
    c.setopt(c.SSL_VERIFYHOST, 0)
    c.setopt(c.CUSTOMREQUEST, "GET")
    c.setopt(c.WRITEDATA, buffer)
    c.setopt(c.CAINFO, certifi.where())
    try:
        c.perform()
    except:
        print(sys.exc_info())
    finally:
        c.close()

    #print(buffer.getvalue().decode('iso-8859-1'))
    jsonstr = json.loads(buffer.getvalue().decode('iso-8859-1'))
    return(jsonstr["result"])
# f = open("instance-level-metrics.txt","r")
# jsonstr = json.load(f)
ary = refresh_instance_metrics()
ns = 'DGInstance'
subsys = ary["cloneEngineName"]+"_"+ary["locationName"]
ary = ary["tableCloneStatus"]
nameAry = []
metricAry = []
for key in ary:
    nameAry.append(key)
for i in range(0,len(nameAry)-1):
    metricAry.append( Gauge(nameAry[i],'',namespace=ns, subsystem=subsys))


if __name__ == '__main__':
    # Start up the server to expose the metrics.
    start_http_server(8080)
    # Generate some requests.
    #generalInfo.set_function(get_Value)
while True:
    i = 0

    ary = refresh_instance_metrics()["tableCloneStatus"]
    for metric in metricAry:
        metric.set(ary[nameAry[i]])
        i+=1
    time.sleep(15)
