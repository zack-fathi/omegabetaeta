import os
from pathlib import Path

uploads_path = 'sql/uploads'
sql_file_path = 'sql/insert_gallery.sql'

# Get all files
image_files = []
if os.path.isdir(uploads_path):
    for filename in sorted(os.listdir(uploads_path)):
        # Skip only .DS_Store
        if filename == '.DS_Store':
            continue
        
        image_files.append(filename)

# Generate SQL
with open(sql_file_path, 'w') as file:
    for filename in image_files:
        # Description is filename without extension
        desc = Path(filename).stem
        if desc == 'default':
            continue  # Skip default.jpg since it's not an actual gallery image
        
        # Create the SQL insert statement
        sql = (
            "INSERT INTO gallery(filename, desc) "
            f"VALUES('{filename}', '{desc}');\n"
        )
        
        file.write(sql)

print(f"Gallery SQL generated for {len(image_files)} images at {sql_file_path}")
for img in image_files:
    print(f"  - {img}")

