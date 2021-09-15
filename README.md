# utils
A simple repo to organize my personal utility scripts.

## kibana_duplicate_dashboard.py:
Very simple script to copy kibana dashboards, replacing IDS, names and hosts in queries.

## Copying AWS SSM Parameters between accounts
Let's say you have SSM Parameters in us-west-2 and wants to copy all of them to eu-west-1. Just execute this command and it will do the work ;)

```
  aws --region us-west-2 ssm get-parameters-by-path  --recursive --with-decryption --path / | \
   jq -r '.Parameters[]' | \
   jq -r '"aws --region eu-west-1 ssm put-parameter --name " + .Name  + " --value \"" + .Value + "\" --type " +  .Type  + " --data-type " + .DataType + "\n"' |xargs -0 /bin/bash -c
```
