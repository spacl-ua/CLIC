import hashlib


def hash_uploaded_file(file):
	sha224 = hashlib.sha224()

	if file.multiple_chunks():
		for chunk in file.chunks(1024):
			sha224.update(chunk)
	else:
		sha224.update(file.read())
	return sha224.hexdigest()

