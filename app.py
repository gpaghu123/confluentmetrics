import pycurl
import certifi
from io import BytesIO
import sys
import logging
import re
from flask import Flask
import requests
from decimal import Decimal

global dev_mode
warning_threshold =1000
critical_threshold = 5000

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(threadName)-12.12s] [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

#These variables need to be changed per the actual requirement. better to put them in toml files, and to the environment
common_url = ''
token = ''
event_url = "http://localhost:42699/com.instana.plugin.generic.event"

help_str = "# HELP confluent_cons_consumer_lag_offsets The lag (consolidated by consumer_group) between a group member's committed offset and the partition's high watermark.\n"
type_str = "# TYPE confluent_cons_consumer_lag_offsets gauge\n"

def retrieve_metrics(common_url, token): 
        def fexp(number):
            (sign, digits, exponent) = Decimal(number).as_tuple()
            return len(digits) + exponent - 1

        def fman(number):
            return Decimal(number).quantize(1)
        
        def remove_timestamp(s):
            # this function removes the timestamp at the end of confluent metrics that Instana does not like. 
            # all metrics begin with confluent, and have a fixed format that the re is matching for.  
            # The backend would not import metrics that has a real number format. That is why we retains only the mantissa
            
            m = re.match(r"(^confluent\S*)(\s*\S*\s*)\d*$",s) 
            if m:
                print("grp 1 " +m.group(1))
                print("grp 2 "+m.group(2))
                mantis = fman(m.group(2))
                print("mantis " + str(mantis))
                s = m.group(1) + " " + str(mantis)
            return s
        
        def generate(strary):
         res_str = ""
         for s in strary:
            res_str +=  s + '\n' 
         return(res_str)

        # consolidate the lags by consumer_group_id. Hopefully this will allow creation of alerts
        def process_lags(strary):
            lag_dict = {}
            for s in strary:
                m = re.match(r"confluent_kafka_server_consumer_lag_offsets{",s)
                if m:
                    m1 = re.search(r"consumer_group_id=(\S*\")\S}\s*(\d*)",s)
                    if m1:
                        #print("consumer group:", m1.group(1), "lag:", m1.group(2))
                        if m1.group(1) in lag_dict:
                            lag_dict[m1.group(1)] += int(m1.group(2))
                        else:
                            lag_dict[m1.group(1)] = int(m1.group(2))
            return lag_dict
        
        def create_event(msg_txt, consumer_group, metric_val, severity):
            payload = {"title":"Lag Threshold " + msg_txt, "text": consumer_group + ' ' + str(metric_val), "duration": 60000, "severity": severity}
            r = requests.post(event_url, json=payload)
        
        def generate_metric(metric_dict):
            res_str = ""
            with open("consumer_groups.txt","w") as f:
                for consumer_group in metric_dict.keys():
                    metric_name = "confluent_cons_consumer_lag_offsets{consumer_group="+consumer_group+"}  "
                    f.write(metric_name+"\n")
                    res_str +=  metric_name + str(metric_dict[consumer_group])+"\n"
                    if ( metric_dict[consumer_group] >= warning_threshold and metric_dict[consumer_group] < critical_threshold): 
                        create_event("Warning",consumer_group, metric_dict[consumer_group], 5)
                    elif  metric_dict[consumer_group] >= critical_threshold:   
                        create_event("Critical",consumer_group, metric_dict[consumer_group], 10)
            return res_str

        logging.info("refreshing..." )
        if dev_mode:
            print("using file")
            with open('confluentmetrics.txt', "r") as f:
                strary1 = list(map(remove_timestamp, f.readlines()))
        else: 
            buffer = BytesIO()
            c = pycurl.Curl()
            myurl = common_url 
            customheaders = ["Authorization:  {0}".format(token)]
            c.setopt(c.URL,myurl)
            c.setopt(c.USERPWD,token)
            c.setopt(c.CUSTOMREQUEST, "GET")
            c.setopt(c.WRITEDATA, buffer)
            c.setopt(c.CAINFO, certifi.where())
            try:
                c.perform()
                strary1 = list(map(remove_timestamp,buffer.getvalue().decode("utf-8").splitlines()))
            except:
                print(sys.exc_info())
                logging.CRITICAL(sys.exc_info())
            finally:
                c.close()
        logging.info("received response.")
        # retrieve the bytes, decode to UTF and convert to string array; then remove the timestamp and generate a new array
        # attach the new line characer to each response line to make lsit more human readable. Access the endpoint from any browser
        # to see the result
        ret_dict = process_lags(strary1)            

        strary2 = help_str + type_str + generate_metric(ret_dict) + generate(strary1)
        return app.response_class(strary2, mimetype='text') 

# start the app to serve responses to metrics requests
dev_mode = False
app = Flask(__name__)
#you can change the endpoint below
@app.route("/")
def get_metrics():
    return(retrieve_metrics(common_url,token))