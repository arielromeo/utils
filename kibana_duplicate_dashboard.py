#!/bin/python3.8

import requests
import json
import uuid
import re
import argparse

SERVER_URL = 'localhost:9200'

parser = argparse.ArgumentParser()
parser.add_argument("-d", '--dashboard-id', help="Dashboard ID", required=True)
parser.add_argument("-sn", '--search-name', help="Search name", required=True)
parser.add_argument("-rn", '--replace-name', help="Replace name", required=True)
parser.add_argument("-sh", '--search-host', help="Search host", required=True)
parser.add_argument("-rh", '--replace-host', help="Replace host", required=True)
parser.add_argument('--dry-run', help="Don't upload new objects to kibana", action='store_true')

args = parser.parse_args()


def get_dashboard(id):
    visualizations = []
    dashboard = None
    params = {
        "objects": [
            {
                "type": "dashboard",
                "id": id
            }
        ],
        "includeReferencesDeep": True
    }
    r = requests.post(url="{SERVER_URL}/api/saved_objects/_export".format(SERVER_URL=SERVER_URL),
                      data=json.dumps(params),
                      headers={
                          'kbn-xsrf': 'true',
                          'Content-Type': 'application/json'
                      })
    if r.status_code == 200:
        for elem in r.text.split("\n"):
            obj = json.loads(elem)
            if 'type' in obj:
                if obj['type'] == 'visualization':
                    visualizations.append(obj)
                elif obj['type'] == 'dashboard':
                    dashboard = obj
    else:
        print(r.text)
        exit(1)

    if dashboard is None or len(visualizations) == 0:
        print("Dashboard or visualizations do not exist. Check your dashboardID")
        exit(1)

    return dashboard, visualizations


def create_new(search_name, replace_name, search_host, replace_host, dashboard, visualizations):
    reg = re.compile(search_name, re.IGNORECASE)
    dashboard['attributes']['title'] = reg.sub(replace_name, dashboard['attributes']['title'])
    dashboard['id'] = str(uuid.uuid1())

    for vis in visualizations:
        vis['attributes']['title'] = reg.sub(replace_name, vis['attributes']['title'])
        vis['attributes']['visState'] = reg.sub(replace_name, vis['attributes']['visState'])
        vis['attributes']['visState'] = vis['attributes']['visState'].replace(search_host, replace_host)
        vis['attributes']['kibanaSavedObjectMeta']['searchSourceJSON'] = vis['attributes']['kibanaSavedObjectMeta']['searchSourceJSON'].replace(search_host, replace_host)

        for ref in dashboard['references']:
            if ref['id'] == vis['id']:
                vis['id'] = str(uuid.uuid4())
                ref['id'] = vis['id']
                break


def import_objects(dashboards, visualizations):
    text = '\n'.join(json.dumps(vis) for vis in visualizations)
    text += '\n' + json.dumps(dashboards) + '\n'

    with open('/tmp/process.ndjson', 'w') as file:
        file.writelines(text)

    file = {'file': open('/tmp/process.ndjson', 'rb')}

    if not args.dry_run:
        r = requests.post(url="{SERVER_URL}/api/saved_objects/_import".format(SERVER_URL=SERVER_URL),
                          files=file,
                          headers={
                              'kbn-xsrf': 'true',
                          })

        if r.status_code == 200:
            print("All done")
        else:
            print(r.text)
            exit(1)
    else:
        print("File created but not uploaded: /tmp/process.ndjson")


dashboards, visualizations = get_dashboard(args.dashboard_id)
create_new(args.search_name, args.replace_name, args.search_host, args.replace_host, dashboards, visualizations)
import_objects(dashboards, visualizations)

