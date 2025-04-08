#!/bin/bash
# Configure PostgreSQL to listen on all interfaces
echo "listen_addresses = '*'" >> /var/lib/postgresql/data/postgresql.conf

# Update access permissions
echo "host    all             all             0.0.0.0/0               md5" >> /var/lib/postgresql/data/pg_hba.conf

# Reload configuration
pg_ctl reload -D /var/lib/postgresql/data