#!/bin/bash
export PATH=/usr/bin:/bin:/usr/sbin:/sbin:/usr/local/bin
env > /Users/rithishsripaul/repos/dockerFlaskMongoDB/BACKUPSCRIPT/backup/cron_env.log

# Variables
CONTAINER_NAME="mongodb"   # Replace with your MongoDB container name
BACKUP_DIR="/Users/rithishsripaul/repos/dockerFlaskMongoDB/BACKUPSCRIPT/backup"
TIMESTAMP=$(date +"%Y%m%d%H%M%S")    # Timestamp for backup naming
BACKUP_NAME="mongodb_backup_$TIMESTAMP.gz"
USERNAME="adminNSTL"                 # Your MongoDB username
PASSWORD="nstl1234"                  # Your MongoDB password
AUTH_DB="admin"                      # The authentication database (usually "admin" for MongoDB)

# Create backup directory if not exists
mkdir -p $BACKUP_DIR

# Run the MongoDB dump command with authentication
/usr/local/bin/docker exec $CONTAINER_NAME mongodump --username $USERNAME --password $PASSWORD --authenticationDatabase $AUTH_DB --archive --gzip > "$BACKUP_DIR/$BACKUP_NAME"

# Optional: Delete old backups (e.g., older than 7 days)
find $BACKUP_DIR -type f -mtime +7 -name "*.gz" -exec rm {} \;

echo "Backup completed: $BACKUP_DIR/$BACKUP_NAME"
