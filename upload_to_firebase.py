import os
from dotenv import load_dotenv
from google.cloud import storage
from io import BytesIO

def upload_to_firebase(file_path, file_name, content_type):
    # Load environment variables
    load_dotenv()

    # Path to the credentials.json file
    cred_path = 'credentials.json'

    # Initialize Firebase Admin SDK with the credentials file
    cred = storage.Client.from_service_account_json(cred_path)
    bucket_name = os.getenv('FIREBASE_STORAGE_BUCKET')
    bucket = cred.get_bucket(bucket_name)
    blob = bucket.blob(file_name)

    # Upload the file from the given file path
    with open(file_path, 'rb') as file:
        blob.upload_from_file(file, content_type=content_type)

    # Make the blob publicly readable
    blob.make_public()

    # The public URL can be used to directly access the uploaded file via HTTP
    return blob.public_url

# Example usage
file_path = 'test.fif' # Replace with the path to the file you want to upload
file_name = 'fif/test12345.fif' # Replace with the destination path in Firebase Storage
content_type = 'application/octet-stream' # Replace with the appropriate content type for your file

url = upload_to_firebase(file_path, file_name, content_type)
print(f'File uploaded to: {url}')
