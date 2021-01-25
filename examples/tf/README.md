Submit decoder.zip and data.zip to the "Image 150 (valid)" track using the Docker image "tensorflow/tensorflow:1.15.0-py3".

The server will run commands similar to the following:

	unzip decoder.zip
	docker run --rm -w "$(pwd)" -v "$(pwd)":"$(pwd)" tensorflow/tensorflow:1.15.0-py3 ./decode
