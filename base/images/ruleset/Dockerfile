FROM python:3.11-bullseye

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

ENV VIRTUAL_ENV=/opt/venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

ADD ./app /app

WORKDIR /app
ENV PYTHONPATH /app

RUN pip install --no-cache-dir --upgrade keyrings.google-artifactregistry-auth \
    google-cloud-secret-manager python-dateutil uvicorn[standard]

RUN pip install --no-cache-dir \
    --extra-index-url https://europe-west4-python.pkg.dev/krules-dev-254113/krules-pre/simple \
    krules-core==0.12.6rc1 \
    krules-env==0.12.6rc1 \
    krules-subjects-storage-redis==0.12.6rc1 \
    krules-dispatcher-cloudevents==0.12.6rc1 \
    krules-dispatcher-cloudevents-pubsub==0.12.6rc1 \
    krules-fastapi-env==0.12.6rc1

RUN pip install --no-cache-dir --no-deps \
     --extra-index-url https://europe-west4-python.pkg.dev/krules-dev-254113/krules-pre/simple \
    krules-core==0.12.6rc2 \
    krules-dispatcher-cloudevents-pubsub==0.12.6rc11 \
    krules-fastapi-env==0.12.6rc2 \
    ;

# development libs
RUN pip install --no-cache-dir pysnooper ipython contexttimer


CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]