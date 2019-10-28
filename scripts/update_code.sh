#!/bin/bash

kubectl delete configmap code 2> /dev/null
kubectl create configmap code --from-file code
