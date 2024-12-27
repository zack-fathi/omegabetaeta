import shutil
from datetime import datetime

# Define source and destination paths
source_file = "/home/ec2-user/omegabetaeta/var/obhapp.sqlite3"
backup_dir = "/home/ec2-user/omegabetaeta/backups/"

# Ensure the backup directory exists
import os
os.makedirs(backup_dir, exist_ok=True)

# Generate a backup file name with a timestamp
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
destination_file = os.path.join(backup_dir, f"obhapp_backup_{timestamp}.sqlite3")

# Perform the copy
shutil.copy2(source_file, destination_file)
print(f"Backup created: {destination_file}")
