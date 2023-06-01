import pycurl
import certifi
from io import BytesIO
import sys
import logging
import re
from flask import Flask


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(threadName)-12.12s] [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

#These variables need to be changed per the actual requirement. better to put them in toml files, and to the environment
common_url = 'https://api.telemetry.confluent.cloud/v2/metrics/cloud/export?resource.kafka.id=lkc-8w2qyq'
token = '335YYPHRCLSMHQZD:u72RozOB7kSjW2KDr758PuB2ALopGLqM6Nq5Ri9YFt9G3aibPDYoxk5D3IQ1SHbz'

def retrieve_metrics(common_url, token):
        def remove_timestamp(s):
            # this function removes the timestamp at the end of confluent metrics that Instana does not like. 
            # all metrics begin with confluent, and have a fixed format that the re is matching for.  
            # The backend would not import metrics that has a real number format. That is why the code drops the decimal
            # and digits that succeed it. Pretty much always .0. 
            m = re.match(r"(^confluent\S*)(\s*\S*\s*)\d*$",s) 
            if m:
                s = m.group(1)+" "+m.group(2)[0:-3]
            return s
        
        def generate(strary):
         for s in strary:
            yield s + '\n'
        logging.info("refreshing..." )
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
        except:
            print(sys.exc_info())
            logging.CRITICAL(sys.exc_info())
        finally:
            c.close()
        logging.info("received response.")
        # retrieve the bytes, decode to UTF and convert to string array; then remove the timestamp and generate a new array
        strary1 = list(map(remove_timestamp,buffer.getvalue().decode("utf-8").splitlines()))
        # attach the new line characer to each response line to make it more human readable. Access the endpoint from any browser
        # to see the result
        return app.response_class(generate(strary1), mimetype='text')

# start the app to serve responses to mertics requests

app = Flask(__name__)
#you can change the endpoint below
@app.route("/")
def get_metrics():
    return(retrieve_metrics(common_url,token))