# Sheets for ERPNext

Sheets is a powerful integration app that provides effortless synchronization between Google Sheets and ERPNext. It enables seamless data flow between your spreadsheets and your ERPNext instance, making data entry and management more accessible for non-technical users.

## Features

- **Bidirectional Sync**: Import data from Google Sheets to ERPNext DocTypes
- **Flexible Mapping**: Map different worksheets to different DocTypes
- **Scheduled Imports**: Set up automatic imports on customizable schedules
- **Multiple Import Strategies**: Support for Insert, Update, and Upsert operations
- **Secure Authentication**: Uses Google's service account authentication
- **Error Handling**: Comprehensive error logging and reporting
- **Incremental Updates**: Tracks the last imported row for efficient updates

## Installation

### Prerequisites

- ERPNext v14+
- A Google account with access to Google Sheets
- Google Cloud Platform account for API access

### Standard Installation

```bash
# On your ERPNext server
bench get-app https://github.com/Milanfils/sheets.git
bench --site your-site-name install-app sheets
bench --site your-site-name migrate
```

## Configuration

### Step 1: Set Up Google Sheets API Access

1. **Create a Google Cloud Project**:
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select an existing one
   - Enable the Google Sheets API

2. **Create a Service Account**:
   - Navigate to "IAM & Admin" > "Service Accounts"
   - Click "Create Service Account"
   - Enter a name and description
   - Grant the role "Project" > "Editor"
   - Click "Create and Continue", then "Done"

3. **Create a Key for the Service Account**:
   - Click on the service account you just created
   - Go to the "Keys" tab
   - Click "Add Key" > "Create new key"
   - Select "JSON" format
   - Click "Create" to download the key file

4. **Share Your Google Sheet**:
   - Open your Google Sheet
   - Click "Share" in the top-right corner
   - Add the service account email (ends with `@*.iam.gserviceaccount.com`)
   - Set permission to "Editor"
   - Uncheck "Notify people"
   - Click "Share"

### Step 2: Configure Sheets App in ERPNext

1. **Set Up Spreadsheet Settings**:
   - In ERPNext, search for "Spreadsheet Settings"
   - Click "New" if no settings exist
   - Upload your service account JSON key file
   - Save the settings

2. **Create a Spreadsheet Document**:
   - Search for "Spreadsheet"
   - Click "New"
   - Enter the full URL of your Google Sheet
   - Enter the name of the specific worksheet/tab
   - Select an import frequency
   - Save the document

3. **Configure DocType Worksheet Mapping**:
   - In the Spreadsheet document, go to "Worksheet IDs"
   - Click "Add Row"
   - Select the DocType to map to (e.g., Customer, Item)
   - Choose the import type (Insert, Update, Upsert)
   - Save the document

## Usage

### Setting Up Your Google Sheet

Your Google Sheet should have:
- Column headers that match or can be mapped to ERPNext DocType fields
- Clean, consistent data
- Each row representing one record

### Manual Imports

To manually trigger an import:
1. Open your Spreadsheet document
2. Click "Trigger Import"

### Automated Imports

The app will automatically sync data based on the frequency you set:
- Yearly
- Monthly
- Weekly
- Daily
- Hourly
- Frequently (based on scheduler interval)
- Custom (using cron expressions)

### Monitoring Imports

- Check import status in "Data Import" list
- Review error logs for failed imports
- Monitor the scheduler logs for background job status

## Troubleshooting

### Common Issues

1. **"Cannot match column with fields" Error**:
   - Ensure your column headers exactly match ERPNext field names, or
   - Create explicit mappings between your columns and ERPNext fields

2. **Authentication Errors**:
   - Verify your service account JSON is correctly uploaded
   - Ensure your Google Sheet is shared with the service account

3. **Import Not Running**:
   - Check scheduler is running: `bench --site your-site-name scheduler-status`
   - Verify import frequency settings

## Development and Customization

For developers looking to customize or extend the Sheets app:

1. **Key Files**:
   - `spreadsheet.py`: Core functionality for sheet interaction
   - `doctype_worksheet_mapping.py`: Handles data mapping
   - `overrides.py`: Custom extensions to ERPNext

2. **Development Workflow**:
   ```bash
   # Clone the repository
   git clone https://github.com/Milanfils/sheets.git
   cd sheets

   # Install in development mode
   bench --site your-dev-site install-app sheets
   ```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Credits

Developed and maintained by Adam Usman (admin@admantechnologies.com)

Originally forked from [gavindsouza/sheets](https://github.com/gavindsouza/sheets)


