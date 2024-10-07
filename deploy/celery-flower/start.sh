#!/usr/bin/env python3

import os
import sys
from google.cloud import secretmanager
from sh import celery, ErrorReturnCode
import signal

# Parse the secret path
secret_path = os.environ.get('CELERY_BROKER_SECRET_PATH')
if not secret_path:
    print("Error: CELERY_BROKER_SECRET_PATH environment variable is not set.")
    sys.exit(1)

project_id, secret_id, version_id = secret_path.split('/')[-5::2]

# Create the Secret Manager client
client = secretmanager.SecretManagerServiceClient()

# Build the resource name of the secret version
name = f"projects/{project_id}/secrets/{secret_id}/versions/{version_id}"

# Access the secret version
try:
    response = client.access_secret_version(request={"name": name})
    broker_url = response.payload.data.decode("UTF-8")
except Exception as e:
    print(f"Error accessing secret: {e}")
    sys.exit(1)

# Prepare Flower command
flower_cmd = celery.bake("--broker=" + broker_url, "flower", "--conf=/data/flowerconfig.py")

print("Starting Flower...")

def signal_handler(signum, frame):
    print(f"Received signal {signum}. Terminating Flower gracefully...")
    try:
        flower_cmd.terminate() # Terminate the celery process gracefully
    except:
        pass
    sys.exit(0) # Exit with a zero exit code

# Register signal handlers
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

try:
    # Run Flower
    for line in flower_cmd(*sys.argv[1:], _iter=True, _err_to_out=True):
        print(line.strip())

except ErrorReturnCode as e:
    print(f"Flower process exited with return code {e.exit_code}")
    print(e.stdout.decode())
    sys.exit(e.exit_code)

except Exception as e:
    print(f"Error running Flower: {e}")
    sys.exit(1)