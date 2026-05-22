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
            dataSource, filterRules, parquetSave = self._retreiveFilterData()

            if not filterRules:
                self.statusMessage = "WARNING: No filter rules"
                return StatusNode.Error
            
            else:
                try:
                    whereClause = self.process_condition(filterRules)
                    if not whereClause:
                        whereClause = "1=1" 

                except Exception as e:
                    self.statusMessage = f"Error in filter conditions: {str(e)}"
                    return StatusNode.Error
            
            source_data = self.inputs[dataSource].get_node_data()

            if not parquetSave:
                if(isinstance(source_data, NodeDataPandasDf)):
                    data = source_data.dataExample if sample else source_data.data

                    conn = duckdb.connect()
                    conn.register('source_table', data)

                    query = f"SELECT * FROM source_table WHERE {whereClause}"
                    logger.info(f"Executing query: {query}")
                    result_df = conn.execute(query).fetchdf()
                    conn.close()

                    # Check if result is empty
                    if result_df.empty:
                        self.statusMessage = "No data matches the filter conditions"
                        return StatusNode.Error
                    
                    # Create node data output
                    if sample:
                        self.outputs.get('out').set_node_data(
                            NodeDataPandasDf(
                                nodeSchema=generate_pandas_schema(result_df),
                                dataExample=result_df, 
                                name="Filtered Data"
                            ),
                            self
                        )
                    else:
                        self.outputs.get('out').set_node_data(
                            NodeDataPandasDf(
                                nodeSchema=generate_pandas_schema(result_df),
                                data=result_df,
                                dataExample=result_df.head(20), 
                                name="Filtered Data"
                            ),
                            self
                        )
                    return StatusNode.Valid

                elif(isinstance(source_data, NodeDataParquet)):
                    """ Process treatement using duckDB if source node is parquet """
                    file_path = PathSecurityValidator.validate_file_path(source_data.data)
                    data = pq.read_table(file_path).to_pandas()

                    conn = duckdb.connect()
                    conn.register('source_table', data)

                    query = f"SELECT * FROM source_table WHERE {whereClause}"
                    print(query)
                    result_df = conn.execute(query).fetchdf()
                    conn.close()

                    # Add empty result check here too
                    if result_df.empty:
                        self.statusMessage = "No data matches the filter conditions"
                        return StatusNode.Error

                else:
                    raise ValueError("Unkown data input")
                
                if result_df is None:
                    raise ValueError("No data after filter")
                
                if sample:
                    self.outputs.get('out').set_node_data(NodeDataPandasDf(
                        nodeSchema=generate_pandas_schema(result_df),
                        dataExample=result_df, 
                        name="Filtered Data"),
                        self)
                else:
                    self.outputs.get('out').set_node_data(NodeDataPandasDf(
                        nodeSchema = generate_pandas_schema(result_df) ,
                        data=result_df,
                        dataExample=result_df.head(20), 
                        name="Filtered Data"),
                        self)
                return StatusNode.Valid
                
            else:
                if(isinstance(source_data, NodeDataPandasDf)):
                    temp_dir = tempfile.gettempdir()
                    file_name = PathSecurityValidator.validate_filename(f"filtered_data_{self.id}.parquet")
                    result_parquet = os.path.join(temp_dir, file_name)
                    
                    data = source_data.dataExample if sample else source_data.data
                    
                    conn = duckdb.connect()
                    conn.register('data', data)
                    
                    query = f"COPY (SELECT * FROM data WHERE {whereClause}) TO '{result_parquet}' (FORMAT PARQUET)"
                    print(query)
                    conn.execute(query)
                    conn.close()

                elif(isinstance(source_data, NodeDataParquet)):
                    temp_dir = tempfile.gettempdir()
                    file_name = PathSecurityValidator.validate_filename(f"filtered_data_{self.id}.parquet")
                    result_parquet = os.path.join(temp_dir, file_name)
                    
                    conn = duckdb.connect()
                    
                    parquet_path = PathSecurityValidator.validate_file_path(source_data.data)
                    
                    query = f"COPY (SELECT * FROM read_parquet('{parquet_path}') WHERE {whereClause}) TO '{result_parquet}' (FORMAT PARQUET)"
                    print(query)
                    conn.execute(query)
                    conn.close()
                
                else:
                    raise ValueError("Unkown data input")
                
                # Add check for empty result in parquet case
                if not os.path.getsize(result_parquet):
                    self.statusMessage = "No data matches the filter conditions"
                    return StatusNode.Error
                
                # Create the node data output
                parquet_file = pq.ParquetFile(result_parquet)
                schema = parquet_file.schema
                node_data = NodeDataParquet(
                    data=result_parquet,
                    nodeSchema=schema,
                    name="filtered_data",
                )
                self.outputs.get('out').set_node_data(node_data, self)
                return StatusNode.Valid

        except Exception as e:
            self.statusMessage = str(e)
            self.errorStackTrace = traceback.TracebackException.from_exception(e).format()
            return StatusNode.Error  
    
    def _retreiveFilterData(self):
        if self.data.get('dataSource') and self.data.get('filterRules') and self.data.get('parquetSave'):
            dataSource = self.data.get('dataSource')
            filterRules = self.data.get('filterRules')
            parquetSave = self.data.get('parquetSave')['value']
            return dataSource, filterRules, parquetSave
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
            value = f"'{value}'"

            string_operators = {
                'contains': lambda f, v: f"CONTAINS(LOWER({f}), LOWER({v}))",
                '=': lambda f, v: f"LOWER({f}) = LOWER({v})",
                '!=': lambda f, v: f"LOWER({f}) != LOWER({v})",
                'like': lambda f, v: f"LOWER({f}) LIKE LOWER('%" + v.strip("'") + "%')",
                'in': lambda f, v: f"{f} IN ({v})",
                'not in': lambda f, v: f"{f} NOT IN ({v})",
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