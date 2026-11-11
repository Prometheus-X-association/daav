import traceback
from app.nodes.transforms.transform_node import TransformNode
from typing import Dict, List, Optional, Any

from pydantic import BaseModel, ConfigDict, TypeAdapter
from app.enums.status_node import StatusNode
from app.models.interface.node_data import NodeDataPandasDf, NodeDataParquet
import duckdb 
from app.utils.utils import generate_pandas_schema
import pyarrow.parquet as pq
import tempfile
import os
from app.utils.security import PathSecurityValidator
import logging
logger = logging.getLogger(__name__)

# Whitelist of allowed comparison operators for numeric values in DuckDB
_NUMERIC_OPERATORS = {'=', '!=', '<>', '>', '>=', '<', '<='}

# Allowed conjunctions for rule groups
_ALLOWED_CONJUNCTIONS = {'AND', 'OR'}


def _quote_duckdb_identifier(name: str) -> str:
    """Double-quote a DuckDB column/table identifier, escaping inner double-quotes."""
    return '"' + name.replace('"', '""') + '"'


def _escape_duckdb_string(value: Any) -> str:
    """Content of a DuckDB string literal: inner single quotes are doubled, so the value cannot end the literal."""
    return str(value).replace("'", "''")


def _duckdb_literal(value: Any) -> str:
    """DuckDB literal of an item of an IN list: a number as it is, anything else as an escaped string."""
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return str(value)
    return f"'{_escape_duckdb_string(value)}'"

class Source(BaseModel):
    id: str
    name: str
    type: str
    datasetId: str

class FilterTransform(TransformNode):
    def __init__(self, id: str, data: Any, revision: Optional[str] = None, status: Optional[StatusNode] = None):
        """Initialize a new ExampleTransform instance.

        Args:
            data (Any): Data associated with the node
            id (str): Unique identifier for the node
            revision (Optional[str]): Revision identifier for the node
            status (Optional[StatusNode]): Current status of the node
        """
        super().__init__(id=id, data=data, revision=revision, status=status)    

    def process(self, sample=False) -> StatusNode:
        """
        Processes the input data by applying the filter rules.
        Args:
            sample (bool, optional): If True, use sample data for processing. Defaults to False.
        Returns:
            StatusNode: The status of the node after processing. Returns StatusNode.Valid if successful, 
                        otherwise returns StatusNode.Error.
        Raises:
            ValueError: If the input data format  is not handle.

        """
        try:
            data_source, filter_rules, parquet_save = self._retreiveFilterData()

            if not filter_rules:
                self.statusMessage = "WARNING: No filter rules"
                return StatusNode.Error

            try:
                where_clause = self._where_clause(filter_rules)
            except Exception as e:
                self.statusMessage = f"Error in filter conditions: {str(e)}"
                return StatusNode.Error

            source_data = self.inputs[data_source].get_node_data()
            # A filter that matches no row is a valid, empty result
            if parquet_save:
                return self._filter_to_parquet(source_data, where_clause, sample)
            return self._filter_to_dataframe(source_data, where_clause, sample)

        except Exception as e:
            return self._fail(e, print_traceback=False)

    def _where_clause(self, filter_rules) -> str:
        """SQL condition of the filter rules; every row matches when the rules give no condition."""
        return self.process_condition(filter_rules) or "1=1"

    def _filter_to_dataframe(self, source_data, where_clause: str, sample: bool) -> StatusNode:
        """Filter the source in memory and publish the result as a DataFrame."""
        if isinstance(source_data, NodeDataPandasDf):
            data = source_data.dataExample if sample else source_data.data
        elif isinstance(source_data, NodeDataParquet):
            # Process treatement using duckDB if source node is parquet
            file_path = PathSecurityValidator.validate_file_path(source_data.data)
            data = pq.read_table(file_path).to_pandas()
        else:
            raise ValueError("Unkown data input")

        conn = duckdb.connect()
        conn.register('source_table', data)
        query = f"SELECT * FROM source_table WHERE {where_clause}"
        logger.info(f"Executing query: {query}")
        result_df = conn.execute(query).fetchdf()
        conn.close()

        if result_df is None:
            raise ValueError("No data after filter")
        return self._publish_dataframe(result_df, "Filtered Data", sample)

    def _filter_to_parquet(self, source_data, where_clause: str, sample: bool) -> StatusNode:
        """Filter the source with DuckDB into a Parquet file and publish it."""
        if isinstance(source_data, NodeDataPandasDf):
            result_parquet = self._result_parquet_path()
            conn = duckdb.connect()
            conn.register('data', source_data.dataExample if sample else source_data.data)
            query = f"COPY (SELECT * FROM data WHERE {where_clause}) TO '{result_parquet}' (FORMAT PARQUET)"
        elif isinstance(source_data, NodeDataParquet):
            result_parquet = self._result_parquet_path()
            conn = duckdb.connect()
            parquet_path = PathSecurityValidator.validate_file_path(source_data.data)
            query = f"COPY (SELECT * FROM read_parquet('{parquet_path}') WHERE {where_clause}) TO '{result_parquet}' (FORMAT PARQUET)"
        else:
            raise ValueError("Unkown data input")

        print(query)
        conn.execute(query)
        conn.close()

        # Create the node data output (a filter that matches no row gives an empty file)
        node_data = NodeDataParquet(
            data=result_parquet,
            nodeSchema=pq.ParquetFile(result_parquet).schema,
            name="filtered_data",
        )
        self.outputs.get('out').set_node_data(node_data, self)
        return StatusNode.Valid

    def _result_parquet_path(self) -> str:
        file_name = PathSecurityValidator.validate_filename(f"filtered_data_{self.id}.parquet")
        return os.path.join(tempfile.gettempdir(), file_name)

    def _retreiveFilterData(self):
        if self.data.get('dataSource') and self.data.get('filterRules') and self.data.get('parquetSave'):
            data_source = self.data.get('dataSource')
            filter_rules = self.data.get('filterRules')
            parquet_save = self.data.get('parquetSave')['value']
            return data_source, filter_rules, parquet_save
        else:
            print(f"datasource : {self.data.get('dataSource')}, filterRules: {self.data.get('filterRules')}")
            raise ValueError("Input required")
    
    def translateRule(self, rule):
        """Translates a single filter rule to a SQL condition.
        
        Args:
            rule (dict): The filter rule to translate.
            
        Returns:
            str: SQL condition representing the rule.
        """
        field = rule['field']
        operator = rule['operator']
        value = rule.get('value')

        # Quote the column identifier to prevent injection
        quoted_field = _quote_duckdb_identifier(field)

        if value is None:
            if operator == '=':
                return f"{quoted_field} IS NULL"
            elif operator == '!=':
                return f"{quoted_field} IS NOT NULL"
            else:
                return "1=0"

        if isinstance(value, (int, float)) or (isinstance(value, str) and value.replace('.', '', 1).isdigit()):
            if operator not in _NUMERIC_OPERATORS:
                raise ValueError(f"Unsupported numeric operator: {operator!r}")
            return f"{quoted_field} {operator} {value}"
        else:
            # The value comes from the workflow: escape it so that it stays inside its string literal
            escaped = _escape_duckdb_string(value)
            if isinstance(value, (list, tuple)):
                in_list = ', '.join(_duckdb_literal(item) for item in value)
            else:
                in_list = f"'{escaped}'"
            value = f"'{escaped}'"

            string_operators = {
                'contains': lambda f, v: f"CONTAINS(LOWER({f}), LOWER({v}))",
                '=': lambda f, v: f"LOWER({f}) = LOWER({v})",
                '!=': lambda f, v: f"LOWER({f}) != LOWER({v})",
                'like': lambda f, v: f"LOWER({f}) LIKE LOWER('%{escaped}%')",
                'in': lambda f, v: f"{f} IN ({in_list})",
                'not in': lambda f, v: f"{f} NOT IN ({in_list})",
            }

            if operator in string_operators:
                return string_operators[operator](quoted_field, value)
            else:
                raise ValueError(f"Unsupported string operator: {operator!r}")
    
    def process_condition(self, condition):
        """Recursively processes filter conditions to build a SQL WHERE clause.
        
        Args:
            condition (dict): The condition to process.
            
        Returns:
            str: SQL WHERE clause.
        """
        try:
            if "condition" in condition:
                operator = condition["condition"].upper()
                if operator not in _ALLOWED_CONJUNCTIONS:
                    raise ValueError(f"Unsupported conjunction: {operator!r}. Only AND/OR are allowed.")

                rules = [self.process_condition(rule) for rule in condition.get("rules", [])]
                rules = [rule for rule in rules if rule]

                if not rules:
                    return ""
                if len(rules) == 1:
                    return rules[0]

                return f"({' '.join([rules[0]] + [f'{operator} {r}' for r in rules[1:]])})"
            elif "field" in condition:
                return self.translateRule(condition)
            else:
                raise ValueError(f"WARNING: Invalid condition {condition}")
        except Exception as e:
            raise ValueError(f"WARNING: Invalid condition {e}")

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
    )