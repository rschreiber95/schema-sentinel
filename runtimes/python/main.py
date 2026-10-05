import sys
import os
import importlib

# Ensure /generated/python is on module path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "generated", "python")))

def process_entity(raw_bytes: bytes, version: str):
    try:
        # Dynamically import module: e.g. "v1.entity_pb2" or "v2.entity_pb2"
        module = importlib.import_module(f"{version}.entity_pb2")
    except ModuleNotFoundError:
        raise ValueError(f"Unsupported schema version: {version}")

    # Instantiate and deserialize using generated class
    entity = module.Entity()
    entity.ParseFromString(raw_bytes)

    # Read common field values
    print(f"[Python ({version})] entity_id: {entity.entity_id}")
    print(f"[Python ({version})] name:      {entity.name}")
    
    # Read version-specific fields if available
    if version == "v2" and hasattr(entity, "description"):
        print(f"[Python ({version})] description: {entity.description}")

# Example Usage
if __name__ == "__main__":
    # Import v1 directly to create mock payload
    from v1 import entity_pb2 as v1_pb
    mock_v1 = v1_pb.Entity(entity_id="py_101", name="Sensor A")
    
    process_entity(mock_v1.SerializeToString(), version="v1")