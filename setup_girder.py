#!/usr/bin/env python3
import json
import requests
import time
import os
import sys

params = {
    "login": "admin",
    "email": "root@dev.null",
    "firstName": "Material",
    "lastName": "Guy",
    "password": "arglebargle123",
    "admin": True,
}
headers = {"Content-Type": "application/json", "Accept": "application/json"}


def final_msg():
    print("-------------- You should be all set!! -------------")
    print("try going to https://girder.htmdec.org and log in with: ")
    print("  user : %s" % params["login"])
    print("  pass : %s" % params["password"])


api_url = "https://girder.htmdec.org/api/v1"

# Give girder time to start
while True:
    print("Waiting for Girder to start")
    r = requests.get(api_url)
    if r.status_code == 200:
        break
    time.sleep(2)

print("Creating admin user")
r = requests.post(api_url + "/user", params=params, headers=headers)
if r.status_code == 400:
    print("Admin user already exists. Database was not purged.")
    print("If that is OK:")
    final_msg()
    sys.exit()

# Store token for future requests
headers["Girder-Token"] = r.json()["authToken"]["token"]

print("Creating default assetstore")
r = requests.post(
    api_url + "/assetstore",
    headers=headers,
    params={
        "type": 0,
        "name": "Base",
        "root": "/volumes/base",
    },
)

print("Enabling plugins")
plugins = [
    "oauth",
    "gravatar",
    "jobs",
    "homepage",
    "worker",
    "globus_handler",
    "virtual_resources",
    "wt_data_manager",
    "wholetale",
    "wt_home_dir",
    "wt_versioning",
    "sem_viewer",
    "table_view",
    "item_previews",
]
r = requests.put(
    api_url + "/system/plugins",
    headers=headers,
    params={"plugins": json.dumps(plugins)},
)
r.raise_for_status()

print("Restarting girder to load plugins")
r = requests.put(api_url + "/system/restart", headers=headers)
r.raise_for_status()

# Give girder time to restart
while True:
    print("Waiting for Girder to restart")
    r = requests.get(
        api_url + "/oauth/provider",
        headers=headers,
        params={"redirect": "http://blah.com"},
    )
    if r.status_code == 200:
        break
    time.sleep(2)

print("Setting up Plugin")

settings = [
    {
        "key": "core.cors.allow_origin",
        "value": "https://dashboard.htmdec.org,http://localhost:4200,https://legacy.htmdec.org",
    },
    {
        "key": "core.cors.allow_headers",
        "value": (
            "Accept-Encoding, Authorization, Content-Disposition, Set-Cookie, "
            "Content-Type, Cookie, Girder-Authorization, Girder-Token, "
            "X-Requested-With, X-Forwarded-Server, X-Forwarded-For, "
            "X-Forwarded-Host, Remote-Addr, Cache-Control"
        ),
    },
    {"key": "core.cookie_domain", "value": ".htmdec.org"},
    {"key": "core.secure_cookie", "value": True},
    {"key": "worker.api_url", "value": "http://girder:8080/api/v1"},
    {"key": "worker.broker", "value": "redis://redis/"},
    {"key": "worker.backend", "value": "redis://redis/"},
    {"key": "oauth.globus_client_id", "value": os.environ.get("GLOBUS_CLIENT_ID")},
    {
        "key": "oauth.globus_client_secret",
        "value": os.environ.get("GLOBUS_CLIENT_SECRET"),
    },
    {"key": "oauth.orcid_client_id", "value": os.environ.get("ORCID_CLIENT_ID")},
    {
        "key": "oauth.orcid_client_secret",
        "value": os.environ.get("ORCID_CLIENT_SECRET"),
    },
    {"key": "oauth.providers_enabled", "value": ["globus"]},
    {"key": "dm.globus_gc_dir", "value": "/opt/globusconnectpersonal"},
    {
        "key": "wholetale.dataverse_extra_hosts",
        "value": ["dev2.dataverse.org", "demo.dataverse.org"],
    },
    {
        "key": "wholetale.zenodo_extra_hosts",
        "value": ["https://sandbox.zenodo.org/record/"]
    },
    {"key": "dm.private_storage_path", "value": "/volumes/ps"},
    {"key": "wthome.homedir_root", "value": "/volumes/homes"},
    {"key": "wthome.taledir_root", "value": "/volumes/workspaces"},
    {"key": "wtversioning.runs_root", "value": "/volumes/runs"},
    {"key": "wtversioning.versions_root", "value": "/volumes/versions"},
]

r = requests.put(
    api_url + "/system/setting", headers=headers, params={"list": json.dumps(settings)}
)
try:
    r.raise_for_status()
except requests.exceptions.HTTPError:
    if r.status_code >= 400 and r.status_code < 500:
        print(f"Request died with {r.status_code}: {r.reason}")
        print(f"Returned: {r.text}")
    raise

with open("dev_images.json", "r") as fp:
    images = json.load(fp)

for image in images:
    print(f"Creating {image['name']} image")
    image["config"] = json.dumps(image["config"])
    r = requests.post(api_url + "/image", headers=headers, params=image)
    r.raise_for_status()

print("Restarting girder to update WebDav roots")
r = requests.put(api_url + "/system/restart", headers=headers)
r.raise_for_status()
final_msg()
