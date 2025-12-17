#!/bin/bash

# Download the latest from https://k8slens.dev/
# On Ubuntu install with:
# sudo snap install <FILENAME>.snap --dangerous --classic

# auth
authenticate --to platform-staging-au

# download config
aws eks --region ap-southeast-2 update-kubeconfig --name platform-staging-au-01

# copy credentials
mv ~/.aws/credentials ~/.aws/credentials_$(date -u +'%Y-%m-%d-%H%M%S')
touch ~/.aws/credentials
AWS_SESSION_TOKEN=$(env | grep AWS_SESSION_TOKEN | cut -d "=" -f 2)
AWS_ACCESS_KEY_ID=$(env | grep -i aws_access_key_id | cut -d "=" -f 2)
AWS_SECRET_ACCESS_KEY=$(env | grep -i aws_secret_access_key | cut -d "=" -f 2)
echo "[default]" >> ~/.aws/credentials
echo "aws_session_token = $AWS_SESSION_TOKEN" >> ~/.aws/credentials
echo "aws_access_key_id = $AWS_ACCESS_KEY_ID" >> ~/.aws/credentials
echo "aws_secret_access_key = $AWS_SECRET_ACCESS_KEY" >> ~/.aws/credentials

lens
