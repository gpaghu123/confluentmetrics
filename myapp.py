from prometheus_client import start_http_server, Gauge, Info, make_wsgi_app
import prometheus_client
import time
import base64
import logging
import pycurl
import certifi
from io import BytesIO
import sys
import json


prometheus_client.REGISTRY.unregister(prometheus_client.GC_COLLECTOR)
prometheus_client.REGISTRY.unregister(prometheus_client.PLATFORM_COLLECTOR)
prometheus_client.REGISTRY.unregister(prometheus_client.PROCESS_COLLECTOR)

def refresh_instance_metrics():
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

    print(buffer.getvalue().decode('iso-8859-1'))
    try:
        tstr = buffer.getvalue().decode('iso-8859-1')
        jsonstr = json.loads(tstr)
        if jsonstr["resStatus"] == "SUCCESS":
            return(jsonstr["result"])
        else:
            raise Exception("Unexpected return status"+jsonstr["resStatus"])
    except:
        raise Exception("Invalid json received" + tstr)
# f = open("instance-level-metrics.txt","r")
# jsonstr = json.load(f)
ary = refresh_instance_metrics()
nameAry = []
metricAry = []
for key in ary:
    if isinstance(ary[key], str):
        s = "yes"
    else:
        s = "no"
    print(key, type(ary[key]), s, ary[key])