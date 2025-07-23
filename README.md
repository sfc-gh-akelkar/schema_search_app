# Database Explorer & Search

A powerful Streamlit app designed to run in Snowflake that provides an intuitive interface for exploring and searching data across any accessible database with granular control over search scope and advanced performance optimizations.

## ✨ Key Features

- **🗃️ Multi-Database Support**: Choose from any accessible database in your Snowflake environment
- **🔄 Cascading Menus**: Auto-populating dropdowns for database → schema → table → column discovery
- **🎯 Flexible Search Filtering**: Two-level selection system for maximum control
- **⚡ Wildcard Search**: Intelligent wildcard syntax for searching all columns with optimal performance
- **🔗 Synchronized Controls**: Smart checkbox synchronization for intuitive user experience
- **📋 Table-Separated Results**: Results organized by table for clear data source identification
- **🏗️ Granular Control**: Discover columns from many tables, then filter search to specific schemas/tables
- **🎨 Modern UI**: Clean, intuitive interface with real-time feedback and dynamic content

## 🚀 How It Works

### Multi-Level Selection System

**1. Database Selection**
- Choose from any accessible database in your Snowflake environment
- Defaults to SANDBOX if available, otherwise uses the first accessible database
- Dynamic title updates to show selected database

**2. Data Discovery Level (Sidebar)**
- Explore schemas, tables, and columns to understand your data structure
- Select broad sets of columns you might be interested in
- Use cascading menus to navigate the database hierarchy
- Intelligent column filtering (only searchable data types: VARCHAR, VARIANT, ARRAY, TEXT, OBJECT)

**3. Search Execution Level (Main Area)**
- Filter down to specific schemas and tables you want to search
- Choose between specific column search or wildcard search
- Execute searches only in your filtered scope
- View results organized by individual tables

## 📋 Step-by-Step Usage

### Step 1: Select Database
1. **Choose Database**: Select from available databases in the dropdown

### Step 2: Discover Your Data (Sidebar)
2. **Select Schema(s)**: Choose schemas from selected database to populate table options
3. **Select Table(s)**: Pick tables to populate column options  
4. **Select Column(s)**: Choose specific columns from the dropdown
5. **Search Options**:
   - ✅ **"Select all columns from selected tables"**: Quick select all available columns
   - ⚡ **"Use wildcard search"**: Forces `table.*` syntax for optimal performance
   - 🔗 **Smart Sync**: Wildcard option automatically checks "select all columns"

### Step 3: Filter Search Scope (Main Area)
6. **Schema Filter**: Choose which specific schemas to actually search in
7. **Table Filter**: Choose which specific tables to actually search in
8. **Verify Scope**: Review the search scope summary before executing

### Step 4: Execute Search
9. **Enter Search Term**: Type your search string
10. **Search**: Click the search button to find matches using Snowflake's SEARCH function
11. **Review Results**: View matches organized by table with individual download options

## 🎯 Advanced Features

### Intelligent Wildcard Search
- **Auto-Activation**: Automatically switches to wildcard when >15 columns selected
- **Performance Mode**: Manual wildcard option for optimal searching
- **Smart Syntax**: Uses `table.*` instead of listing individual columns
- **User Feedback**: Clear indicators when wildcard search is active

### Synchronized Controls
- **Logical Pairing**: Wildcard search auto-checks "select all columns"
- **Intuitive UX**: Unchecking wildcard unchecks "select all columns"
- **Manual Override**: Independent control when wildcard is disabled

### Table-Organized Results
- **Individual Tables**: Each table's results displayed separately
- **Result Summary**: Total results across all tables
- **Dual Downloads**: 
  - Combined CSV with all results
  - Individual CSV per table
- **Dynamic Display**: Table height adjusts to content

## 💡 Pro Tips

- **Broad Discovery, Narrow Search**: Select columns from 10 schemas, then search in just 2
- **Wildcard Performance**: Use wildcard search for tables with many columns (>15)
- **Default Behavior**: Search filters default to all available schemas/tables for convenience
- **Column Context**: Columns show their data types: `schema.table.column (VARCHAR)`
- **Smart Filtering**: Only searchable column types are shown (VARCHAR, VARIANT, etc.)

## 🛠️ Deployment Instructions

### Prerequisites
- Access to Snowflake account with target databases
- Permissions to create and run Streamlit apps
- Access to INFORMATION_SCHEMA in target databases

### Deploy to Snowflake

**Option A: Snowflake Web Interface**
1. Log into Snowflake → Navigate to **Streamlit**
2. Click **+ Streamlit App** → **Upload from Stage** or **Create from GitHub**
3. Upload: `streamlit_app.py` and `environment.yml`
4. Set **Main File**: `streamlit_app.py`
5. Configure warehouse and database settings → **Create**

**Option B: SQL Commands**
```sql
CREATE STREAMLIT DATABASE_EXPLORER
ROOT_LOCATION = '@<your_stage_name>/database_explorer'
MAIN_FILE = 'streamlit_app.py'
QUERY_WAREHOUSE = '<your_warehouse_name>';
```

### Required Permissions
```sql
-- Database access for multiple databases
GRANT USAGE ON DATABASE <database_name> TO ROLE <your_role>;
GRANT USAGE ON ALL SCHEMAS IN DATABASE <database_name> TO ROLE <your_role>;

-- Information schema access
GRANT SELECT ON ALL TABLES IN SCHEMA <database_name>.INFORMATION_SCHEMA TO ROLE <your_role>;

-- Data access for searching
GRANT SELECT ON ALL TABLES IN DATABASE <database_name> TO ROLE <your_role>;

-- Show databases permission
GRANT USAGE ON WAREHOUSE <warehouse_name> TO ROLE <your_role>;
```

## 🔧 Technical Implementation

### Core Database Queries

**Database Discovery:**
```sql
SHOW DATABASES
```

**Schema Discovery:**
```sql
SELECT SCHEMA_NAME 
FROM {database}.INFORMATION_SCHEMA.SCHEMATA 
WHERE SCHEMA_NAME NOT IN ('INFORMATION_SCHEMA')
ORDER BY SCHEMA_NAME
```

**Table Discovery:**
```sql
SELECT DISTINCT TABLE_SCHEMA, TABLE_NAME 
FROM {database}.INFORMATION_SCHEMA.TABLES 
WHERE TABLE_SCHEMA IN ('<selected_schemas>')
AND TABLE_TYPE = 'BASE TABLE'
ORDER BY TABLE_SCHEMA, TABLE_NAME
```

**Column Discovery (Optimized):**
```sql
SELECT TABLE_SCHEMA, TABLE_NAME, COLUMN_NAME, DATA_TYPE
FROM {database}.INFORMATION_SCHEMA.COLUMNS 
WHERE (TABLE_SCHEMA = '<schema>' AND TABLE_NAME = '<table>')
AND DATA_TYPE IN ('VARCHAR', 'VARIANT', 'ARRAY', 'TEXT', 'OBJECT')
ORDER BY TABLE_SCHEMA, TABLE_NAME, ORDINAL_POSITION
```

**Search Execution (Specific Columns):**
```sql
SELECT 
    '<schema>' as SCHEMA_NAME,
    '<table>' as TABLE_NAME,
    *
FROM {database}.<schema>.<table>
WHERE SEARCH((column1, column2), '<search_string>')
LIMIT 1000
```

**Search Execution (Wildcard):**
```sql
SELECT 
    '<schema>' as SCHEMA_NAME,
    '<table>' as TABLE_NAME,
    *
FROM {database}.<schema>.<table>
WHERE SEARCH((<table>.*), '<search_string>')
LIMIT 1000
```

### Performance Optimizations

- ⚡ **SEARCH vs CONTAINS**: Uses Snowflake's optimized SEARCH function
- 🎯 **Scope Limiting**: Search filters prevent unnecessary table scans
- 💾 **Smart Caching**: Session state prevents re-querying metadata
- 🔄 **Wildcard Intelligence**: Auto-switches to wildcard for performance
- 📊 **Result Limiting**: 1000 rows per table to manage performance
- 🛡️ **Error Handling**: Graceful handling with informative messages
- 🎛️ **Column Filtering**: Only includes searchable data types
- 📋 **Table Separation**: Organized results for better performance and clarity

### User Interface Enhancements

- **Dynamic Titles**: Database name appears in page title
- **Smart Defaults**: Intelligent default selections
- **Real-time Feedback**: Immediate updates and clear status messages
- **Responsive Design**: Adapts to different screen sizes
- **Intuitive Flow**: Logical progression through selection steps

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| **"No databases found"** | Check SHOW DATABASES permissions, verify warehouse access |
| **"No schemas found"** | Check database exists, verify INFORMATION_SCHEMA permissions |
| **"Error fetching tables/columns"** | Verify schema names, check SELECT permissions on INFORMATION_SCHEMA |
| **"Error performing search"** | Confirm SELECT permissions on target tables, verify data exists |
| **Performance Issues** | Use wildcard search, limit search scope with filters |
| **Empty Results** | Verify search string format, check if data contains expected values |
| **Checkbox Issues** | Refresh page if synchronization seems stuck |

## 📊 Results Features

### Table-Separated Display
- Each table's results shown individually
- Clear table headers with schema.table format
- Record count per table
- Dynamic table height based on content

### Download Options
- **Combined Download**: All results in single CSV
- **Individual Downloads**: Separate CSV per table
- **Timestamped Files**: Automatic timestamp in filenames
- **Clean Formatting**: Proper CSV structure for external tools

## 📄 Files Structure

```
├── streamlit_app.py      # Main Streamlit application
├── environment.yml       # Conda environment dependencies  
└── README.md            # This documentation
```

## 🔄 Recent Updates

- ✅ Multi-database support with dynamic selection
- ✅ Wildcard search with performance optimization
- ✅ Synchronized checkbox controls
- ✅ Table-separated results display
- ✅ Optimized column filtering for searchable types
- ✅ Enhanced error handling and user feedback
- ✅ Individual table download options

## 🆘 Support

- **Snowflake Setup**: [Snowflake Documentation](https://docs.snowflake.com/)
- **Streamlit Apps**: [Snowflake Streamlit Guide](https://docs.snowflake.com/en/developer-guide/streamlit)
- **Permissions**: Contact your Snowflake administrator
- **App Issues**: Check error messages and console logs
- **Feature Requests**: Review code comments for customization options

---

💡 **Pro Tip**: Start with wildcard search on a small table to test functionality, then expand to larger datasets as needed! 
