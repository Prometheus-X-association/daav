#!/bin/sh
# Loads the sample indices (products: 50 documents, customers: 20 documents) into Elasticsearch.
# Existing indices are left untouched.
#
# Usage: ES_URL=http://localhost:9200 ES_USER=elastic ES_PASSWORD=<password> ./seed.sh
set -e
ES_URL="${ES_URL:-http://localhost:9200}"
ES_USER="${ES_USER:-elastic}"
DIR="$(dirname "$0")"

es() {
  curl -sS -u "$ES_USER:$ES_PASSWORD" "$@"
}

for index in products customers; do
  status=$(es -o /dev/null -w '%{http_code}' -I "$ES_URL/$index")
  if [ "$status" = "200" ]; then
    echo "$index already exists, skipped"
    continue
  fi
  es -f -X PUT "$ES_URL/$index" -H 'Content-Type: application/json' \
    -d '{"settings": {"number_of_replicas": 0}}' > /dev/null
  if es -f -X POST "$ES_URL/_bulk?refresh=true" -H 'Content-Type: application/x-ndjson' \
      --data-binary "@$DIR/$index.ndjson" | grep -q '"errors":false'; then
    echo "$index loaded"
  else
    echo "$index: some documents were rejected" >&2
    exit 1
  fi
done
