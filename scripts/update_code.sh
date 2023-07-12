#!/bin/bash

LABEL=clic2023
kubectl delete configmap code-${LABEL} 2> /dev/null
kubectl create configmap code-${LABEL} --from-file code
