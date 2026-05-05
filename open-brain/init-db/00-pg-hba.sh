#!/bin/bash
# Copy custom pg_hba.conf into the data directory, overriding the default.
# This runs before schema init because files are processed in alphabetical order.
cp /etc/postgresql/pg_hba_custom.conf /var/lib/postgresql/data/pg_hba.conf
echo "listen_addresses = '*'" >> /var/lib/postgresql/data/postgresql.conf
