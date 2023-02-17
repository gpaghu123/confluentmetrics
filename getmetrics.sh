token=`echo "admin:Uh68bJcGJithBQl87Q9bp1SW0jZ0kfwht4ZV6u45" | base64`
urlOltpTables="https://cpd-zen1.apps.dgsvt5.cp.fyre.ibm.com/icp4data-databases/dg-1672018833030580/zen1/clone_system/clone_engine/clone_table"
curl --libcurl out.c -k -X GET -H "Authorization: ZenApiKey $token" $urlOltpTables | jq .
urlOltpInstance="https://cpd-zen1.apps.dgsvt5.cp.fyre.ibm.com/icp4data-databases/dg-1672018833030580/zen1/clone_system/clone_engine/status?force_refresh=true"
curl -k -X GET -H "Authorization: ZenApiKey $token" -H "Content-Type: application/json" $urlOltpInstance | jq .
