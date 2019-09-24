# 1. Select Google Cloud project

Create and select a Google Cloud project.

	gcloud config set project clic-215616

# 2. Build Docker images

Build all required Docker images:

	./scripts/build_images.sh

In the Google Cloud console, you can enable public access to the Docker images under
"Container Registry > Settings" so that participants can use them as well.

# 3. Create storage bucket and upload content

Create the following storage buckets:

	gsutil mb gs://clic2020_targets
	gsutil mb gs://clic2020_environments
	gsutil mb gs://clic2020_submissions

For each task and phase, create folders `<task>/<phase>/` and upload corresponding files into these
directories. The first bucket contains the target images, the second bucket contains any extra files
which will be provided to the decoders. The third bucket will be used to store submissions.

# 4. Create kubernetes cluster

Create a cluster which will run decoders and other servers:

	./scripts/create_cluster.sh

To later shut down the server, run:

	./scripts/delete_cluster.sh
