#!/bin/bash
set -e

echo "Waiting for dependent services to start..."
sleep 10

echo "Checking Hive Metastore Schema status..."
export HIVE_CONF_DIR=/opt/hive/conf

if /opt/hive/bin/schematool -dbType postgres -info 2>&1 | grep -q "Metastore connection URL"; then
    if /opt/hive/bin/schematool -dbType postgres -info 2>&1 | grep -q "schemaTool completed"; then
        echo "Schema already exists, skipping initialization"
    else
        echo "Schema does not exist or is corrupted, starting initialization..."
        /opt/hive/bin/schematool -dbType postgres -initSchema || true
        echo "Schema initialization completed"
    fi
else
    echo "Schema does not exist, starting initialization..."
    /opt/hive/bin/schematool -dbType postgres -initSchema || true
    echo "Schema initialization completed"
fi

echo "Starting Metastore service..."
/opt/hive/bin/hive --service metastore
