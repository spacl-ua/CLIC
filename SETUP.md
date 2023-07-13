> **Note**
> Before you launch any script, check them to see if you are happy with the
> settings or to see if they need to be updated.

# 0. Install Google Cloud SDK & Docker

Cloud SDK (Mac):

	curl https://sdk.cloud.google.com | bash

We will also need this plugin:

	gcloud components install gke-gcloud-auth-plugin

To install Docker, see https://docs.docker.com/get-docker, for example.

# 1. Select Google Cloud project

Select a Google Cloud project:

	gcloud config set project <project>

If you are creating a new project, make sure the necessary APIs are enabled.

# 2. Build Docker images

Before building Docker images, check that they are up to date. Especially these files:

	./cloudbuild.yaml
	./environments/decoding/Dockerfile

Build all required Docker images:

	./scripts/build_images.sh

In the Google Cloud console, you can enable public access to the Docker images under
"Container Registry > Settings" so that participants can use them as well.

# 3. Create storage bucket and upload content

Create the following storage buckets:

	gsutil mb gs://clic2023_targets
	gsutil mb gs://clic2023_environments
	gsutil mb gs://clic2023_submissions

For each task and phase, create folders `<task>/<phase>/` and upload corresponding files into these
directories. The first bucket contains the target images, the second bucket contains any extra files
which will be provided to the decoders. The third bucket will be used to store submissions.

# 4. Create MySQL server

> **Warning**
> Whenever you change the MySQL password, you will also need to update the corresponding secret
> in kubernetes so that the website continues to function.

Create a MySQL instance _if it does not already exist_:

	gcloud sql instances create clic --database-version=MYSQL_8_0

 Change the root password:

	gcloud sql users set-password root --instance clic --host % --password <password>

Create a database for this year's competition:

	gcloud sql databases create clic2023 --instance clic

### (Optional) Migrate data

	./scripts/start_local_sql_proxy.sh

	mysqldump --port 1234 -h 127.0.0.1 --user root -p clic2022 > clic2022.sql

	cat clic2022.sql | mysql --port 1234 -h 127.0.0.1 --user root -p clic2022


# 5. Create service account

	./scripts/create_service_account.sh


# 6. Create kubernetes cluster

Create a cluster _if it does not already exist_.

	./scripts/create_cluster.sh

If you later want to shut down the server, run:

	./scripts/delete_cluster.sh


# 7. Create secrets

Add secrets to kubernetes:

	./scripts/create_secrets.sh


# 6. Create SQL tables

Enter environment with code + DB proxy:

	./scripts/start_webserver_local.sh  -i

Create database tables:

	./manage.py migrate

Create an admin:

	./manage.py createsuperuser


# 7. Start webserver

Create a public storage bucket to host static content:

	gsutil mb gs://clic2022_public
	gsutil iam ch allUsers:objectViewer gs://clic2022_public

Start webserver:

	./scripts/restart_webserver.sh

This script will automatically upload static content and request a static IP address
for the server.

The same script can be used to restart the webserver if its configuration is changed.
Note that most changes to the webserver require rebuilding the Docker images first.

# 8. Debugging

If there is an issue with the website, it is often easier to debug it locally:

	./scripts/start_webserver_local.sh
