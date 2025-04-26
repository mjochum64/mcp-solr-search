#!/bin/bash

# Start the Solr container using Docker Compose
echo "Starting Solr container..."
docker-compose up -d

# Wait for Solr to fully start
echo "Waiting for Solr to start..."
while ! curl -s http://localhost:8983/solr/ > /dev/null; do
  echo "Solr is not yet available, waiting..."
  sleep 2
done

# Wait a bit more to make sure Solr is fully operational
sleep 5

# Make the sample data loader executable
chmod +x ./docker/solr/load_sample_data.py

# Load sample data
echo "Loading sample data into Solr..."
python ./docker/solr/load_sample_data.py

echo "Solr is ready for testing with sample data loaded!"
echo "Access Solr Admin UI at: http://localhost:8983/solr/"