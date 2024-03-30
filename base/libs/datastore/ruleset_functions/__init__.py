import os

from krules_core.base_functions.processing import ProcessingFunction
from google.cloud import datastore

client = datastore.Client(
    database=os.environ.get("DATASTORE_DATABASE"), project=os.environ.get("DATASTORE_PROJECT_ID")
)


class DatastoreEntityStore(ProcessingFunction):
    def execute(self, kind: str, key: str, properties: dict, exclude_from_indexes: list = (), update = False):
        print(f"Storing {kind} entity with key {key} and properties {properties}")
        try:
            key = client.key(kind, key)
            if update:
                entity = client.get(key)
            else:
                entity = datastore.Entity(key, exclude_from_indexes=tuple(exclude_from_indexes))
            for prop_name, prop_value in properties.items():
                entity[prop_name] = prop_value
            client.put(entity)
        except Exception as e:
            print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
            print(e)
