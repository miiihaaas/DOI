# Database Backup and Restore Procedures

This document outlines the database backup and restore procedures for the DOI Management Application.

## Overview

The application uses MySQL as its primary database and includes automated backup and restore capabilities through the `setup-database.sh` script.

## Quick Reference

```bash
# Create backup
./deployment/scripts/setup-database.sh backup

# Restore from backup
./deployment/scripts/setup-database.sh restore /path/to/backup.sql.gz

# Check database status
./deployment/scripts/setup-database.sh status

# Test database connection
./deployment/scripts/setup-database.sh test
```

## Backup Procedures

### Automated Backup

The database setup script provides automated backup functionality:

```bash
./deployment/scripts/setup-database.sh backup
```

This will:
1. Create a timestamped SQL dump file in the `backups/` directory
2. Compress the backup file with gzip
3. Include all tables, data, and schema definitions

### Backup File Naming

Backup files follow this naming convention:
```
doi_db_backup_YYYYMMDD_HHMMSS.sql.gz
```

Example: `doi_db_backup_20250819_143022.sql.gz`

### Manual Backup

For manual backups, you can use mysqldump directly:

```bash
# Load environment variables
source .env

# Extract database details (or use individual variables)
mysqldump -h $DB_HOST -P $DB_PORT -u $DB_USER -p$DB_PASSWORD $DB_NAME > backup.sql

# Compress the backup
gzip backup.sql
```

### Scheduled Backups

To set up automatic daily backups, add to crontab:

```bash
# Edit crontab
sudo crontab -e

# Add daily backup at 2 AM
0 2 * * * cd /opt/doi-app && ./deployment/scripts/setup-database.sh backup >> logs/backup.log 2>&1
```

### Backup Retention

The application automatically manages backup retention based on the `BACKUP_RETENTION_DAYS` environment variable (default: 30 days).

To manually clean up old backups:

```bash
# Remove backups older than 30 days
find backups/ -name "*.sql.gz" -mtime +30 -delete
```

## Restore Procedures

### Full Database Restore

**⚠️ WARNING: This will completely replace all data in the database!**

```bash
# Restore from compressed backup
./deployment/scripts/setup-database.sh restore backups/doi_db_backup_20250819_143022.sql.gz

# Restore from uncompressed backup
./deployment/scripts/setup-database.sh restore backups/backup.sql
```

The restore process will:
1. Confirm the operation (requires typing "yes")
2. Stop the application service
3. Restore the database from the backup file
4. Restart the application service

### Manual Restore

For manual restore operations:

```bash
# Load environment variables
source .env

# For compressed backups
zcat backups/backup.sql.gz | mysql -h $DB_HOST -P $DB_PORT -u $DB_USER -p$DB_PASSWORD $DB_NAME

# For uncompressed backups
mysql -h $DB_HOST -P $DB_PORT -u $DB_USER -p$DB_PASSWORD $DB_NAME < backups/backup.sql
```

### Selective Restore

To restore specific tables only:

```bash
# Extract specific tables from backup
zcat backup.sql.gz | sed -n '/DROP TABLE.*`table_name`/,/UNLOCK TABLES/p' | mysql -h $DB_HOST -u $DB_USER -p$DB_PASSWORD $DB_NAME
```

## Migration Management

### Running Migrations

```bash
# Run all pending migrations
./deployment/scripts/setup-database.sh migrate

# Or using Flask directly
cd /opt/doi-app
source venv/bin/activate
flask db upgrade
```

### Creating New Migrations

When models are updated:

```bash
cd /opt/doi-app
source venv/bin/activate
flask db migrate -m "Description of changes"
flask db upgrade
```

### Migration Rollback

```bash
# Rollback to previous migration
flask db downgrade

# Rollback to specific migration
flask db downgrade <revision_id>
```

## Database Status and Monitoring

### Check Database Status

```bash
./deployment/scripts/setup-database.sh status
```

This displays:
- Connection status
- Database size
- Number of tables  
- Migration count

### Test Connection

```bash
./deployment/scripts/setup-database.sh test
```

### Monitor Database Health

```bash
# Check MySQL service status
systemctl status mysql

# Check database processes
mysqladmin -u $DB_USER -p$DB_PASSWORD processlist

# Check database size
mysql -u $DB_USER -p$DB_PASSWORD -e "SELECT table_schema AS 'Database', ROUND(SUM(data_length + index_length) / 1024 / 1024, 1) AS 'DB Size in MB' FROM information_schema.tables WHERE table_schema='$DB_NAME' GROUP BY table_schema;"
```

## Disaster Recovery

### Complete System Recovery

1. **Install and configure MySQL server**
2. **Restore application files**
3. **Configure environment variables**
4. **Restore database from latest backup**
5. **Run any pending migrations**
6. **Restart services**

```bash
# Example recovery sequence
sudo mysql -u root -p -e "CREATE DATABASE doi_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
sudo mysql -u root -p -e "CREATE USER 'doi_user'@'localhost' IDENTIFIED BY 'password';"
sudo mysql -u root -p -e "GRANT ALL PRIVILEGES ON doi_db.* TO 'doi_user'@'localhost';"

# Restore from backup
./deployment/scripts/setup-database.sh restore /path/to/latest/backup.sql.gz

# Run migrations if needed
./deployment/scripts/setup-database.sh migrate

# Start services
sudo systemctl start doi-app nginx
```

### Point-in-Time Recovery

For point-in-time recovery, you need binary logging enabled in MySQL:

```sql
-- Enable binary logging in MySQL configuration
SET GLOBAL log_bin = ON;
SET GLOBAL expire_logs_days = 7;
```

Recovery process:
1. Restore from latest full backup
2. Apply binary logs from backup time to desired point

## Best Practices

### Backup Best Practices

1. **Regular Backups**: Schedule daily automated backups
2. **Test Backups**: Regularly test backup restoration on a separate system
3. **Multiple Locations**: Store backups in multiple locations (local + remote)
4. **Encryption**: Encrypt backups for sensitive data
5. **Monitoring**: Monitor backup success/failure
6. **Documentation**: Keep backup logs and documentation updated

### Security Considerations

1. **Access Control**: Restrict access to backup files
2. **Encryption**: Encrypt backup files containing sensitive data
3. **Network Security**: Use secure connections for remote backups
4. **Audit Trail**: Log all backup and restore operations

### Performance Considerations

1. **Backup Timing**: Schedule backups during low-usage periods
2. **Incremental Backups**: Consider incremental backups for large databases
3. **Compression**: Always compress backup files to save space
4. **I/O Impact**: Monitor disk I/O during backup operations

## Troubleshooting

### Common Issues

1. **Backup fails with permission denied**
   - Check file system permissions
   - Ensure backup directory exists and is writable
   - Verify MySQL user has necessary privileges

2. **Restore fails with foreign key constraints**
   - Disable foreign key checks during restore:
   ```sql
   SET FOREIGN_KEY_CHECKS = 0;
   -- Restore data
   SET FOREIGN_KEY_CHECKS = 1;
   ```

3. **Database connection timeout during backup**
   - Increase MySQL timeout settings
   - Use `--single-transaction` flag for consistent backups

4. **Out of disk space during backup**
   - Clean up old backups
   - Use streaming backup to remote location
   - Monitor disk space regularly

### Recovery Validation

After any restore operation:

1. **Check application functionality**
2. **Verify data integrity**
3. **Run database consistency checks**
4. **Test user authentication**
5. **Validate all critical workflows**

## Monitoring and Alerts

### Backup Monitoring

Set up monitoring for:
- Backup completion status
- Backup file size (detect incomplete backups)
- Backup file age (ensure recent backups exist)
- Disk space for backup storage

### Database Health Monitoring

Monitor:
- Database connection availability
- Query performance
- Disk space usage
- Error log entries
- Replication status (if applicable)

## Contact and Support

For database-related issues:
1. Check application logs: `tail -f logs/doi_app.log`
2. Check MySQL logs: `tail -f /var/log/mysql/error.log`
3. Check system resources: `df -h` and `free -m`
4. Review this documentation for standard procedures