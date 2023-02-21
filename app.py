from prometheus_client import start_http_server, Gauge, Info, make_wsgi_app
import prometheus_client
import time
import base64
import pycurl
import certifi
from io import BytesIO
import sys
import json
import datetime
from datetime import timedelta


prometheus_client.REGISTRY.unregister(prometheus_client.GC_COLLECTOR)
prometheus_client.REGISTRY.unregister(prometheus_client.PLATFORM_COLLECTOR)
prometheus_client.REGISTRY.unregister(prometheus_client.PROCESS_COLLECTOR)
def get_metrics(item):
    # print(item)

    time_since_lastLoadTime = datetime.datetime.now() - datetime.datetime.fromtimestamp(item["lastLoadTime"]/1e3)
    time_since_lastReplicationTime = datetime.datetime.now() - datetime.datetime.fromtimestamp(item["lastReplicationTime"]/1e3)
    if item["replicationStatus"] == "Enabled":
            replicating = 1
    else:
            replicating = 0
    rname = item["id"]
    sizeFact = item["tableSize"][-2:]
    sizeNum = float(item["tableSize"].split(" ")[0])
    if sizeFact == "MB":
        sizeRet = sizeNum/1e3
    elif sizeFact == "GB":
        sizeRet = sizeNum/1.0
    elif sizeFact == "TB":
        sizeRet = sizeNum * 1e3
    else:
        tb = sys.exc_info()[2]
        raise(ValueError("Invalid table size value")).with_traceback(tb)
    # print(rname)
    return (rname,replicating,sizeRet,time_since_lastLoadTime/timedelta(minutes=1),time_since_lastReplicationTime/timedelta(minutes=1))

def refresh_table_metrics():
    print("refreshing...")
    token= base64.b64encode("admin:Uh68bJcGJithBQl87Q9bp1SW0jZ0kfwht4ZV6u45".encode("UTF-8"))
    buffer = BytesIO()
    c = pycurl.Curl()
    customheaders = ["Authorization: ZenApiKey {0}".format(base64.b64encode("admin:Uh68bJcGJithBQl87Q9bp1SW0jZ0kfwht4ZV6u45".encode("ascii")).decode('UTF8'))]
    c.setopt(c.URL,"https://cpd-zen1.apps.dgsvt5.cp.fyre.ibm.com/icp4data-databases/dg-1672018833030580/zen1/clone_system/clone_engine/clone_table")
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
    #print(jsonstr)
    return(jsonstr["result"])

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

arytable = refresh_table_metrics()
nstable = 'DGTable'
#subsys = ary["cloneEngineName"]+"_"+ary["locationName"]
#ary = ary["tableCloneStatus"]
nameAryTable = {}
for item in arytable:
    rname,replicating,sizeRet,lastload,lastrepl = get_metrics(item)
    metricAryTable = {}
    metricAryTable["repl"] = Gauge("Replicating","Table replication. 1=Enabled",namespace=nstable, subsystem=rname)
    metricAryTable["size"] = Gauge("TableSize","Table size in GB",namespace=nstable, subsystem=rname)
    metricAryTable["lastload"]= Gauge("lastload","Minutes since last load",namespace=nstable, subsystem=rname)
    metricAryTable["lastrepl"]= Gauge("lastrepl","Minutes since last replicate",namespace=nstable, subsystem=rname)
    nameAryTable[rname] = metricAryTable
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
    ary = refresh_table_metrics()
    for item in ary:
        rname,replicating,sizeRet,lastload,lastrepl = get_metrics(item)
        nameAryTable[rname]["repl"].set(replicating)
        nameAryTable[rname]["size"].set(sizeRet)
        nameAryTable[rname]["lastload"].set(lastload)
        nameAryTable[rname]["lastrepl"].set(lastrepl)
    time.sleep(15)
