import logging
import time
import google.auth
from google.cloud.container_v1 import ClusterManagerClient
from kubernetes import client
from kubernetes.client.rest import ApiException
from . import utils


class KubernetesClient():
	def __init__(self):
		credentials, project = google.auth.default(
			scopes=['https://www.googleapis.com/auth/cloud-platform',])

		# obtain bearer token
		credentials.refresh(google.auth.transport.requests.Request())

		# obtain cluster
		cluster_manager = ClusterManagerClient(credentials=credentials)
		cluster = cluster_manager.get_cluster(project, 'us-west1-b', 'clic-cluster')

		# configure client
		config = client.Configuration()
		config.host = f'https://{cluster.endpoint}:443'
		config.verify_ssl = False
		config.api_key = {"authorization": "Bearer " + credentials.token}
		config.username = credentials._service_account_email
		client.Configuration.set_default(config)

		self.core_v1_api = client.CoreV1Api()
		self.batch_v1_api = client.BatchV1Api()


	def list_pods(self, namespace='default', **kwargs):
		return self.core_v1_api.list_namespaced_pod(namespace, **kwargs).items


	def create_job(self, job, namespace='default', **kwargs):
		kwargs['body'] = job
		return self.batch_v1_api.create_namespaced_job(namespace, **kwargs)


	def delete_job(self, job, namespace='default', **kwargs):
		kwargs['namespace'] = namespace
		kwargs['propagation_policy'] = kwargs.get('propagation_policy', 'Background')
		kwargs['grace_period_seconds'] = kwargs.get('grace_period_seconds', 0)
		kwargs['name'] = job if isinstance(job, str) else job['metadata']['name']
		return self.batch_v1_api.delete_namespaced_job(**kwargs)


	def read_log(self, pod, namespace='default', **kwargs):
		kwargs['namespace'] = namespace
		kwargs['name'] = pod if isinstance(pod, str) else pod.metadata.name

		if isinstance(kwargs.get('container', None), (list, tuple)):
			# concatenate logs
			logs = []
			for container in kwargs.pop('container'):
				logs.append(self.read_log(pod, namespace, container=container))
			return '\n'.join(logs)

		return self.core_v1_api.read_namespaced_pod_log(**kwargs)


	def stream_log(self, pod, namespace='default', amt=1024, max_attempts=5, delay_attempt=2, **kwargs):
		kwargs['namespace'] = namespace
		kwargs['name'] = pod if isinstance(pod, str) else pod.metadata.name

		# stream logs
		kwargs['follow'] = True
		kwargs['_preload_content'] = False

		if isinstance(kwargs.get('container', None), (list, tuple)):
			# concatenate logs
			for container in kwargs.pop('container'):
				yield from self.stream_log(pod, namespace, amt, container=container)
			return

		for i in range(max_attempts):
			try:
				yield from self.core_v1_api.read_namespaced_pod_log(**kwargs).stream(amt=amt)
			except ApiException:
				if i < max_attempts - 1:
					yield utils.log_message(logging.INFO, 'Waiting for container to start')
					time.sleep(delay_attempt)
				else:
					yield utils.log_message(logging.ERROR, 'Unable to retrieve logs')
					raise
			else:
				break
