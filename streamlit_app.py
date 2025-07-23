import streamlit as st
import pandas as pd
from snowflake.snowpark.context import get_active_session

# Get the active Snowflake session
session = get_active_session()

# Set page configuration
st.set_page_config(
    page_title="SANDBOX Database Explorer & Search",
    page_icon="🔍",
    layout="wide"
)

# Main title
st.title("🔍 SANDBOX Database Explorer & Search")
st.markdown("---")

# Initialize session state
if 'selected_schemas' not in st.session_state:
    st.session_state.selected_schemas = []
if 'selected_tables' not in st.session_state:
    st.session_state.selected_tables = []
if 'selected_columns' not in st.session_state:
    st.session_state.selected_columns = []
if 'available_tables' not in st.session_state:
    st.session_state.available_tables = []
if 'available_columns' not in st.session_state:
    st.session_state.available_columns = []

def get_schemas():
    """Get all schemas from SANDBOX database"""
    try:
        query = """
        SELECT SCHEMA_NAME 
        FROM SANDBOX.INFORMATION_SCHEMA.SCHEMATA 
        WHERE SCHEMA_NAME NOT IN ('INFORMATION_SCHEMA')
        ORDER BY SCHEMA_NAME
        """
        result = session.sql(query).collect()
        return [row['SCHEMA_NAME'] for row in result]
    except Exception as e:
        st.error(f"Error fetching schemas: {str(e)}")
        return []

def get_tables(schemas):
    """Get all tables from selected schemas"""
    if not schemas:
        return []
    
    try:
        schema_list = "', '".join(schemas)
        query = f"""
        SELECT DISTINCT TABLE_SCHEMA, TABLE_NAME 
        FROM SANDBOX.INFORMATION_SCHEMA.TABLES 
        WHERE TABLE_SCHEMA IN ('{schema_list}')
        AND TABLE_TYPE = 'BASE TABLE'
        ORDER BY TABLE_SCHEMA, TABLE_NAME
        """
        result = session.sql(query).collect()
        return [(row['TABLE_SCHEMA'], row['TABLE_NAME']) for row in result]
    except Exception as e:
        st.error(f"Error fetching tables: {str(e)}")
        return []

def get_columns(tables):
    """Get all columns from selected tables"""
    if not tables:
        return []
    
    try:
        table_conditions = []
        for schema, table in tables:
            table_conditions.append(f"(TABLE_SCHEMA = '{schema}' AND TABLE_NAME = '{table}')")
        
        where_clause = " OR ".join(table_conditions)
        
        query = f"""
        SELECT TABLE_SCHEMA, TABLE_NAME, COLUMN_NAME, DATA_TYPE
        FROM SANDBOX.INFORMATION_SCHEMA.COLUMNS 
        WHERE ({where_clause})
        ORDER BY TABLE_SCHEMA, TABLE_NAME, ORDINAL_POSITION
        """
        result = session.sql(query).collect()
        return [(row['TABLE_SCHEMA'], row['TABLE_NAME'], row['COLUMN_NAME'], row['DATA_TYPE']) for row in result]
    except Exception as e:
        st.error(f"Error fetching columns: {str(e)}")
        return []

def perform_search(search_string, selected_columns, selected_tables):
    """Perform search using Snowflake SEARCH function"""
    if not search_string.strip() or not selected_columns:
        return pd.DataFrame()
    
    try:
        # Group columns by table
        tables_columns = {}
        for schema, table, column, data_type in selected_columns:
            table_key = f"{schema}.{table}"
            if table_key not in tables_columns:
                tables_columns[table_key] = []
            tables_columns[table_key].append(column)
        
        all_results = []
        
        for table_key, columns in tables_columns.items():
            schema, table = table_key.split('.')
            
            # Create column list for SEARCH function
            column_list = ', '.join([f'"{col}"' for col in columns])
            
            # Build the search query
            search_query = f"""
            SELECT 
                '{schema}' as SCHEMA_NAME,
                '{table}' as TABLE_NAME,
                *
            FROM SANDBOX.{schema}.{table}
            WHERE SEARCH({column_list}, '{search_string}')
            LIMIT 1000
            """
            
            try:
                result = session.sql(search_query).collect()
                if result:
                    df = pd.DataFrame([row.asDict() for row in result])
                    all_results.append(df)
            except Exception as table_error:
                st.warning(f"Error searching in {table_key}: {str(table_error)}")
                continue
        
        if all_results:
            combined_df = pd.concat(all_results, ignore_index=True)
            return combined_df
        else:
            return pd.DataFrame()
            
    except Exception as e:
        st.error(f"Error performing search: {str(e)}")
        return pd.DataFrame()

# Sidebar for selections
st.sidebar.header("📋 Database Selection")

# Schema selection
st.sidebar.subheader("1. Select Schema(s)")
available_schemas = get_schemas()

if available_schemas:
    selected_schemas = st.sidebar.multiselect(
        "Choose schemas from SANDBOX database:",
        available_schemas,
        default=st.session_state.selected_schemas,
        key="schema_multiselect"
    )
    
    # Update session state and fetch tables when schemas change
    if selected_schemas != st.session_state.selected_schemas:
        st.session_state.selected_schemas = selected_schemas
        st.session_state.available_tables = get_tables(selected_schemas)
        st.session_state.selected_tables = []
        st.session_state.available_columns = []
        st.session_state.selected_columns = []
        st.rerun()
else:
    st.sidebar.error("No schemas found in SANDBOX database")
    selected_schemas = []

# Table selection
st.sidebar.subheader("2. Select Table(s)")
if selected_schemas:
    if not st.session_state.available_tables:
        st.session_state.available_tables = get_tables(selected_schemas)
    
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
            st.session_state.available_columns = get_columns(selected_tables)
            st.session_state.selected_columns = []
            st.rerun()
    else:
        st.sidebar.info("No tables found in selected schema(s)")
        selected_tables = []
else:
    st.sidebar.info("Please select schema(s) first")
    selected_tables = []

# Column selection
st.sidebar.subheader("3. Select Column(s)")
if selected_tables:
    if not st.session_state.available_columns:
        st.session_state.available_columns = get_columns(selected_tables)
    
    if st.session_state.available_columns:
        # Option to select all columns
        select_all_columns = st.sidebar.checkbox("Select all columns from selected tables")
        
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
    st.sidebar.info("Please select table(s) first")
    selected_columns = []

# Main content area
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("🔍 Search Configuration")
    
    # Display current selections
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
    if not selected_columns:
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
                results_df = perform_search(search_string, filtered_columns, search_tables)
            
            if not results_df.empty:
                st.success(f"Found {len(results_df)} result(s) containing '{search_string}'")
                
                # Display results with pagination
                st.dataframe(
                    results_df,
                    use_container_width=True,
                    height=400
                )
                
                # Download button
                csv = results_df.to_csv(index=False)
                st.download_button(
                    label="📥 Download Results as CSV",
                    data=csv,
                    file_name=f"search_results_{search_string}_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
            else:
                st.info(f"No results found for '{search_string}' in the selected schemas and tables.")
            
elif search_button and not search_string.strip():
    st.warning("Please enter a search string.")

# Instructions
st.markdown("---")
with st.expander("ℹ️ How to use this app"):
    st.markdown("""
    **Step-by-step instructions:**
    
    1. **Select Schema(s)**: Choose schemas from SANDBOX database to populate table options
    2. **Select Table(s)**: Pick tables from your selected schema(s) to populate column options
    3. **Select Column(s)**: Either:
       - Check "Select all columns" to include all columns from selected tables
       - Or manually select specific columns from the dropdown
    4. **Filter Search Scope**: 
       - **Schema Filter**: Choose which specific schemas to actually search in
       - **Table Filter**: Choose which specific tables to actually search in
    5. **Enter Search Term**: Type the text you want to search for
    6. **Click Search**: The app will use Snowflake's SEARCH function to find matches
    
    **Key Features:**
    - 🔄 **Cascading Menus**: Auto-populate tables and columns based on schema selection
    - 🎯 **Flexible Filtering**: Select columns from multiple schemas/tables, then filter search scope
    - 📊 **Interactive Results**: View and download search results
    - ⚡ **Optimized Search**: Uses Snowflake's SEARCH function for better performance
    - 🏗️ **Granular Control**: Search specific schemas and tables even after broader column selection
    
    **Pro Tip**: You can select columns from many tables/schemas for convenience, then use the search filters to narrow down exactly where to search!
    """) 