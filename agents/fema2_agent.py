# -*- coding: utf-8 -*-
"""
BigQuery Agent - A flexible Python class for accessing and querying BigQuery datasets.
Enhanced with ADK integration for agent-based workflows.
"""

from google.cloud import bigquery
from typing import Optional, List, Dict, Any
import pandas as pd

# ADK imports for agent integration
from google.adk.agents import Agent
from google.adk.tools.bigquery import BigQueryCredentialsConfig, BigQueryToolset
from google.adk.tools.bigquery.config import BigQueryToolConfig, WriteMode
from google.genai import types
import google.auth

PROJECT_ID = "qwiklabs-gcp-01-2a76b8f0c7a6" # @param {type:"string"}
DATASET_NAME = "qwiklabs-gcp-01-2a76b8f0c7a6.B2AgentsForImpact"

class BigQueryAgent:
    """
    A flexible agent for interacting with BigQuery datasets and tables.
    """

    def __init__(self, project_id: Optional[str] = None):
        """
        Initialize the BigQuery agent.

        Args:
            project_id (str, optional): GCP project ID. If None, uses default credentials.
        """
        self.client = bigquery.Client(project=project_id) if project_id else bigquery.Client()
        self.project_id = project_id or self.client.project

    def list_datasets(self, project_id: Optional[str] = None) -> List[str]:
        """
        List all datasets in a project.

        Args:
            project_id (str, optional): Project ID to list datasets from. Uses default if None.

        Returns:
            List[str]: List of dataset IDs
        """
        target_project = project_id or self.project_id
        try:
            datasets = list(self.client.list_datasets(project=target_project))
            return [dataset.dataset_id for dataset in datasets]
        except Exception as e:
            print(f"Error listing datasets: {e}")
            return []

    def get_dataset_info(self, dataset_id: str, project_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Get information about a specific dataset.

        Args:
            dataset_id (str): Dataset ID
            project_id (str, optional): Project ID. Uses default if None.

        Returns:
            Dict[str, Any]: Dataset information or None if error
        """
        target_project = project_id or self.project_id
        try:
            dataset_ref = self.client.dataset(dataset_id, project=target_project)
            dataset = self.client.get_dataset(dataset_ref)

            return {
                'dataset_id': dataset.dataset_id,
                'project': dataset.project,
                'description': dataset.description,
                'created': dataset.created,
                'modified': dataset.modified,
                'location': dataset.location
            }
        except Exception as e:
            print(f"Error accessing dataset {dataset_id}: {e}")
            return None

    def list_tables(self, dataset_id: str, project_id: Optional[str] = None) -> List[str]:
        """
        List all tables in a dataset.

        Args:
            dataset_id (str): Dataset ID
            project_id (str, optional): Project ID. Uses default if None.

        Returns:
            List[str]: List of table IDs
        """
        target_project = project_id or self.project_id
        try:
            dataset_ref = self.client.dataset(dataset_id, project=target_project)
            tables = list(self.client.list_tables(dataset_ref))
            return [table.table_id for table in tables]
        except Exception as e:
            print(f"Error listing tables in dataset {dataset_id}: {e}")
            return []

    def get_table_info(self, dataset_id: str, table_id: str, project_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Get information about a specific table.

        Args:
            dataset_id (str): Dataset ID
            table_id (str): Table ID
            project_id (str, optional): Project ID. Uses default if None.

        Returns:
            Dict[str, Any]: Table information or None if error
        """
        target_project = project_id or self.project_id
        try:
            full_table_id = f"{target_project}.{dataset_id}.{table_id}"
            table = self.client.get_table(full_table_id)

            return {
                'table_id': table.table_id,
                'dataset_id': table.dataset_id,
                'project': table.project,
                'num_rows': table.num_rows,
                'num_bytes': table.num_bytes,
                'created': table.created,
                'modified': table.modified,
                'schema': [{'name': field.name, 'type': field.field_type, 'mode': field.mode}
                          for field in table.schema]
            }
        except Exception as e:
            print(f"Error accessing table {table_id}: {e}")
            return None

    def query(self, sql: str, to_dataframe: bool = True) -> Optional[Any]:
        """
        Execute a SQL query.

        Args:
            sql (str): SQL query string
            to_dataframe (bool): If True, return pandas DataFrame. If False, return query results.

        Returns:
            pandas.DataFrame or QueryJob results, or None if error
        """
        try:
            query_job = self.client.query(sql)
            results = query_job.result()

            if to_dataframe:
                return results.to_dataframe()
            else:
                return results
        except Exception as e:
            print(f"Error executing query: {e}")
            return None

    def sample_table(self, dataset_id: str, table_id: str, limit: int = 10,
                    project_id: Optional[str] = None) -> Optional[pd.DataFrame]:
        """
        Get a sample of rows from a table.

        Args:
            dataset_id (str): Dataset ID
            table_id (str): Table ID
            limit (int): Number of rows to sample
            project_id (str, optional): Project ID. Uses default if None.

        Returns:
            pandas.DataFrame: Sample data or None if error
        """
        target_project = project_id or self.project_id
        sql = f"SELECT * FROM `{target_project}.{dataset_id}.{table_id}` LIMIT {limit}"
        return self.query(sql)

    def explore_dataset(self, dataset_id: str, project_id: Optional[str] = None) -> None:
        """
        Print comprehensive information about a dataset and its tables.

        Args:
            dataset_id (str): Dataset ID
            project_id (str, optional): Project ID. Uses default if None.
        """
        target_project = project_id or self.project_id

        # Get dataset info
        dataset_info = self.get_dataset_info(dataset_id, target_project)
        if not dataset_info:
            return

        print(f"Dataset: {dataset_info['dataset_id']}")
        print(f"Project: {dataset_info['project']}")
        print(f"Description: {dataset_info['description']}")
        print(f"Location: {dataset_info['location']}")
        print(f"Created: {dataset_info['created']}")
        print("-" * 50)

        # List tables
        tables = self.list_tables(dataset_id, target_project)
        print(f"\nTables ({len(tables)}):")

        for table_id in tables:
            table_info = self.get_table_info(dataset_id, table_id, target_project)
            if table_info:
                print(f"  - {table_id}: {table_info['num_rows']:,} rows, {table_info['num_bytes']:,} bytes")

    def explore_all_datasets(self, project_id: Optional[str] = None, max_datasets: int = 10) -> None:
        """
        Explore all available datasets in a project with summary information.

        Args:
            project_id (str, optional): Project ID. Uses default if None.
            max_datasets (int): Maximum number of datasets to explore in detail
        """
        target_project = project_id or self.project_id

        print(f"Exploring all datasets in project: {target_project}")
        print("=" * 60)

        datasets = self.list_datasets(target_project)
        if not datasets:
            print("No datasets found or access denied.")
            return

        print(f"Found {len(datasets)} datasets:")
        for i, dataset_id in enumerate(datasets[:max_datasets]):
            print(f"\n[{i+1}/{len(datasets)}] {dataset_id}")
            print("-" * 40)

            dataset_info = self.get_dataset_info(dataset_id, target_project)
            if dataset_info:
                print(f"Description: {dataset_info['description'] or 'No description'}")
                print(f"Location: {dataset_info['location']}")

                # List tables with basic info
                tables = self.list_tables(dataset_id, target_project)
                if tables:
                    print(f"Tables ({len(tables)}):")
                    for table_id in tables[:5]:  # Show first 5 tables
                        table_info = self.get_table_info(dataset_id, table_id, target_project)
                        if table_info:
                            rows = table_info['num_rows']
                            size_mb = table_info['num_bytes'] / (1024 * 1024) if table_info['num_bytes'] else 0
                            print(f"  • {table_id}: {rows:,} rows ({size_mb:.1f} MB)")

                    if len(tables) > 5:
                        print(f"  ... and {len(tables) - 5} more tables")
                else:
                    print("No tables found in this dataset")

        if len(datasets) > max_datasets:
            print(f"\n... and {len(datasets) - max_datasets} more datasets")
            print(f"Use explore_dataset() to examine specific datasets in detail")

    def search_datasets(self, search_term: str, project_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Search for datasets containing a specific term in their ID or description.

        Args:
            search_term (str): Term to search for
            project_id (str, optional): Project ID. Uses default if None.

        Returns:
            List[Dict[str, Any]]: List of matching datasets with their info
        """
        target_project = project_id or self.project_id
        search_term_lower = search_term.lower()
        matching_datasets = []

        datasets = self.list_datasets(target_project)
        for dataset_id in datasets:
            dataset_info = self.get_dataset_info(dataset_id, target_project)
            if dataset_info:
                # Search in dataset ID and description
                if (search_term_lower in dataset_id.lower() or
                    (dataset_info['description'] and search_term_lower in dataset_info['description'].lower())):
                    matching_datasets.append(dataset_info)

        return matching_datasets

    def search_tables(self, search_term: str, project_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Search for tables containing a specific term across all datasets.

        Args:
            search_term (str): Term to search for in table names
            project_id (str, optional): Project ID. Uses default if None.

        Returns:
            List[Dict[str, Any]]: List of matching tables with their info
        """
        target_project = project_id or self.project_id
        search_term_lower = search_term.lower()
        matching_tables = []

        datasets = self.list_datasets(target_project)
        for dataset_id in datasets:
            tables = self.list_tables(dataset_id, target_project)
            for table_id in tables:
                if search_term_lower in table_id.lower():
                    table_info = self.get_table_info(dataset_id, table_id, target_project)
                    if table_info:
                        table_info['full_table_id'] = f"{target_project}.{dataset_id}.{table_id}"
                        matching_tables.append(table_info)

        return matching_tables


# Example usage and convenience functions
def create_agent(project_id: Optional[str] = None) -> BigQueryAgent:
    """
    Create a new BigQuery agent instance.

    Args:
        project_id (str, optional): GCP project ID

    Returns:
        BigQueryAgent: Configured agent instance
    """
    return BigQueryAgent(project_id)


def create_emergency_crisis_bigquery_agent(project_id: str, dataset_name: str, model: str = "gemini-2.5-flash") -> Agent:
    """
    Create an ADK Agent configured for FEMA BigQuery dataset analysis.

    Args:
        project_id: Google Cloud project ID
        dataset_name: Full dataset name (e.g., "project.dataset")
        model: Gemini model to use

    Returns:
        Configured ADK Agent for BigQuery operations
    """
    # Setup BigQuery tools
    credentials, _ = google.auth.default()
    bq_credentials = BigQueryCredentialsConfig(credentials=credentials)
    bq_tool_cfg = BigQueryToolConfig(write_mode=WriteMode.BLOCKED)  # Read-only

    bq_tools = BigQueryToolset(
        credentials_config=bq_credentials,
        bigquery_tool_config=bq_tool_cfg
    )

    # Database schema for USDA food data
    DB_SCHEMA = """
[{
  "table_name": "fema_nssf",
  "fields": [{
    "column_name": "Sheleter_id",
    "data_type": "INT64"
  }, {
    "column_name": "shelter_name",
    "data_type": "STRING"
  },
  {
    "column_name": "city",
    "data_type": "STRING"
  }, {
    "column_name": "state",
    "data_type": "STRING"
  }, {
    "column_name": "pet_capacity",
    "data_type": "INT64"
  },
  {
    "column_name": "pet_accommodations_code",
    "data_type": "INT64"
  },
  {
    "column_name": "pet_accommodations_desc",
    "data_type": "INT64"
  },
  {
    "column_name": "zip",
    "data_type": "INT64"
  },
  "column_name": "shelter_status_code",
    "data_type": "STRING"
  },
  {
    "column_name": "lattitude",
    "data_type": "FLOAT"
  },
  {
    "column_name": "longitude",
    "data_type": "FLOAT"
  },{
    "column_name": "ada_compliant",
    "data_type": "STRING"
  },{
    "column_name": "evacuation_capacity",
    "data_type": "STRING"
  },
  {
    "column_name": "org_main_phone",
    "data_type": "STRING"
  }, {
    "column_name": "address_1",
    "data_type": "STRING"
  }]
},
{
  "table_name": "hospital_general_info",
  "fields": [{
    "column_name": "provider_id",
    "data_type": "STRING"
  }, {
    "column_name": "hospital_name",
    "data_type": "STRING"
  },
  {
    "column_name": "address",
    "data_type": "STRING"
  },
  {
    "column_name": "city",
    "data_type": "STRING"
  }, {
    "column_name": "state",
    "data_type": "STRING"
  }, {
    "column_name": "zip_code",
    "data_type": "INT64"
  }]
}, {
  "table_name": "humanitarian_needs",
  "fields": [{
    "column_name": "STRING_0",
    "data_type": "STRING"
  }, {
    "column_name": "STRING1",
    "data_type": "STRING"
  }, {
    "column_name": "STRING2",
    "data_type": "STRING"
  }]
}, {
  "table_name": "Fema",
  "fields": [{
    "column_name": "id",
    "data_type": "STRING"
  }, {
    "column_name": "hash",
    "data_type": "STRING"
  }, {
    "column_name": "disasterNumber",
    "data_type": "INT64"
  }, {
    "column_name": "state",
    "data_type": "STRING"
  },
  {
    "column_name": "incidentType",
    "data_type": "STRING"
  },
  {
    "column_name": "desginatedArea",
    "data_type": "STRING"
  }]
},
{
  "table_name": "Food_Banks",
  "fields": [{
    "column_name": "service_area",
    "data_type": "STRING"
  }, {
    "column_name": "phone",
    "data_type": "STRING"
  },
  {
    "column_name": "city",
    "data_type": "STRING"
  }, {
    "column_name": "county",
    "data_type": "STRING"
  }, {
    "column_name": "state",
    "data_type": "STRING"
  },
  {
    "column_name": "zip_code",
    "data_type": "INT64"
  },
  {
    "column_name": "name",
    "data_type": "STRING"
  },
  {
    "column_name": "zip",
    "data_type": "INT64"
  },{
  "column_name": "street",
    "data_type": "STRING"
  },
  {
    "column_name": "website",
    "data_type": "STRING"
  }]
  }]
    """

    # Agent instructions
    PROJECT_ID = "qwiklabs-gcp-01-2a76b8f0c7a6" # @param {type:"string"}
    DATASET_NAME = "B2AgentsForImpact"
    instructions = f"""
The dataset you have access to contains information from FEMA e.g. fema_nssf, hospital_gengeral_info, Food_Banks and other tables
have info about emergency shelters, pet capacity, etc.
Only query the dataset `{PROJECT_ID}.{DATASET_NAME}`.
Fully qualify every table as `{PROJECT_ID}.{DATASET_NAME}.<table>`. Use all available tables and fields to make jugdement.
Never perform DDL/DML; SELECT-only. Return the SQL you ran along with a concise answer.
Here is the database schema, please study it {DB_SCHEMA}
    """

    # Create and return the agent
    return Agent(
        model=model,
        name="fema_information_bigquery_agent",
        description="Analyzes tables in a BigQuery FEMA dataset.",
        instruction=instructions,
        tools=[bq_tools],
    )




# Example usage
if __name__ == "__main__":
    # Create agent
    agent = create_agent()

    # Default behavior: Explore all available datasets
    print("🔍 Exploring all available datasets...")
    agent.explore_all_datasets()

    # Search for specific datasets
    print("\n" + "="*60)
    print("🔎 Searching for datasets containing 'fema'...")
    fema_datasets = agent.search_datasets("fema")
    for dataset in fema_datasets:
        print(f"Found: {dataset['dataset_id']} - {dataset['description']}")

    # Search for specific tables across all datasets
    print("\n" + "="*60)
    print("🔎 Searching for tables containing 'shelter'...")
    shelter_tables = agent.search_tables("shelter")
    for table in shelter_tables:
        print(f"Found: {table['full_table_id']} ({table['num_rows']:,} rows)")

    # Example: Explore a specific dataset if found
    if fema_datasets:
        print("\n" + "="*60)
        print("📊 Detailed exploration of first FEMA dataset...")
        agent.explore_dataset(fema_datasets[0]['dataset_id'], fema_datasets[0]['project'])

    # Example: Sample data from a table (uncomment if table exists)
    # if shelter_tables:
    #     print("\n" + "="*60)
    #     print("📋 Sample data from first shelter table...")
    #     sample_data = agent.query(f"SELECT * FROM `{shelter_tables[0]['full_table_id']}` LIMIT 5")
    #     if sample_data is not None:
    #         print(sample_data)

