import google.auth
from google.cloud.container_v1 import ClusterManagerClient
from kubernetes import client


def get_kubernetes_client():
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

	# create client
	return client.BatchV1Api()
