import streamlit as st
import pandas as pd
from snowflake.snowpark.context import get_active_session

# Get the active Snowflake session
session = get_active_session()

# Set page configuration
st.set_page_config(
    page_title="Database Explorer & Search",
    page_icon="🔍",
    layout="wide"
)

# Initialize session state
if 'selected_database' not in st.session_state:
    st.session_state.selected_database = None
if 'selected_schemas' not in st.session_state:
    st.session_state.selected_schemas = []
if 'selected_tables' not in st.session_state:
    st.session_state.selected_tables = []
if 'selected_columns' not in st.session_state:
    st.session_state.selected_columns = []
if 'available_schemas' not in st.session_state:
    st.session_state.available_schemas = []
if 'available_tables' not in st.session_state:
    st.session_state.available_tables = []
if 'available_columns' not in st.session_state:
    st.session_state.available_columns = []

def get_databases():
    """Get all databases accessible to the user"""
    try:
        query = "SHOW DATABASES"
        result = session.sql(query).collect()
        return [row['name'] for row in result]
    except Exception as e:
        st.error(f"Error fetching databases: {str(e)}")
        return []

def get_schemas(database):
    """Get all schemas from selected database"""
    if not database:
        return []
    
    try:
        query = f"""
        SELECT SCHEMA_NAME 
        FROM {database}.INFORMATION_SCHEMA.SCHEMATA 
        WHERE SCHEMA_NAME NOT IN ('INFORMATION_SCHEMA')
        ORDER BY SCHEMA_NAME
        """
        result = session.sql(query).collect()
        return [row['SCHEMA_NAME'] for row in result]
    except Exception as e:
        st.error(f"Error fetching schemas from {database}: {str(e)}")
        return []

def get_tables(database, schemas):
    """Get all tables from selected schemas"""
    if not database or not schemas:
        return []
    
    try:
        schema_list = "', '".join(schemas)
        query = f"""
        SELECT DISTINCT TABLE_SCHEMA, TABLE_NAME 
        FROM {database}.INFORMATION_SCHEMA.TABLES 
        WHERE TABLE_SCHEMA IN ('{schema_list}')
        AND TABLE_TYPE = 'BASE TABLE'
        ORDER BY TABLE_SCHEMA, TABLE_NAME
        """
        result = session.sql(query).collect()
        return [(row['TABLE_SCHEMA'], row['TABLE_NAME']) for row in result]
    except Exception as e:
        st.error(f"Error fetching tables from {database}: {str(e)}")
        return []

def get_columns(database, tables):
    """Get all columns from selected tables"""
    if not database or not tables:
        return []
    
    try:
        table_conditions = []
        for schema, table in tables:
            table_conditions.append(f"(TABLE_SCHEMA = '{schema}' AND TABLE_NAME = '{table}')")
        
        where_clause = " OR ".join(table_conditions)
        
        query = f"""
        SELECT TABLE_SCHEMA, TABLE_NAME, COLUMN_NAME, DATA_TYPE
        FROM {database}.INFORMATION_SCHEMA.COLUMNS 
        WHERE ({where_clause})
        AND data_type in ('VARCHAR', 'VARIANT', 'ARRAY', 'TEXT', 'OBJECT') 
        ORDER BY TABLE_SCHEMA, TABLE_NAME, ORDINAL_POSITION
        """
        result = session.sql(query).collect()
        return [(row['TABLE_SCHEMA'], row['TABLE_NAME'], row['COLUMN_NAME'], row['DATA_TYPE']) for row in result]
    except Exception as e:
        st.error(f"Error fetching columns from {database}: {str(e)}")
        return []

def perform_search(database, search_string, selected_columns, selected_tables, force_wildcard=False):
    """Perform search using Snowflake SEARCH function, returns results grouped by table"""
    if not database or not search_string.strip() or not selected_columns:
        return {}
    
    try:
        # Group columns by table
        tables_columns = {}
        for schema, table, column, data_type in selected_columns:
            table_key = f"{schema}.{table}"
            if table_key not in tables_columns:
                tables_columns[table_key] = []
            tables_columns[table_key].append(column)
        
        table_results = {}
        
        for table_key, columns in tables_columns.items():
            schema, table = table_key.split('.')
            
            # Use wildcard syntax if forced, or if there are many columns (> 15) to improve performance 
            # and avoid "too many columns" errors
            if force_wildcard or len(columns) > 15:
                search_clause = f"{table}.*"
                if force_wildcard:
                    st.info(f"🔍 Using wildcard search for {table_key} (user selected wildcard option)")
                else:
                    st.info(f"🔍 Using wildcard search for {table_key} ({len(columns)} columns) - this searches all columns in the table")
            else:
                # Create column list for SEARCH function for specific columns
                column_list = ', '.join([f'{col}' for col in columns])
                search_clause = column_list
            
            # Build the search query
            search_query = f"""
            SELECT 
                '{schema}' as SCHEMA_NAME,
                '{table}' as TABLE_NAME,
                *
            FROM {database}.{schema}.{table}
            WHERE SEARCH(({search_clause}), '{search_string}')
            LIMIT 1000
            """
            
            try:
                result = session.sql(search_query).collect()
                if result:
                    df = pd.DataFrame([row.asDict() for row in result])
                    table_results[table_key] = df
            except Exception as table_error:
                st.warning(f"Error searching in {table_key}: {str(table_error)}")
                continue
        
        return table_results
            
    except Exception as e:
        st.error(f"Error performing search: {str(e)}")
        return {}

# Sidebar for selections
st.sidebar.header("📋 Database Selection")

# Database selection
st.sidebar.subheader("1. Select Database")
available_databases = get_databases()

if available_databases:
    # Set default to SANDBOX if available, otherwise first database
    default_db = "SANDBOX" if "SANDBOX" in available_databases else available_databases[0]
    if st.session_state.selected_database is None:
        st.session_state.selected_database = default_db
    
    selected_database = st.sidebar.selectbox(
        "Choose a database:",
        available_databases,
        index=available_databases.index(st.session_state.selected_database) if st.session_state.selected_database in available_databases else 0,
        key="database_selectbox"
    )
    
    # Update session state and reset dependent selections when database changes
    if selected_database != st.session_state.selected_database:
        st.session_state.selected_database = selected_database
        st.session_state.available_schemas = []
        st.session_state.selected_schemas = []
        st.session_state.available_tables = []
        st.session_state.selected_tables = []
        st.session_state.available_columns = []
        st.session_state.selected_columns = []
        st.rerun()
else:
    st.sidebar.error("No databases found or accessible")
    selected_database = None

# Dynamic main title based on selected database
if selected_database:
    st.title(f"🔍 {selected_database} Database Explorer & Search")
else:
    st.title("🔍 Database Explorer & Search")
st.markdown("---")

# Schema selection
st.sidebar.subheader("2. Select Schema(s)")
if selected_database:
    if not st.session_state.available_schemas:
        st.session_state.available_schemas = get_schemas(selected_database)
    
    if st.session_state.available_schemas:
        selected_schemas = st.sidebar.multiselect(
            f"Choose schemas from {selected_database} database:",
            st.session_state.available_schemas,
            default=st.session_state.selected_schemas,
            key="schema_multiselect"
        )
        
        # Update session state and fetch tables when schemas change
        if selected_schemas != st.session_state.selected_schemas:
            st.session_state.selected_schemas = selected_schemas
            st.session_state.available_tables = get_tables(selected_database, selected_schemas)
            st.session_state.selected_tables = []
            st.session_state.available_columns = []
            st.session_state.selected_columns = []
            st.rerun()
    else:
        st.sidebar.error(f"No schemas found in {selected_database} database")
        selected_schemas = []
else:
    st.sidebar.info("Please select a database first")
    selected_schemas = []

# Table selection
st.sidebar.subheader("3. Select Table(s)")
if selected_database and selected_schemas:
    if not st.session_state.available_tables:
        st.session_state.available_tables = get_tables(selected_database, selected_schemas)
    
    if st.session_state.available_tables:
        # Create display names for tables (schema.table)
        table_display_names = [f"{schema}.{table}" for schema, table in st.session_state.available_tables]
        
        selected_table_displays = st.sidebar.multiselect(
            "Choose tables:",
            table_display_names,
            key="table_multiselect"
        )
        
        # Convert back to tuple format
        selected_tables = []
        for display_name in selected_table_displays:
            schema, table = display_name.split('.')
            selected_tables.append((schema, table))
        
        # Update session state and fetch columns when tables change
        if selected_tables != st.session_state.selected_tables:
            st.session_state.selected_tables = selected_tables
            st.session_state.available_columns = get_columns(selected_database, selected_tables)
            st.session_state.selected_columns = []
            st.rerun()
    else:
        st.sidebar.info("No tables found in selected schema(s)")
        selected_tables = []
elif selected_database and not selected_schemas:
    st.sidebar.info("Please select schema(s) first")
    selected_tables = []
else:
    st.sidebar.info("Please select database and schema(s) first")
    selected_tables = []

# Column selection
st.sidebar.subheader("4. Select Column(s)")

# Initialize force_wildcard with default value
force_wildcard = False

if selected_database and selected_tables:
    if not st.session_state.available_columns:
        st.session_state.available_columns = get_columns(selected_database, selected_tables)
    
    if st.session_state.available_columns:
        # Initialize session state for checkbox synchronization
        if 'prev_force_wildcard' not in st.session_state:
            st.session_state.prev_force_wildcard = False
        if 'prev_select_all_columns' not in st.session_state:
            st.session_state.prev_select_all_columns = False
        
        # Option to force wildcard search for better performance
        force_wildcard = st.sidebar.checkbox(
            "Use wildcard search (search all columns in each table)", 
            help="Forces wildcard search (table.*) for better performance, especially with many columns",
            value=st.session_state.prev_force_wildcard
        )
        
        # Synchronize select_all_columns with force_wildcard
        if force_wildcard != st.session_state.prev_force_wildcard:
            # Wildcard checkbox changed
            if force_wildcard:
                # Wildcard was just checked, so check select_all_columns too
                select_all_columns_value = True
            else:
                # Wildcard was just unchecked, so uncheck select_all_columns too
                select_all_columns_value = False
            st.session_state.prev_force_wildcard = force_wildcard
        else:
            # Use the previous value of select_all_columns
            select_all_columns_value = st.session_state.prev_select_all_columns
        
        # Option to select all columns
        select_all_columns = st.sidebar.checkbox(
            "Select all columns from selected tables",
            value=select_all_columns_value
        )
        
        # Update session state
        st.session_state.prev_select_all_columns = select_all_columns
        
        if select_all_columns:
            selected_columns = st.session_state.available_columns
        else:
            # Create display names for columns (schema.table.column)
            column_display_names = [f"{schema}.{table}.{column} ({data_type})" 
                                  for schema, table, column, data_type in st.session_state.available_columns]
            
            selected_column_displays = st.sidebar.multiselect(
                "Choose specific columns:",
                column_display_names,
                key="column_multiselect"
            )
            
            # Convert back to tuple format
            selected_columns = []
            for display_name in selected_column_displays:
                for schema, table, column, data_type in st.session_state.available_columns:
                    if display_name.startswith(f"{schema}.{table}.{column}"):
                        selected_columns.append((schema, table, column, data_type))
                        break
    else:
        st.sidebar.info("No columns found in selected table(s)")
        selected_columns = []
else:
    st.sidebar.info("Please select database, schema(s), and table(s) first")
    selected_columns = []

# Main content area
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("🔍 Search Configuration")
    
    # Display current selections
    if selected_database:
        st.write("**Selected Database:**", selected_database)
    
    if selected_schemas:
        st.write("**Available Schemas:**", ", ".join(selected_schemas))
    
    if selected_tables:
        table_names = [f"{schema}.{table}" for schema, table in selected_tables]
        st.write("**Available Tables:**", ", ".join(table_names))
    
    if selected_columns:
        st.write(f"**Available Columns:** {len(selected_columns)} column(s)")
        with st.expander("View available columns"):
            for schema, table, column, data_type in selected_columns:
                st.write(f"• {schema}.{table}.{column} ({data_type})")

with col2:
    st.subheader("🎯 Search Filters")
    
    # Initialize search filter variables
    search_schemas = []
    search_tables = []
    
    # Schema filter for search
    if selected_schemas:
        search_schemas = st.multiselect(
            "🏗️ Limit search to specific schemas:",
            selected_schemas,
            default=selected_schemas,
            help="Choose which schemas to actually search in",
            key="search_schema_filter"
        )
    
    # Table filter for search
    if selected_tables and search_schemas:
        # Filter tables to only show those in selected search schemas
        filtered_tables = [(schema, table) for schema, table in selected_tables if schema in search_schemas]
        if filtered_tables:
            table_display_names = [f"{schema}.{table}" for schema, table in filtered_tables]
            selected_search_table_displays = st.multiselect(
                "📋 Limit search to specific tables:",
                table_display_names,
                default=table_display_names,
                help="Choose which tables to actually search in",
                key="search_table_filter"
            )
            
            # Convert back to tuple format
            search_tables = []
            for display_name in selected_search_table_displays:
                schema, table = display_name.split('.')
                search_tables.append((schema, table))
    elif selected_tables and not search_schemas:
        st.info("Please select schemas first to enable table filtering")

# Search Input Section
st.subheader("🔍 Search Input")

# Search input
search_string = st.text_input(
    "Enter search string:",
    placeholder="Type your search term here...",
    help="This will use Snowflake's SEARCH function to find matches across selected columns"
)

# Search button
search_button = st.button("🔍 Search", type="primary", use_container_width=True)

# Search results
st.markdown("---")
st.subheader("📊 Search Results")

if search_button and search_string.strip():
    if not selected_database:
        st.warning("Please select a database first.")
    elif not selected_columns:
        st.warning("Please select at least one column to search in.")
    elif not search_schemas:
        st.warning("Please select at least one schema to search in.")
    elif not search_tables:
        st.warning("Please select at least one table to search in.")
    else:
        # Filter columns to only include those from selected search schemas and tables
        filtered_columns = []
        for schema, table, column, data_type in selected_columns:
            if schema in search_schemas and (schema, table) in search_tables:
                filtered_columns.append((schema, table, column, data_type))
        
        if not filtered_columns:
            st.warning("No columns available for the selected search schemas and tables. Please adjust your filters.")
        else:
            # Display search scope
            search_scope_col1, search_scope_col2 = st.columns([1, 1])
            with search_scope_col1:
                st.info(f"🎯 Searching in {len(search_schemas)} schema(s): {', '.join(search_schemas)}")
            with search_scope_col2:
                table_names = [f"{schema}.{table}" for schema, table in search_tables]
                st.info(f"📋 Searching {len(search_tables)} table(s): {', '.join(table_names)}")
            
            st.info(f"🔍 Searching across {len(filtered_columns)} column(s) for: '{search_string}'")
            
            with st.spinner("Searching..."):
                table_results = perform_search(selected_database, search_string, filtered_columns, search_tables, force_wildcard)
            
            if table_results:
                # Calculate total results
                total_results = sum(len(df) for df in table_results.values())
                st.success(f"Found {total_results} result(s) containing '{search_string}' across {len(table_results)} table(s)")
                
                # Create combined DataFrame for download
                all_dfs = list(table_results.values())
                combined_df = pd.concat(all_dfs, ignore_index=True) if all_dfs else pd.DataFrame()
                
                # Download button for all results
                if not combined_df.empty:
                    csv = combined_df.to_csv(index=False)
                    st.download_button(
                        label="📥 Download All Results as CSV",
                        data=csv,
                        file_name=f"search_results_all_{search_string}_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv"
                    )
                
                st.markdown("---")
                
                # Display results for each table separately
                for table_key, df in table_results.items():
                    st.subheader(f"📋 Results from {table_key}")
                    st.write(f"**{len(df)} record(s) found**")
                    
                    # Display table results
                    st.dataframe(
                        df,
                        use_container_width=True,
                        height=min(400, max(200, len(df) * 35 + 50))  # Dynamic height based on rows
                    )
                    
                    # Individual table download button
                    table_csv = df.to_csv(index=False)
                    st.download_button(
                        label=f"📥 Download {table_key} Results",
                        data=table_csv,
                        file_name=f"search_results_{table_key.replace('.', '_')}_{search_string}_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv",
                        key=f"download_{table_key}"
                    )
                    
                    st.markdown("---")
            else:
                st.info(f"No results found for '{search_string}' in the selected schemas and tables.")
            
elif search_button and not search_string.strip():
    st.warning("Please enter a search string.")

# Instructions
st.markdown("---")
with st.expander("ℹ️ How to use this app"):
    st.markdown("""
    **Step-by-step instructions:**
    
    1. **Select Database**: Choose which database to explore from the available options
    2. **Select Schema(s)**: Choose schemas from the selected database to populate table options
    3. **Select Table(s)**: Pick tables from your selected schema(s) to populate column options
    4. **Select Column(s)**: Either:
       - Check "Select all columns" to include all columns from selected tables
       - Or manually select specific columns from the dropdown
    5. **Filter Search Scope**: 
       - **Schema Filter**: Choose which specific schemas to actually search in
       - **Table Filter**: Choose which specific tables to actually search in
    6. **Enter Search Term**: Type the text you want to search for
    7. **Click Search**: The app will use Snowflake's SEARCH function to find matches
    
    **Key Features:**
    - 🗃️ **Database Selection**: Choose from any accessible database in your Snowflake environment
    - 🔄 **Cascading Menus**: Auto-populate schemas, tables and columns based on database/schema selection
    - 🎯 **Flexible Filtering**: Select columns from multiple schemas/tables, then filter search scope
    - 📊 **Interactive Results**: View and download search results
    - ⚡ **Optimized Search**: Uses Snowflake's SEARCH function for better performance
    - 🏗️ **Granular Control**: Search specific schemas and tables even after broader column selection
    
    **Pro Tip**: You can select columns from many tables/schemas for convenience, then use the search filters to narrow down exactly where to search!
    """) 
