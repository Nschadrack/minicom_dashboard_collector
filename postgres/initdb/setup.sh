#!/bin/bash
# Allow all remote connections to the database
echo "host    all             all             0.0.0.0/0               md5" >> /var/lib/postgresql/data/pg_hba.conf
# Reload PostgreSQL configuration
pg_ctl reload -D /var/lib/postgresql/data