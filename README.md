# SANDBOX Database Explorer & Search

A Streamlit app designed to run in Snowflake that provides an intuitive interface for exploring and searching data in the SANDBOX database.

## Features

- **🔄 Cascading Menus**: Auto-populating dropdowns for schema → table → column selection
- **🎯 Multi-table Search**: Search across multiple tables and columns simultaneously  
- **⚡ Optimized Search**: Uses Snowflake's SEARCH function for better performance
- **📊 Interactive Results**: View and download search results
- **🎨 Modern UI**: Clean, intuitive interface with helpful guidance

## Deployment Instructions

### 1. Prerequisites
- Access to a Snowflake account with SANDBOX database
- Appropriate permissions to create and run Streamlit apps
- Access to the INFORMATION_SCHEMA in the SANDBOX database

### 2. Deploy to Snowflake

#### Option A: Using Snowflake Web Interface
1. Log into your Snowflake account
2. Navigate to **Streamlit** in the left sidebar
3. Click **+ Streamlit App**
4. Choose **Create from GitHub Repository** or **Upload from Stage**
5. Upload the following files:
   - `streamlit_app.py`
   - `environment.yml`
6. Set the **Main File** to `streamlit_app.py`
7. Choose appropriate warehouse and database settings
8. Click **Create**

#### Option B: Using SQL Commands
```sql
-- Create the Streamlit app
CREATE STREAMLIT SANDBOX_EXPLORER
ROOT_LOCATION = '@<your_stage_name>/sandbox_explorer'
MAIN_FILE = 'streamlit_app.py'
QUERY_WAREHOUSE = '<your_warehouse_name>';

-- Upload files to the stage first using PUT commands or Snowflake web interface
```

### 3. Required Permissions

Ensure your role has the following permissions:
```sql
-- Grant usage on SANDBOX database and its schemas
GRANT USAGE ON DATABASE SANDBOX TO ROLE <your_role>;
GRANT USAGE ON ALL SCHEMAS IN DATABASE SANDBOX TO ROLE <your_role>;

-- Grant select permissions on information schema
GRANT SELECT ON ALL TABLES IN SCHEMA SANDBOX.INFORMATION_SCHEMA TO ROLE <your_role>;

-- Grant select permissions on tables you want to search
GRANT SELECT ON ALL TABLES IN DATABASE SANDBOX TO ROLE <your_role>;
```

## How to Use

### Step 1: Select Schemas
- Choose one or more schemas from the SANDBOX database
- The app will automatically query `SANDBOX.INFORMATION_SCHEMA.SCHEMATA`

### Step 2: Select Tables  
- Pick specific tables from your selected schema(s)
- Tables are displayed as `schema.table` for clarity
- Multiple table selection is supported

### Step 3: Select Columns
- **Option A**: Check "Select all columns" to search across all columns in selected tables
- **Option B**: Manually select specific columns from the dropdown
- Columns are displayed with their data types: `schema.table.column (DATA_TYPE)`

### Step 4: Search
- Enter your search term in the text input
- Click the "🔍 Search" button
- Results will appear below with download option

## Technical Details

### Database Queries

The app uses these key queries:

**Schema Discovery:**
```sql
SELECT SCHEMA_NAME 
FROM SANDBOX.INFORMATION_SCHEMA.SCHEMATA 
WHERE SCHEMA_NAME NOT IN ('INFORMATION_SCHEMA')
ORDER BY SCHEMA_NAME
```

**Table Discovery:**
```sql
SELECT DISTINCT TABLE_SCHEMA, TABLE_NAME 
FROM SANDBOX.INFORMATION_SCHEMA.TABLES 
WHERE TABLE_SCHEMA IN ('<selected_schemas>')
AND TABLE_TYPE = 'BASE TABLE'
ORDER BY TABLE_SCHEMA, TABLE_NAME
```

**Column Discovery:**
```sql
SELECT TABLE_SCHEMA, TABLE_NAME, COLUMN_NAME, DATA_TYPE
FROM SANDBOX.INFORMATION_SCHEMA.COLUMNS 
WHERE (TABLE_SCHEMA = '<schema>' AND TABLE_NAME = '<table>')
ORDER BY TABLE_SCHEMA, TABLE_NAME, ORDINAL_POSITION
```

**Search Query:**
```sql
SELECT 
    '<schema>' as SCHEMA_NAME,
    '<table>' as TABLE_NAME,
    *
FROM SANDBOX.<schema>.<table>
WHERE SEARCH("<column1>", "<column2>", '<search_string>')
LIMIT 1000
```

### Performance Considerations

- **SEARCH Function**: Uses Snowflake's optimized SEARCH function instead of CONTAINS for better performance
- **Result Limiting**: Limits results to 1000 rows per table to prevent excessive data transfer
- **Efficient Caching**: Uses Streamlit session state to avoid re-querying metadata
- **Error Handling**: Graceful error handling with informative messages

### Limitations

- Search results are limited to 1000 rows per table
- Requires SELECT permissions on target tables
- SEARCH function behavior depends on Snowflake's text search capabilities
- Large result sets may impact performance

## Troubleshooting

### Common Issues

**"No schemas found"**
- Check if SANDBOX database exists
- Verify permissions on INFORMATION_SCHEMA
- Ensure proper role assignments

**"Error fetching tables/columns"**  
- Verify schema names are correct
- Check SELECT permissions on INFORMATION_SCHEMA tables
- Confirm table types (only BASE TABLEs are shown)

**"Error performing search"**
- Verify SELECT permissions on target tables
- Check if tables contain data
- Ensure search string doesn't contain SQL injection characters

**Performance Issues**
- Consider selecting fewer columns/tables
- Use more specific search terms
- Check warehouse size allocation

## Support

For issues related to:
- **Snowflake Setup**: Consult Snowflake documentation
- **Permissions**: Contact your Snowflake administrator  
- **App Functionality**: Review the code comments and error messages 
