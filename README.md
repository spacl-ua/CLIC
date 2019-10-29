# 1. Select Google Cloud project

Select a Google Cloud project:

	gcloud config set project clic-215616

If you are creating a new project, make sure the necessary APIs are enabled.

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

# 4. Create MySQL server

Create a MySQL instance if it does not already exist:

	gcloud sql instances create clic --database-version=MYSQL_5_7

Change the root password:

	gcloud sql users set-password root --instance clic --host % --password <password>

Create a database for this year's competition:

	gcloud sql databases create clic2020 --instance clic

# 5. Create kubernetes cluster

Create a cluster which will run decoders and other servers:

	./scripts/create_cluster.sh

If you are using a new service account, make it sure it has the necessary roles. To later shut down
the server, run:

	./scripts/delete_cluster.sh

# 6. Start webserver

Create a public storage bucket to host static content:

	gsutil mb gs://clic2020_public
	gsutil iam ch allUsers:objectViewer gs://clic2020_public

Upload static files:

	./manage.py collectstatic
	gsutil -m rsync -R web/static/ gs://clic2020_public/static/

Start webserver:

	kubectl apply -f web/web.yaml
