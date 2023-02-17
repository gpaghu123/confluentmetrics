import pycurl
import certifi
from io import BytesIO

buffer = BytesIO()
c = pycurl.Curl()
customheaders = ["Authorization: ZenApiKey YWRtaW46VWg2OGJKY0dKaXRoQlFsODdROWJwMVNXMGpaMGtmd2h0NFpWNnU0NQo="]
c.setopt(c.URL, "https://cpd-zen1.apps.dgsvt5.cp.fyre.ibm.com/icp4data-databases/dg-1672018833030580/zen1/clone_system/clone_engine/clone_table")
c.setopt(c.HTTPHEADER, customheaders)
c.setopt(c.SSL_VERIFYPEER, 0)
c.setopt(c.SSL_VERIFYHOST, 0)
c.setopt(c.CUSTOMREQUEST, "GET")
c.setopt(c.WRITEDATA, buffer)
c.setopt(c.CAINFO, certifi.where())
c.perform()
c.close()

body = buffer.getvalue()
# Body is a byte string.
# We have to know the encoding in order to print it to a text file
# such as standard output.
print(body.decode('iso-8859-1'))
