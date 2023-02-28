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
import logging


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(threadName)-12.12s] [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

class DGMetrics:
    def __init__(self, url, apikey):
        self.url = url
        self.apikey = apikey
        self.define_prometheus_metrics()
    
    def retrieve_metrics_in_json(self):
        logging.info("refreshing " + str(type(self).__name__))
        buffer = BytesIO()
        c = pycurl.Curl()
        customheaders = ["Authorization: ZenApiKey {0}".format(base64.b64encode(self.apikey.encode("ascii")).decode('UTF8'))]
        c.setopt(c.URL,self.url)
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
        jsonstr = json.loads(buffer.getvalue().decode('iso-8859-1'))
        if jsonstr["resStatus"] == "SUCCESS":
            return(jsonstr["result"])
        else:
            raise(Exception("Failed to get metrics"+str(type(self).__name__)))

    def define_prometheus_metrics(self):
        self.result = self.retrieve_metrics_in_json()

    def set_prometheus_metrics(self):
        self.result = self.retrieve_metrics_in_json()

class InstanceMetrics(DGMetrics):
    def define_prometheus_metrics(self):
        super().define_prometheus_metrics()
        ns = 'DGInstance'
        subsys = self.result["cloneEngineName"]+"_"+self.result["locationName"]
        self.result = self.result["tableCloneStatus"]
        self.metricAry = {}
        for key in self.result:
            self.metricAry[key]=Gauge(key,'',namespace=ns, subsystem=subsys)

    def set_prometheus_metrics(self):
        super().retrieve_metrics_in_json()["tableCloneStatus"]
        for  key in self.metricAry:
            self.metricAry[key].set(self.result[key])


# this is a general purpose generator to identify only the metrics we need. As below, any class that has no subclass is a metric we want.  
def get_only_derived_classes(cls):
	for subclass in cls.__subclasses__():
		if not subclass.__subclasses__():
			yield subclass
		yield from get_only_derived_classes(subclass)

class TableMetrics(DGMetrics):
    # Since we are not retrieving all the table metrics returned, define the ones we want
    # To retrieve the metric from DG and send to Instana, define a subclass of BaseMetric, and call the init with the key, name and description
    #     then, override the getValue method to specify any special processing required as shown below. 
    #     All values returned by getValue should be numeric, since Instana only takes numerics from Prometheus. 
    #     I did not have much luck with "info" type metrics



    class BaseMetric:
        def __init__(self,index,mname,mdesc):
            self.index = index
            self.mname = mname
            self.mdesc = mdesc
        def getvalue(self,item):
            self.value = item[self.index]
    class mReplicationStatus (BaseMetric):
        def __init__(self):
            super().__init__("replicationStatus","Replicating","Table replication1=Enabled")
        def getValue(self,item):
            super().getvalue(item)
            return 1 if self.value == "Enabled" else 0
    class mTableSize(BaseMetric):
        factor_table = {"MB": 1/1e3, "GB": 1.0, "TB: 1": 1e3}
        def __init__(self):
            super().__init__("tableSize","TableSize","Table size in GB")
        def getValue(self,item):
            super().getvalue(item)
            try: 
               return float(self.value[:-2]) * self.factor_table[self.value[-2:]] #converted to GB
            except(e):
                raise Exception("Unexpected size "+self.value)
    class BaseTime(BaseMetric):
         def getValue(self, item):
            super().getvalue(item)
            return (datetime.datetime.now() - datetime.datetime.fromtimestamp(self.value/1e3))/timedelta(minutes=1)       
    class mLastLoadTime(BaseTime):
        def __init__(self):
            super().__init__("lastLoadTime","lastLoad","Minutes since last load")
    class mLastReplTime(BaseTime):
        def __init__(self):
            super().__init__("lastReplicationTime","lastReplication","Minutes since last replicate")

    
    # Instantiate only the lowest level classes in the heirarchy. These represent the metrics we want to capture and send to Instana
    def __init__(self, url, apikey): 
        self.tableMetricstoGet  = [subclass() for subclass in get_only_derived_classes(self.BaseMetric)]
        super().__init__(url,apikey)
    # this sets up the metrics with uniqie names in the Prometheus client. This is a requirement for Prometheus. 
    # Each TableID is a row, 1 column per metric holding a Guage object and a subclass instance of BaseMetric
    def define_prometheus_metrics(self):
        super().define_prometheus_metrics()
        ns = 'DGTable'
        self.nameAryTable = {item["id"]: 
                                [[Gauge(metric.mname,metric.mdesc,namespace=ns, subsystem=item["id"]), metric] for metric in self.tableMetricstoGet] 
                             for item in self.result
                            }

    def set_prometheus_metrics(self):
        super().set_prometheus_metrics()   
        try: 
            [[gaugeary[0].set(gaugeary[1].getValue(item)) for gaugeary in self.nameAryTable[item["id"]]] for item in self.result]
        except Exception as e:
            raise Exception("Cant process input metrics json",e,self.result)

# main program starts here

common_url = "https://cpd-zen1.apps.dgsvt5.cp.fyre.ibm.com/icp4data-databases/dg-1672018833030580/zen1/clone_system/"
token = "admin:Uh68bJcGJithBQl87Q9bp1SW0jZ0kfwht4ZV6u45"

instance_metrics = InstanceMetrics(common_url+"clone_engine/status?force_refresh=true",token)
table_metrics = TableMetrics(common_url+"clone_engine/clone_table",token)

# this turns off all the python run-time related metrics. We only want to send DG metrics to Instana
prometheus_client.REGISTRY.unregister(prometheus_client.GC_COLLECTOR)
prometheus_client.REGISTRY.unregister(prometheus_client.PLATFORM_COLLECTOR)
prometheus_client.REGISTRY.unregister(prometheus_client.PROCESS_COLLECTOR)

if __name__ == '__main__':
    # Start up the prometheus metric server to expose the metrics.
    # I had problems with any port other than 8080. The Instana agent seems to prefer this port
    start_http_server(8080)

while True:
    # Refresh the metrics every 270 seconds, since frequency at which the Instana agent sends to the backend is 300 seconds
    try:
        instance_metrics.set_prometheus_metrics()
        table_metrics.set_prometheus_metrics()
    except Exception as e:
        logging.critical("Refresh failed" % e)
    time.sleep(250)