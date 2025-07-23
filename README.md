# SANDBOX Database Explorer & Search

A Streamlit app designed to run in Snowflake that provides an intuitive interface for exploring and searching data in the SANDBOX database with granular control over search scope.

## ✨ Key Features

- **🔄 Cascading Menus**: Auto-populating dropdowns for schema → table → column discovery
- **🎯 Flexible Search Filtering**: Two-level selection system for maximum control
- **🏗️ Granular Control**: Discover columns from many tables, then filter search to specific schemas/tables
- **⚡ Optimized Search**: Uses Snowflake's SEARCH function for better performance than CONTAINS
- **📊 Interactive Results**: View, filter, and download search results
- **🎨 Modern UI**: Clean, intuitive interface with real-time feedback

## 🚀 How It Works

### Two-Level Selection System

**1. Data Discovery Level (Sidebar)**
- Explore schemas, tables, and columns to understand your data structure
- Select broad sets of columns you might be interested in
- Use cascading menus to navigate the database hierarchy

**2. Search Execution Level (Main Area)**
- Filter down to specific schemas and tables you want to search
- Execute searches only in your filtered scope
- Maintain flexibility while controlling search performance

## 📋 Step-by-Step Usage

### Step 1: Discover Your Data (Sidebar)
1. **Select Schema(s)**: Choose schemas from SANDBOX to populate table options
2. **Select Table(s)**: Pick tables to populate column options  
3. **Select Column(s)**: Either:
   - ✅ Check "Select all columns" for all columns from selected tables
   - 🎯 Manually select specific columns from the dropdown

### Step 2: Filter Search Scope (Main Area)
4. **Schema Filter**: Choose which specific schemas to actually search in
5. **Table Filter**: Choose which specific tables to actually search in
6. **Verify Scope**: Review the search scope summary before executing

### Step 3: Execute Search
7. **Enter Search Term**: Type your search string
8. **Search**: Click the search button to find matches using Snowflake's SEARCH function
9. **Review Results**: View matches with schema/table context and download if needed

## 💡 Pro Tips

- **Broad Discovery, Narrow Search**: Select columns from 10 schemas, then search in just 2
- **Default Behavior**: Search filters default to all available schemas/tables for convenience
- **Performance**: Use filters to limit search scope for better performance on large datasets
- **Column Context**: Columns show their data types: `schema.table.column (VARCHAR)`

## 🛠️ Deployment Instructions

### Prerequisites
- Access to Snowflake account with SANDBOX database
- Permissions to create and run Streamlit apps
- Access to INFORMATION_SCHEMA in SANDBOX database

### Deploy to Snowflake

**Option A: Snowflake Web Interface**
1. Log into Snowflake → Navigate to **Streamlit**
2. Click **+ Streamlit App** → **Upload from Stage** or **Create from GitHub**
3. Upload: `streamlit_app.py` and `environment.yml`
4. Set **Main File**: `streamlit_app.py`
5. Configure warehouse and database settings → **Create**

**Option B: SQL Commands**
```sql
CREATE STREAMLIT SANDBOX_EXPLORER
ROOT_LOCATION = '@<your_stage_name>/sandbox_explorer'
MAIN_FILE = 'streamlit_app.py'
QUERY_WAREHOUSE = '<your_warehouse_name>';
```

### Required Permissions
```sql
-- Database and schema access
GRANT USAGE ON DATABASE SANDBOX TO ROLE <your_role>;
GRANT USAGE ON ALL SCHEMAS IN DATABASE SANDBOX TO ROLE <your_role>;

-- Information schema access
GRANT SELECT ON ALL TABLES IN SCHEMA SANDBOX.INFORMATION_SCHEMA TO ROLE <your_role>;

-- Data access for searching
GRANT SELECT ON ALL TABLES IN DATABASE SANDBOX TO ROLE <your_role>;
```

## 🔧 Technical Implementation

### Core Database Queries

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

**Search Execution:**
```sql
SELECT 
    '<schema>' as SCHEMA_NAME,
    '<table>' as TABLE_NAME,
    *
FROM SANDBOX.<schema>.<table>
WHERE SEARCH("<column1>", "<column2>", '<search_string>')
LIMIT 1000
```

### Performance Optimizations

- ⚡ **SEARCH vs CONTAINS**: Uses Snowflake's optimized SEARCH function
- 🎯 **Scope Limiting**: Search filters prevent unnecessary table scans
- 💾 **Smart Caching**: Session state prevents re-querying metadata
- 📊 **Result Limiting**: 1000 rows per table to manage performance
- 🛡️ **Error Handling**: Graceful handling with informative messages

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| **"No schemas found"** | Check SANDBOX database exists, verify INFORMATION_SCHEMA permissions |
| **"Error fetching tables/columns"** | Verify schema names, check SELECT permissions on INFORMATION_SCHEMA |
| **"Error performing search"** | Confirm SELECT permissions on target tables, verify data exists |
| **Performance Issues** | Use search filters to limit scope, check warehouse size |
| **Empty Results** | Verify search string format, check if data contains expected values |

## 📄 Files Structure

```
├── streamlit_app.py      # Main Streamlit application
├── environment.yml       # Conda environment dependencies  
└── README.md            # This documentation
```

## 🆘 Support

- **Snowflake Setup**: [Snowflake Documentation](https://docs.snowflake.com/)
- **Permissions**: Contact your Snowflake administrator
- **App Issues**: Check error messages and console logs
- **Feature Requests**: Review code comments for customization options 
