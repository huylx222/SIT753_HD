#!/bin/bash
# Script to create GCP monitoring alert policies
# Usage: ./create-alerts.sh [PROJECT_ID] [NOTIFICATION_URL] [CLUSTER_NAME] [REGION]

set -e

# Check if required arguments are provided
if [ "$#" -lt 2 ]; then
    echo "Usage: $0 <gcp-project-id> <notification-webhook-url> [cluster-name] [region]"
    exit 1
fi

# Set variables from arguments
PROJECT_ID=$1
NOTIFICATION_URL=$2
CLUSTER_NAME=${3:-"cluster-1"}      # Default to cluster-1 if not provided
REGION=${4:-"us-central1"}          # Default to us-central1 if not provided

echo "Setting up alert policies for project: ${PROJECT_ID}"

# Create notification channel by replacing the webhook URL in the template
TEMP_NOTIFICATION_FILE="temp_notification_channel.json"
cp monitoring/alerts/notification-channel.json $TEMP_NOTIFICATION_FILE
sed -i "s|\${TEAMS_WEBHOOK}|${NOTIFICATION_URL}|g" $TEMP_NOTIFICATION_FILE

# Create notification channel and capture the ID
echo "Creating notification channel..."
NOTIFICATION_CHANNEL_ID=$(gcloud alpha monitoring channels create \
    --channel-content-from-file=$TEMP_NOTIFICATION_FILE \
    --format="value(name)" \
    --project=${PROJECT_ID})

echo "Created notification channel with ID: $NOTIFICATION_CHANNEL_ID"

# Create alert policies using the YAML files
echo "Creating CPU utilization alert policy..."
gcloud alpha monitoring policies create \
    --policy-from-file=monitoring/cpu-alert.yaml \
    --notification-channels=$NOTIFICATION_CHANNEL_ID \
    --project=${PROJECT_ID}

echo "Creating memory utilization alert policy..."
gcloud alpha monitoring policies create \
    --policy-from-file=monitoring/memory-alert.yaml \
    --notification-channels=$NOTIFICATION_CHANNEL_ID \
    --project=${PROJECT_ID}

echo "Creating container restart alert policy..."
gcloud alpha monitoring policies create \
    --policy-from-file=monitoring/restart-alert.yaml \
    --notification-channels=$NOTIFICATION_CHANNEL_ID \
    --project=${PROJECT_ID}

# Clean up temp file
rm $TEMP_NOTIFICATION_FILE

echo "All alert policies have been created successfully!"
echo "You can view your alert policies at:"
echo "https://console.cloud.google.com/monitoring/alerting?project=${PROJECT_ID}"