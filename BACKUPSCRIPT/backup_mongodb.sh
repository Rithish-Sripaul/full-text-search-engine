#!/bin/bash
export PATH=/usr/bin:/bin:/usr/sbin:/sbin:/usr/local/bin

# Variables
CONTAINER_NAME="mongodb"
BACKUP_DIR="/data/backup"  # Directory inside the container
LOCAL_BACKUP_DIR="/Users/rithishsripaul/repos/dockerFlaskMongoDB/BACKUPSCRIPT/backup"
TIMESTAMP=$(date +"%Y%m%d%H%M%S")
BACKUP_NAME="mongodb_backup_$TIMESTAMP.gz"
USERNAME="adminNSTL"
PASSWORD="nstl1234"
AUTH_DB="admin"

# Ensure the backup directory exists inside the container
docker exec $CONTAINER_NAME mkdir -p $BACKUP_DIR

# Run the MongoDB dump command inside the container
docker exec $CONTAINER_NAME mongodump --username $USERNAME --password $PASSWORD --authenticationDatabase $AUTH_DB --archive --gzip > "$BACKUP_DIR/$BACKUP_NAME"

# Copy backup from container to local machine
docker cp $CONTAINER_NAME:$BACKUP_DIR/$BACKUP_NAME $LOCAL_BACKUP_DIR/

# Remove old backups (older than 7 days)
find $LOCAL_BACKUP_DIR -type f -mtime +7 -name "*.gz" -exec rm {} \;

echo "Backup completed: $LOCAL_BACKUP_DIR/$BACKUP_NAME"