#!/usr/bin/env python

import optparse
import commands
#import httplib2
import json
import sys
import os
from string import Template
import time
import logging

TIMEOUT = 10 # set the default timeout for http request
log = logging.getLogger('serviceSync')

def getOpts():
    p = getOptparse()
    options, arguments = p.parse_args()

    return options, arguments

def getOptparse():
    p = optparse.OptionParser()
    p.add_option('-u', '--url', help='the rest url' )

    return p

# status, result
def runCommand( command ):
    return commands.getstatusoutput( command )

# status, result
# def requestHttp( url, method='GET' ):
#     h = httplib2.Http(cache="/tmp/.cache", timeout=TIMEOUT, disable_ssl_certificate_validation=True)
#     return h.request( url, method )

def getServiceData(serviceServe, serviceName ):

    command = "curl -s --cacert /etc/docker/acs-ca.pem --cert /etc/docker/service.pem --key /etc/docker/service-key.pem  https://"+serviceServe+"/services/"+serviceName
    print command
    status, result = runCommand( command )
    print status, result
    return json.loads(result)

def getUpstreamIps(serviceData):
    containers = serviceData.get("Containers")

    ips = []
    for k in containers.keys():
        if containers[k]["health"] == "success":
            # ip for contianer , node for node ip
            ips.append( containers[k]["ip"] )
    return ips

def getTemplate():
    return Template('''upstream tomcat {
      $upstreamServers
}

server {
listen       80;
server_name localhost;
index index.html index.htm index.php;
access_log  /var/log/nginx/access.log;
location / {
proxy_pass  http://tomcat;
}
}''')

# update nginx config
def updateConfig( config ):
    runCommand("cp /etc/nginx/conf.d/default.conf /etc/nginx/conf.d/default.conf.bk")
    # write to file and reload
    file_object = open('/etc/nginx/conf.d/default.conf', 'w')
    file_object.write( config )
    file_object.close( )

    # compare file
    status, result = runCommand("cmp /etc/nginx/conf.d/default.conf /etc/nginx/conf.d/default.conf.bk")
    print status, result
    if result != None and result !='':
        # reload nginx
        status, result = runCommand("service nginx reload")
        print status, result


def serviceSync():
    # read setting
    serviceServer = os.getenv('ETCD_NODES')
    projectName = os.getenv('COMPOSE_PROJECT_NAME')


    if serviceServer!=None:
        serviceServer = serviceServer.split(',')[0]
    else:
        log.error( " need to set ETCD_NODES" )
        sys.exit(0)

    port = os.getenv('SERVICE_PORT')
    if port ==None:
        port = '8080'

    #port = serviceData["Service"]["extensions"]["routing"]["port"]
    #port = serviceData["Service"]["definition"]["ports"][0]

    serviceName = os.getenv('SERVICE_NAME')
    if serviceName== None:
        if projectName!=None:
            serviceName = projectName +"_tomcat"
        else:
            log.error( "need to set SERVICE_NAME" )
            sys.exit(0)

    # get service data for contianers
    serviceData = getServiceData(serviceServer, serviceName )
    upStreamIPs = getUpstreamIps( serviceData )

    # generate config from template
    upstreamServers = ''
    for ip in upStreamIPs:
        # server tomcat_1:8080;
        upstreamServers += "server %s:%s;\n" % (ip, port)

    print upstreamServers

    config = getTemplate().substitute(upstreamServers=upstreamServers)
    print config

    updateConfig( config )

def main():
    options, arguments = getOpts()

    while True:
        serviceSync()
        time.sleep(60)

    sys.exit(0)

if __name__ == '__main__':
    main()