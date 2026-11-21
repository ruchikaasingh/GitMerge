-- Local development setup only. Run this in MySQL Workbench as an admin user.
CREATE DATABASE IF NOT EXISTS merge_resolver
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

CREATE USER IF NOT EXISTS 'merge_app'@'localhost'
  IDENTIFIED BY 'demo_password';

CREATE USER IF NOT EXISTS 'merge_app'@'127.0.0.1'
  IDENTIFIED BY 'demo_password';

GRANT ALL PRIVILEGES ON merge_resolver.* TO 'merge_app'@'localhost';
GRANT ALL PRIVILEGES ON merge_resolver.* TO 'merge_app'@'127.0.0.1';

FLUSH PRIVILEGES;
