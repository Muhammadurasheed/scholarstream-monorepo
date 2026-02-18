
import os
import shutil
import glob

files_to_delete = [
    r"c:\Users\HP\Documents\scholarstream-confluent\backend\verify_pipeline.py",
    r"c:\Users\HP\Documents\scholarstream-confluent\backend\test_streaming_scrapers.py",
    r"c:\Users\HP\Documents\scholarstream-confluent\backend\test_kafka_producer.py",
    r"c:\Users\HP\Documents\scholarstream-confluent\backend\test_kafka_connection.py",
    r"c:\Users\HP\Documents\scholarstream-confluent\backend\test_enriched_stream.py",
    r"c:\Users\HP\Documents\scholarstream-confluent\backend\scripts\test_chaos.py",
    r"c:\Users\HP\Documents\scholarstream-confluent\backend\kafka_to_cloud_function.py",
    r"c:\Users\HP\Documents\scholarstream-confluent\backend\debug_kafka.py",
    r"c:\Users\HP\Documents\scholarstream-confluent\backend\debug_consumer.py",
    r"c:\Users\HP\Documents\scholarstream-confluent\backend\create_topics.py"
]

dirs_to_delete = [
    r"c:\Users\HP\Documents\scholarstream-confluent\backend\scrapers",
    r"c:\Users\HP\Documents\scholarstream-confluent\backend\cloud_functions"
]

print("Starting cleanup...")

for f in files_to_delete:
    try:
        if os.path.exists(f):
            os.remove(f)
            print(f"Deleted file: {f}")
        else:
            print(f"File not found (already deleted?): {f}")
    except Exception as e:
        print(f"Error deleting file {f}: {e}")

for d in dirs_to_delete:
    try:
        if os.path.exists(d):
            shutil.rmtree(d)
            print(f"Deleted directory: {d}")
        else:
            print(f"Directory not found (already deleted?): {d}")
    except Exception as e:
        print(f"Error deleting directory {d}: {e}")

print("Cleanup script finished.")
