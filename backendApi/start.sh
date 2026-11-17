#!/bin/sh
# Usage: ./start.sh [--with-mongo]
#   --with-mongo  Start the local MongoDB container "daav-mongo" (127.0.0.1:27017, no authentication) before the
#                 backend, creating it on first use. Its data is kept in the Docker volume "daav-mongo-data", or in
#                 the directory MONGO_DATA_DIR when it is set (needed when the Docker root dir is on a filesystem
#                 that does not support chown, such as NTFS). An existing container is started as it is.

MONGO_CONTAINER=daav-mongo
MONGO_IMAGE=mongo:7.0

usage() {
    sed -n '2,6p' "$0" | sed 's/^# \{0,1\}//'
}

start_mongo() {
    if ! command -v docker >/dev/null 2>&1; then
        echo "--with-mongo: docker is not installed" >&2
        exit 1
    fi
    docker=docker
    if ! docker info >/dev/null 2>&1; then
        docker="sudo docker"
    fi

    if [ -n "$($docker ps -aq --filter "name=^${MONGO_CONTAINER}\$")" ]; then
        echo "Starting the MongoDB container $MONGO_CONTAINER..."
        $docker start "$MONGO_CONTAINER" >/dev/null || exit 1
    elif [ -n "$MONGO_DATA_DIR" ]; then
        echo "Creating the MongoDB container $MONGO_CONTAINER (data in $MONGO_DATA_DIR)..."
        mkdir -p "$MONGO_DATA_DIR/db" "$MONGO_DATA_DIR/configdb" || exit 1
        $docker run -d --name "$MONGO_CONTAINER" -p 127.0.0.1:27017:27017 \
            -v "$MONGO_DATA_DIR/db:/data/db" -v "$MONGO_DATA_DIR/configdb:/data/configdb" \
            "$MONGO_IMAGE" >/dev/null || exit 1
    else
        echo "Creating the MongoDB container $MONGO_CONTAINER (data in the Docker volume daav-mongo-data)..."
        $docker run -d --name "$MONGO_CONTAINER" -p 127.0.0.1:27017:27017 \
            -v daav-mongo-data:/data/db "$MONGO_IMAGE" >/dev/null || exit 1
    fi

    echo "Waiting for MongoDB..."
    i=0
    until $docker exec "$MONGO_CONTAINER" mongosh --quiet --eval 'db.runCommand({ ping: 1 }).ok' >/dev/null 2>&1; do
        if [ "$($docker inspect -f '{{.State.Running}}' "$MONGO_CONTAINER")" != "true" ]; then
            echo "The MongoDB container $MONGO_CONTAINER stopped:" >&2
            $docker logs --tail 20 "$MONGO_CONTAINER" >&2
            exit 1
        fi
        i=$((i + 1))
        if [ "$i" -ge 30 ]; then
            echo "MongoDB is not ready after 30s, see: $docker logs $MONGO_CONTAINER" >&2
            exit 1
        fi
        sleep 1
    done
    echo "MongoDB ready !"
}

with_mongo=false
for arg in "$@"; do
    case "$arg" in
        --with-mongo) with_mongo=true ;;
        -h|--help) usage; exit 0 ;;
        *) echo "Unknown option: $arg" >&2; usage >&2; exit 1 ;;
    esac
done

if [ "$with_mongo" = true ]; then
    start_mongo
fi

echo "Checking if python virtual environment exists"
# check if env exists
if [ -f "./.venv/bin/activate" ]; then
    echo "Environment exists"
else
#   if not exists, create it
    echo "Environment doesn't exist"
    echo "Creating virtual environment..."
    python3 -m venv .venv
    echo "Virtual environment created !"
fi
# use the env
echo "Activating virtual environment..."
sh .venv/bin/activate
echo "Virtual environment activated !"

echo "Installing backend dependencies..."
.venv/bin/pip install -q -r requirements.txt
echo "Backend dependencies installed !"

echo "Starting backend..."

.venv/bin/uvicorn app.main:app
echo "Backend started !"
