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
    # Operators written the same way in SQL
    _SQL_OPERATORS = ('=', '>', '>=', '<', '<=', 'IN', 'NOT IN', 'BETWEEN', 'NOT BETWEEN', 'IS NULL', 'IS NOT NULL')
    OPERATOR_MAP = {
        **dict(zip(_SQL_OPERATORS, _SQL_OPERATORS)),
        '<>': '!=',
        'STARTS_WITH': 'LIKE',
        'CONTAINS': 'LIKE',
        'ENDS_WITH': 'LIKE',
    }

    # Allowed group conjunctions (inserted in the SQL, so never taken as is from the query string)
    CONJUNCTIONS = ('AND', 'OR')

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
            Output: ('"model" LIKE ?', ['M%'])
        """
        groups, conditions_by_group, root_conditions = self._classify_filters(filters)

        # Build conditions and collect parameters IN ORDER
        final_conditions = []
        parameters = []

        # Build root conditions FIRST (they will appear first in WHERE clause)
        for _label, condition_data in root_conditions:
            self._append_condition(condition_data, final_conditions, parameters)

        # Build group conditions AFTER root conditions
        for group_label, group_data in groups.items():
            group_sql = self._build_group_sql(group_data, conditions_by_group.get(group_label), parameters)
            if group_sql:
                final_conditions.append(group_sql)

        # Build final WHERE clause
        if final_conditions:
            return ' AND '.join(final_conditions), parameters
        return "", []

    def _classify_filters(self, filters: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, List], List]:
        """Split the filters into groups, conditions by group label and root conditions."""
        groups = {}
        conditions_by_group = {}
        root_conditions = []
        for label, filter_data in filters.items():
            # Only a dict can declare a group or a condition: a shortcut value is a plain string
            is_dict = isinstance(filter_data, dict)
            if is_dict and 'group' in filter_data:
                groups[label] = filter_data['group']
                # Keep the conditions already collected: a group may be declared after its members
                conditions_by_group.setdefault(label, [])
            elif is_dict and 'condition' in filter_data:
                condition_data = filter_data['condition']
                member_of = condition_data.get('memberOf')
                if member_of:
                    # This condition belongs to a group
                    conditions_by_group.setdefault(member_of, []).append((label, condition_data))
                else:
                    root_conditions.append((label, condition_data))
            else:
                root_conditions.append((label, self._shortcut_condition(label, filter_data)))
        return groups, conditions_by_group, root_conditions

    @staticmethod
    def _shortcut_condition(label: str, filter_data: Any) -> Dict[str, Any]:
        """Condition of the shortcut syntax filter[field_name]=value."""
        if isinstance(filter_data, dict) and 'value' in filter_data:
            value = filter_data['value']
        else:
            value = filter_data
        return {'path': label, 'operator': '=', 'value': value}

    def _build_group_sql(self, group_data: Dict[str, Any], conditions: Optional[List],
                         parameters: List[Any]) -> Optional[str]:
        """Build the SQL of a group, adding its parameters in order; None if the group is empty."""
        if not conditions:
            return None
        conjunction = str(group_data.get('conjunction', 'AND')).upper()
        if conjunction not in self.CONJUNCTIONS:
            raise ValueError(f"Unsupported filter group conjunction: {conjunction!r}")
        group_sql_parts = []
        for _label, condition_data in conditions:
            self._append_condition(condition_data, group_sql_parts, parameters)
        if not group_sql_parts:
            return None
        return f"({f' {conjunction} '.join(group_sql_parts)})"

    def _append_condition(self, condition_data: Dict[str, Any], sql_parts: List[str], parameters: List[Any]):
        """Build a condition and append its SQL and parameters."""
        condition_sql, condition_params = self._build_condition(condition_data)
        if condition_sql:
            sql_parts.append(condition_sql)
            parameters.extend(condition_params)

    def _build_condition(self, condition_data: Dict[str, Any]) -> Tuple[str, List[Any]]:
        """Build a single condition from condition data."""
        path = condition_data.get('path', '')
        operator = condition_data.get('operator', '=')
        value = condition_data.get('value')

        # Map field path to database column
        field_name = self._map_field_path(path)

        if operator in ('IS NULL', 'IS NOT NULL'):
            return f"{field_name} {self.OPERATOR_MAP[operator]}", []
        if operator in ('IN', 'NOT IN'):
            values = self._as_list(value, lambda scalar: [scalar])
            placeholders = ', '.join(['?'] * len(values))
            return f"{field_name} {self.OPERATOR_MAP[operator]} ({placeholders})", values
        if operator in ('BETWEEN', 'NOT BETWEEN'):
            return f"{field_name} {self.OPERATOR_MAP[operator]} ? AND ?", self._between_values(value)
        if operator in ('STARTS_WITH', 'ENDS_WITH', 'CONTAINS'):
            return f"{field_name} LIKE ?", [self._like_pattern(operator, value)]
        # Standard comparison operators — reject any operator not in the whitelist
        if operator not in self.OPERATOR_MAP:
            raise ValueError(f"Unsupported filter operator: {operator!r}")
        return f"{field_name} {self.OPERATOR_MAP[operator]} ?", [value]

    @staticmethod
    def _as_list(value: Any, from_scalar) -> List[Any]:
        """Values of an indexed dict (by key order) or of a list; other values go through from_scalar."""
        if isinstance(value, dict):
            return [value[key] for key in sorted(value.keys())]
        if isinstance(value, list):
            return value
        return from_scalar(value)

    @classmethod
    def _between_values(cls, value: Any) -> List[Any]:
        """The two bounds of a BETWEEN; a scalar is split on its first comma."""
        values = cls._as_list(value, lambda scalar: str(scalar).split(',', 1))
        if len(values) >= 2:
            return values[:2]
        return [value, value]

    # LIKE pattern of each LIKE operator
    LIKE_PATTERNS = {
        'STARTS_WITH': '{}%',
        'ENDS_WITH': '%{}',
        'CONTAINS': '%{}%',
    }

    @classmethod
    def _like_pattern(cls, operator: str, value: Any) -> str:
        return cls.LIKE_PATTERNS[operator].format(value)

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
        if self.table_prefix and '.' not in mapped_field:
            mapped_field = f"{self.table_prefix}.{mapped_field}"

        # Quote each identifier part: the path comes from the query string
        # and must never be interpreted as SQL
        return '.'.join(self._quote_identifier(part) for part in mapped_field.split('.'))

    @staticmethod
    def _quote_identifier(identifier: str) -> str:
        """Quote a SQL identifier, escaping embedded double quotes."""
        escaped = identifier.replace('"', '""')
        return f'"{escaped}"'
    
    def convert_query_string_to_where(self, query_string: str) -> Tuple[str, List[Any]]:
        """
        Convert a URL query string with Drupal filters to MySQL WHERE clause.
        
        Args:
            query_string: URL query string containing filter parameters
            
        Returns:
            Tuple of (where_clause, parameters) for parameterized query

        Example:
            Input: "filter[test][condition][path]=model&filter[test][condition][operator]=STARTS_WITH&filter[test][condition][value]=M"
            Output: ('"model" LIKE ?', ['M%'])
        """
        filters = self.parse_query_string(query_string)
        return self.convert_filters_to_where(filters)