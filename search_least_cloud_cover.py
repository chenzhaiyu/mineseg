import os
import pdb
import xml.etree.ElementTree as ET
import shutil
from collections import defaultdict

# 98% written by ChatGPT


# Function to parse XML file and extract Cloud Coverage Assessment
def parse_xml(file_path):
    tree = ET.parse(file_path)
    root = tree.getroot()
    cloud_coverage = root.find('.//Cloud_Coverage_Assessment').text
    return cloud_coverage

# List to store results
results = defaultdict(list)

# Get the current directory
current_directory = os.getcwd()

# Traverse through all folders and subfolders
for foldername, subfolders, filenames in os.walk(current_directory):
    # Check if the file "MTD_MSIL1C.xml" exists in the current folder
    if 'MTD_MSIL1C.xml' in filenames:
        file_path = os.path.join(foldername, 'MTD_MSIL1C.xml')
        # Parse XML and extract Cloud Coverage Assessment
        cloud_coverage = float(parse_xml(file_path))
        # Extract granule ID from the folder name
        granule_id = foldername.split('_')[5]
        # Append filename, foldername, and cloud coverage to results list
        results[granule_id].append({'filename': 'MTD_MSIL1C.xml', 'foldername': foldername, 'cloud_coverage': cloud_coverage})

# Process results and save the filename with the least cloud coverage for each granule ID
least_cloud_coverage_files = []
for granule_id, granule_results in results.items():
    # Find the entry with the least cloud coverage
    entry_with_least_cloud_coverage = min(granule_results, key=lambda x: x['cloud_coverage'])
    least_cloud_coverage_files.append(entry_with_least_cloud_coverage)

# Create a subfolder named "selected"
selected_folder = os.path.join(current_directory, 'selected')
os.makedirs(selected_folder, exist_ok=True)

# Print the results
print("Files: ", len(least_cloud_coverage_files))

for result in least_cloud_coverage_files:
    source_folder = result['foldername']
    destination_folder = os.path.join(selected_folder, os.path.basename(source_folder))
    shutil.copytree(source_folder, destination_folder)
    print(f"Granule ID: {result['foldername'].split('_')[5]}, Foldername: {result['foldername']}, Cloud Coverage: {result['cloud_coverage']}")

