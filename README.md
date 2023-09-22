# This is an example of scraping metrics from Confluent Cloud and injecting them into Instana


Confluent cloud has a well documented [metrics api](https://docs.confluent.io/cloud/current/monitoring/metrics-api.html), and already delivers metrics either in Openmetrics or JSON format. In this example, we use the OpenMetrics format. 

The example does three things:

Remove timestamp. The Confluent result has a timestamp attached to the metric, which causes some confusion with Instana. This code removes the timestamp and sends the Confluent result to the Instana backend. The current example uses Flask as the app mechanism and Gunicorn as the app server. Should be sufficient in most instances, particularly behind firewalls. If it is exposed to the Web, it needs a more robust mechanism such as gunicorn behind Nginx.

Reformat real numbers. Beware: Confluence returns very large numbers for some metrics, that causes issues with Instana. The code drops the exponent, and reduces the mantissa to an integer, sometimes quite large. Still good for trend analysis and anomaly detection, but not good if the expectation is to get the actual numbers. 

Consolidate the lags by consumer_group_id. After consolidating lags, it creates a new set of lag metrics for export to Instana. 

Create events using the Instana agent REST API. There is also an example in the code on how to create events directly in the Instana agent triggered by lags. 

The test system was a Linux VM running Python, Flask and Gunicorn and the Instana agent. Since the metric scraping only happens relatively infrequently as configured in the Instana configuration, this doesnt need much by way of infrastructure resources. **Be aware of API metering that Confluent does on their end**. 512MB of memory, 10-15GB of disk and 1-2 CPUs should be more than sufficient. No data is stored on disk. 

Refer Instana documenation for how to set this up on Kubernetes. 

Below is a section of the agent config file (ususally at `/opt/instana/agent/etc/instana`). Isolating the machine in its own zone may be a good idea!


    com.instana.plugin.prometheus:
        poll_rate: 30
        customMetricSources:
          - url: 'http://localhost:8000/'
          metricNameIncludeRegex: '.*'  
      

Set up the Python venv, install modules from requirements.txt, and run (this example creates 2 worker threads):

`gunicorn -w 2 'app:app'`

Once the flask app is running, the output metrics can be viewed at http://localhost:8000 with either a browser or CURL. 

The metrics will show up in the Instana backend, and you should be able to set up a custom dashboard to display then in a consumable format! 
