# 1. Select Google Cloud project

Create and select a Google Cloud project.

	gcloud config set project clic-215616

# 2. Build Docker images

Build all required Docker images:

	`./scripts/build_images.sh`

In the Google Cloud console, you can enable public access to the Docker images under
"Container Registry > Settings" so that participants can use them as well.

# 3. Create storage bucket and upload content

Create a storage bucket for target images:

	gsutil mb gs://clic2020_targets

For each task and phase, put corresponding images into the `<task>/<phase>/`. Create another
storage bucket for submissions:

	gsutil mb gs://clic2020_submissions

Create another storage bucket containing any extra files which will be made available to the
decoders during decoding:

	gsutil mb gs://clic2020_environments

 Upload the corresponding content into `<task>/<phase>/`.

# 4. Create kubernetes cluster

Create a cluster which will run decoders and other servers:

	./scripts/create_cluster.sh

To later shut down the server, run:

	./scripts/delete_cluster.sh
