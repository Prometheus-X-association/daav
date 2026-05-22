import urllib.parse
from typing import Dict, List, Any, Tuple, Optional
import re
import logging
logger = logging.getLogger(__name__)

class DrupalFilterConverter:
    """
    Converts Drupal JSON:API filter parameters to MySQL WHERE clauses.
    
    Based on: https://www.drupal.org/docs/core-modules-and-themes/core-modules/jsonapi-module/filtering
    """
    
    # Mapping of JSON:API operators to MySQL operators
    OPERATOR_MAP = {
        '=': '=',
        '<>': '!=',
        '>': '>',
        '>=': '>=',
        '<': '<',
        '<=': '<=',
        'STARTS_WITH': 'LIKE',
        'CONTAINS': 'LIKE',
        'ENDS_WITH': 'LIKE',
        'IN': 'IN',
        'NOT IN': 'NOT IN',
        'BETWEEN': 'BETWEEN',
        'NOT BETWEEN': 'NOT BETWEEN',
        'IS NULL': 'IS NULL',
        'IS NOT NULL': 'IS NOT NULL',
    }
    
    def __init__(self, table_prefix: str = '', field_mapping: Optional[Dict[str, str]] = None):
        """
        Initialize the converter.
        
        Args:
            table_prefix: Optional table prefix for field names
            field_mapping: Optional mapping of JSON:API field names to database column names
        """
        self.table_prefix = table_prefix
        self.field_mapping = field_mapping or {}
        
    def parse_query_string(self, query_string: str) -> Dict[str, Any]:
        """Parse URL query string into filter structure.
        
        Example:
            Input: filter[test][condition][path]=model&filter[test][condition][operator]=STARTS_WITH&filter[test][condition][value]=M
            Output: {
                'test': 
                    {'condition': 
                        {
                            'path': 'model', 
                            'operator': 'STARTS_WITH', 
                            'value': 'M'
                        }
                    }
                }
        """
        parsed = urllib.parse.parse_qs(query_string, keep_blank_values=True)
        filters = {}
        
        for key, values in parsed.items():
            if key.startswith('filter['):
                # Parse filter structure from key
                parts = self._parse_filter_key(key)
                if parts:
                    self._build_filter_structure(filters, parts, values[0] if values else '')
        logger.info(f"Parsed filters: {filters}")         
        return filters
    
    def _parse_filter_key(self, key: str) -> List[str]:
        """Parse filter key like 'filter[label][condition][path]' into parts."""
        # Remove 'filter[' prefix and split by '][' or ']'
        key = key[7:]  # Remove 'filter['
        if key.endswith(']'):
            key = key[:-1]  # Remove trailing ']'
            
        # Split by '][' to get the parts
        parts = key.split('][')
        return parts
    
    def _build_filter_structure(self, filters: Dict, parts: List[str], value: str):
        """Build nested filter structure from parsed parts."""
        current = filters
        for i, part in enumerate(parts[:-1]):
            if part not in current:
                current[part] = {}
            current = current[part]
        
        # Handle array values (e.g., value[1], value[2])
        last_part = parts[-1]
        if '[' in last_part and ']' in last_part:
            # This is an array index like 'value[1]'
            array_key = last_part.split('[')[0]
            if array_key not in current:
                current[array_key] = {}
            index = last_part.split('[')[1].rstrip(']')
            current[array_key][index] = value
        else:
            current[last_part] = value
    
    def convert_filters_to_where(self, filters: Dict[str, Any]) -> Tuple[str, List[Any]]:
        """
        Convert parsed filters to MySQL WHERE clause.
        
        Returns:
            Tuple of (where_clause, parameters) for parameterized query

        Example:
            Input: {
                'test': {
                    'condition': {
                        'path': 'model',
                        'operator': 'STARTS_WITH',
                        'value': 'M'
                    }
                }
            }
            Output: ("model LIKE ?", ['M%'])
        """
        groups = {}
        conditions_by_group = {}  # Stocker les conditions par groupe
        root_conditions = []
        
        # First pass: identify groups and organize conditions
        for label, filter_data in filters.items():
            if 'group' in filter_data:
                groups[label] = filter_data['group']
                conditions_by_group[label] = []  # Initialize empty list for this group
            elif 'condition' in filter_data:
                condition_data = filter_data['condition']
                member_of = condition_data.get('memberOf')
                
                if member_of:
                    # This condition belongs to a group
                    if member_of not in conditions_by_group:
                        conditions_by_group[member_of] = []
                    conditions_by_group[member_of].append((label, condition_data))
                else:
                    # This is a root condition
                    root_conditions.append((label, condition_data))
            else:
                # Handle shortcut syntax like filter[field_name]=value
                if isinstance(filter_data, dict) and 'value' in filter_data:
                    condition_data = {'path': label, 'operator': '=', 'value': filter_data['value']}
                else:
                    condition_data = {'path': label, 'operator': '=', 'value': filter_data}
                
                root_conditions.append((label, condition_data))
        
        # Second pass: build conditions and collect parameters IN ORDER
        final_conditions = []
        parameters = []
        
        # Build root conditions FIRST (they will appear first in WHERE clause)
        for label, condition_data in root_conditions:
            condition_sql, condition_params = self._build_condition(condition_data)
            if condition_sql:
                final_conditions.append(condition_sql)
                parameters.extend(condition_params)  # Add parameters in order
        
        # Build group conditions AFTER root conditions
        for group_label, group_data in groups.items():
            if group_label in conditions_by_group and conditions_by_group[group_label]:
                conjunction = group_data.get('conjunction', 'AND')
                group_sql_parts = []
                
                # Process conditions in this group
                for label, condition_data in conditions_by_group[group_label]:
                    condition_sql, condition_params = self._build_condition(condition_data)
                    if condition_sql:
                        group_sql_parts.append(condition_sql)
                        parameters.extend(condition_params)  # Add parameters in order
                
                if group_sql_parts:
                    group_sql = f"({f' {conjunction} '.join(group_sql_parts)})"
                    final_conditions.append(group_sql)
        
        # Build final WHERE clause
        if final_conditions:
            where_clause = ' AND '.join(final_conditions)
            return f"{where_clause}", parameters
        else:
            return "", []
    
    def _build_condition(self, condition_data: Dict[str, Any]) -> Tuple[str, List[Any]]:
        """Build a single condition from condition data."""
        path = condition_data.get('path', '')
        operator = condition_data.get('operator', '=')
        value = condition_data.get('value')
        
        # Map field path to database column
        field_name = self._map_field_path(path)
        
        # Handle different operators
        if operator in ['IS NULL', 'IS NOT NULL']:
            return f"{field_name} {self.OPERATOR_MAP[operator]}", []
        
        elif operator in ['IN', 'NOT IN']:
            # Handle array values
            if isinstance(value, dict):
                # Convert indexed dict to list
                values = [value[key] for key in sorted(value.keys())]
            elif isinstance(value, list):
                values = value
            else:
                values = [value]
            
            placeholders = ', '.join(['%s'] * len(values))
            return f"{field_name} {self.OPERATOR_MAP[operator]} ({placeholders})", values
        
        elif operator == 'BETWEEN' or operator == 'NOT BETWEEN':
            if isinstance(value, dict):
                values = [value[key] for key in sorted(value.keys())]
            elif isinstance(value, list):
                values = value
            else:
                # Assume two values separated by comma or similar
                values = str(value).split(',', 1)
            
            if len(values) >= 2:
                return f"{field_name} {self.OPERATOR_MAP[operator]} ? AND ?", values[:2]
            else:
                return f"{field_name} {self.OPERATOR_MAP[operator]} ? AND ?", [value, value]
        
        elif operator in ['STARTS_WITH', 'ENDS_WITH', 'CONTAINS']:
            # Handle LIKE operations
            if operator == 'STARTS_WITH':
                like_value = f"{value}%"
            elif operator == 'ENDS_WITH':
                like_value = f"%{value}"
            else:  # CONTAINS
                like_value = f"%{value}%"
            
            return f"{field_name} LIKE ?", [like_value]
        
        else:
            # Standard comparison operators — reject any operator not in the whitelist
            if operator not in self.OPERATOR_MAP:
                raise ValueError(f"Unsupported filter operator: {operator!r}")
            mysql_operator = self.OPERATOR_MAP[operator]
            return f"{field_name} {mysql_operator} ?", [value]
    
    def _build_simple_condition(self, field_name: str, value: Any) -> Tuple[str, List[Any]]:
        """Build a simple condition from field name and value."""
        mapped_field = self._map_field_path(field_name)
        return f"{mapped_field} = ?", [value]
    
    def _map_field_path(self, path: str) -> str:
        """
        Map JSON:API field path to database column name.
        
        Handles dot notation for relationships and field mapping.
        """
        # Handle dot notation for relationships
        if '.' in path:
            parts = path.split('.')
            # For now, flatten relationships - in a real implementation,
            # you'd need to handle JOINs
            if len(parts) == 2 and parts[1] in ['id', 'uuid']:
                # Handle entity reference IDs
                base_field = parts[0]
                if parts[1] == 'id':
                    mapped_field = f"{base_field}_uuid"  # Drupal typically stores UUIDs
                else:
                    mapped_field = f"{base_field}_{parts[1]}"
            else:
                # For complex relationships, you might need JOINs
                # For simplicity, we'll just use the last part
                mapped_field = parts[-1]
        else:
            mapped_field = path
        
        # Apply field mapping if provided
        if mapped_field in self.field_mapping:
            mapped_field = self.field_mapping[mapped_field]
        
        # Add table prefix if provided
        if self.table_prefix and not '.' in mapped_field:
            mapped_field = f"{self.table_prefix}.{mapped_field}"
        
        return mapped_field
    
    def convert_query_string_to_where(self, query_string: str) -> Tuple[str, List[Any]]:
        """
        Convert a URL query string with Drupal filters to MySQL WHERE clause.
        
        Args:
            query_string: URL query string containing filter parameters
            
        Returns:
            Tuple of (where_clause, parameters) for parameterized query

        Example:
            Input: "filter[test][condition][path]=model&filter[test][condition][operator]=STARTS_WITH&filter[test][condition][value]=M"
            Output: ('model LIKE ?', ['M%'])
        """
        filters = self.parse_query_string(query_string)
        return self.convert_filters_to_where(filters)