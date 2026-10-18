#!/usr/bin/env bash
# SkillSight MySQL Database Initialization Helper
set -e

DB_NAME=${DB_NAME:-skillsight_db}
DB_USER=${DB_USER:-skillsight_user}
DB_PASS=${DB_PASS:-skillsight_pass}

echo "=== Initializing SkillSight MySQL Database ==="
echo "Database Name: $DB_NAME"
echo "Database User: $DB_USER"

mysql -u root -p -e "
CREATE DATABASE IF NOT EXISTS \`$DB_NAME\` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS '$DB_USER'@'localhost' IDENTIFIED BY '$DB_PASS';
GRANT ALL PRIVILEGES ON \`$DB_NAME\`.* TO '$DB_USER'@'localhost';
FLUSH PRIVILEGES;
"

echo "MySQL database '$DB_NAME' successfully initialized!"
echo "Update your .env file with:"
echo "DB_ENGINE=mysql"
echo "DB_NAME=$DB_NAME"
echo "DB_USER=$DB_USER"
echo "DB_PASSWORD=$DB_PASS"
echo "DB_HOST=127.0.0.1"
echo "DB_PORT=3306"
