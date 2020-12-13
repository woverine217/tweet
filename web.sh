#!/bin/bash
cd terraform
terraform init
terraform apply

while true
do
  echo haha
  ps -fe |grep "terraform" |grep -v grep
  if [ $? -ne 0 ]
  then
  break
  fi
  sleep 120
done

aws eks --region $(terraform output region) update-kubeconfig --name $(terraform output cluster_name)
cd ..
cd kube
kubectl apply -f redis-deployment.yaml
kubectl apply -f service-redis.yaml
kubectl apply -f backend-deployment.yaml
kubectl apply -f service-backend.yaml
kubectl apply -f frontend-deployment.yaml
kubectl apply -f service-frontend-lb.yaml


#
#while
