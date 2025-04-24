"""
Flexible filtering system for the Car Search application.

This module provides a powerful and flexible way to filter car collections
using a query builder pattern that supports complex filter expressions.
"""

import logging
import json
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Union, Callable, Tuple, Set
from dataclasses import dataclass, field, asdict

from src.models.car import Car, CarCollection

# Configure logging
logger = logging.getLogger(__name__)


class FilterOperator(Enum):
    """Operators for filter expressions."""
    EQUALS = auto()
    NOT_EQUALS = auto()
    GREATER_THAN = auto()
    LESS_THAN = auto()
    GREATER_EQUAL = auto()
    LESS_EQUAL = auto()
    CONTAINS = auto()
    STARTS_WITH = auto()
    ENDS_WITH = auto()
    IN_LIST = auto()
    BETWEEN = auto()
    IS_NULL = auto()
    IS_NOT_NULL = auto()


class LogicalOperator(Enum):
    """Logical operators for combining filter expressions."""
    AND = auto()
    OR = auto()
    NOT = auto()


@dataclass
class FilterExpression:
    """Base class for filter expressions."""
    pass


@dataclass
class SimpleFilter(FilterExpression):
    """A simple filter expression that operates on a single field."""
    field: str
    operator: FilterOperator
    value: Any


@dataclass
class CompoundFilter(FilterExpression):
    """A compound filter that combines multiple filter expressions."""
    operator: LogicalOperator
    expressions: List[FilterExpression] = field(default_factory=list)


class FieldFilterBuilder:
    """Builder for creating field-specific filters."""
    
    def __init__(self, query_builder: 'FilterQueryBuilder', field_name: str):
        """
        Initialize a field filter builder.
        
        Args:
            query_builder: The parent query builder
            field_name: The field to filter on
        """
        self.query_builder = query_builder
        self.field_name = field_name
    
    def equals(self, value: Any) -> 'FilterQueryBuilder':
        """Filter where field equals value."""
        self.query_builder.expression = SimpleFilter(
            self.field_name, FilterOperator.EQUALS, value
        )
        return self.query_builder
    
    def not_equals(self, value: Any) -> 'FilterQueryBuilder':
        """Filter where field does not equal value."""
        self.query_builder.expression = SimpleFilter(
            self.field_name, FilterOperator.NOT_EQUALS, value
        )
        return self.query_builder
    
    def greater_than(self, value: Any) -> 'FilterQueryBuilder':
        """Filter where field is greater than value."""
        self.query_builder.expression = SimpleFilter(
            self.field_name, FilterOperator.GREATER_THAN, value
        )
        return self.query_builder
    
    def less_than(self, value: Any) -> 'FilterQueryBuilder':
        """Filter where field is less than value."""
        self.query_builder.expression = SimpleFilter(
            self.field_name, FilterOperator.LESS_THAN, value
        )
        return self.query_builder
    
    def greater_equal(self, value: Any) -> 'FilterQueryBuilder':
        """Filter where field is greater than or equal to value."""
        self.query_builder.expression = SimpleFilter(
            self.field_name, FilterOperator.GREATER_EQUAL, value
        )
        return self.query_builder
    
    def less_equal(self, value: Any) -> 'FilterQueryBuilder':
        """Filter where field is less than or equal to value."""
        self.query_builder.expression = SimpleFilter(
            self.field_name, FilterOperator.LESS_EQUAL, value
        )
        return self.query_builder
    
    def contains(self, value: str) -> 'FilterQueryBuilder':
        """Filter where field contains value (for strings)."""
        self.query_builder.expression = SimpleFilter(
            self.field_name, FilterOperator.CONTAINS, value
        )
        return self.query_builder
    
    def starts_with(self, value: str) -> 'FilterQueryBuilder':
        """Filter where field starts with value (for strings)."""
        self.query_builder.expression = SimpleFilter(
            self.field_name, FilterOperator.STARTS_WITH, value
        )
        return self.query_builder
    
    def ends_with(self, value: str) -> 'FilterQueryBuilder':
        """Filter where field ends with value (for strings)."""
        self.query_builder.expression = SimpleFilter(
            self.field_name, FilterOperator.ENDS_WITH, value
        )
        return self.query_builder
    
    def in_list(self, values: List[Any]) -> 'FilterQueryBuilder':
        """Filter where field is in a list of values."""
        self.query_builder.expression = SimpleFilter(
            self.field_name, FilterOperator.IN_LIST, values
        )
        return self.query_builder
    
    def between(self, min_value: Any, max_value: Any) -> 'FilterQueryBuilder':
        """Filter where field is between min and max values (inclusive)."""
        self.query_builder.expression = SimpleFilter(
            self.field_name, FilterOperator.BETWEEN, (min_value, max_value)
        )
        return self.query_builder
    
    def is_null(self) -> 'FilterQueryBuilder':
        """Filter where field is null or not set."""
        self.query_builder.expression = SimpleFilter(
            self.field_name, FilterOperator.IS_NULL, None
        )
        return self.query_builder
    
    def is_not_null(self) -> 'FilterQueryBuilder':
        """Filter where field is not null (has a value)."""
        self.query_builder.expression = SimpleFilter(
            self.field_name, FilterOperator.IS_NOT_NULL, None
        )
        return self.query_builder


class FilterQueryBuilder:
    """Builder for creating complex filter queries."""
    
    def __init__(self):
        """Initialize a filter query builder."""
        self.expression: Optional[FilterExpression] = None
    
    def field(self, field_name: str) -> FieldFilterBuilder:
        """Start building a filter for a specific field."""
        return FieldFilterBuilder(self, field_name)
    
    def and_(self, *queries: 'FilterQueryBuilder') -> 'FilterQueryBuilder':
        """Combine this query with others using AND logic."""
        expressions = [q.expression for q in queries if q.expression is not None]
        if not expressions:
            return self
        
        if self.expression is None:
            if len(expressions) == 1:
                self.expression = expressions[0]
            else:
                self.expression = CompoundFilter(LogicalOperator.AND, expressions)
        else:
            expressions.insert(0, self.expression)
            self.expression = CompoundFilter(LogicalOperator.AND, expressions)
        
        return self
    
    def or_(self, *queries: 'FilterQueryBuilder') -> 'FilterQueryBuilder':
        """Combine this query with others using OR logic."""
        expressions = [q.expression for q in queries if q.expression is not None]
        if not expressions:
            return self
        
        if self.expression is None:
            if len(expressions) == 1:
                self.expression = expressions[0]
            else:
                self.expression = CompoundFilter(LogicalOperator.OR, expressions)
        else:
            expressions.insert(0, self.expression)
            self.expression = CompoundFilter(LogicalOperator.OR, expressions)
        
        return self
    
    def not_(self) -> 'FilterQueryBuilder':
        """Negate this query."""
        if self.expression is None:
            return self
        
        self.expression = CompoundFilter(LogicalOperator.NOT, [self.expression])
        return self
    
    # Convenience methods for common car filters
    def make(self, make: str) -> 'FilterQueryBuilder':
        """Filter by car make (exact match)."""
        return self.field('make').equals(make)
    
    def model(self, model: str) -> 'FilterQueryBuilder':
        """Filter by car model (exact match)."""
        return self.field('model').equals(model)
    
    def model_contains(self, text: str) -> 'FilterQueryBuilder':
        """Filter by car model (contains text)."""
        return self.field('model').contains(text)
    
    def price_between(self, min_price: float, max_price: float) -> 'FilterQueryBuilder':
        """Filter by price range."""
        return self.field('price').between(min_price, max_price)
    
    def price_max(self, max_price: float) -> 'FilterQueryBuilder':
        """Filter by maximum price."""
        return self.field('price').less_equal(max_price)
    
    def price_min(self, min_price: float) -> 'FilterQueryBuilder':
        """Filter by minimum price."""
        return self.field('price').greater_equal(min_price)
    
    def year_between(self, min_year: int, max_year: int) -> 'FilterQueryBuilder':
        """Filter by year range."""
        return self.field('year').between(min_year, max_year)
    
    def year_newer_than(self, year: int) -> 'FilterQueryBuilder':
        """Filter for cars newer than a specific year."""
        return self.field('year').greater_equal(year)
    
    def year_older_than(self, year: int) -> 'FilterQueryBuilder':
        """Filter for cars older than a specific year."""
        return self.field('year').less_equal(year)
    
    def mileage_max(self, max_mileage: int) -> 'FilterQueryBuilder':
        """Filter for cars with mileage less than a specific value."""
        return self.field('mileage').less_equal(max_mileage)
    
    def location(self, location: str) -> 'FilterQueryBuilder':
        """Filter by location (contains)."""
        return self.field('location').contains(location)
    
    def has_feature(self, feature_name: str) -> 'FilterQueryBuilder':
        """Filter for cars with a specific feature."""
        # This assumes features are stored in a 'features' list field
        # Actual implementation might need to be adjusted based on car model
        return self.field(f'features.{feature_name}').equals(True)


class FilterEngine:
    """Engine for applying filter expressions to car collections."""
    
    def apply_filter(self, cars: Union[List[Car], CarCollection], 
                    filter_expression: Optional[FilterExpression]) -> List[Car]:
        """
        Apply a filter expression to a collection of cars.
        
        Args:
            cars: List of cars or a CarCollection to filter
            filter_expression: The filter expression to apply
            
        Returns:
            Filtered list of cars
        """
        if isinstance(cars, CarCollection):
            cars = cars.cars
        
        if not filter_expression:
            return cars
        
        return [car for car in cars if self._evaluate_expression(car, filter_expression)]
    
    def _evaluate_expression(self, car: Car, expression: FilterExpression) -> bool:
        """
        Evaluate a filter expression against a car.
        
        Args:
            car: Car object to evaluate
            expression: Filter expression to apply
            
        Returns:
            True if the car matches the filter, False otherwise
        """
        if isinstance(expression, SimpleFilter):
            return self._evaluate_simple_filter(car, expression)
        elif isinstance(expression, CompoundFilter):
            return self._evaluate_compound_filter(car, expression)
        
        # Unknown expression type
        logger.warning(f"Unknown filter expression type: {type(expression)}")
        return True
    
    def _evaluate_simple_filter(self, car: Car, filter_expr: SimpleFilter) -> bool:
        """
        Evaluate a simple filter against a car.
        
        Args:
            car: Car object to evaluate
            filter_expr: Simple filter expression to apply
            
        Returns:
            True if the car matches the filter, False otherwise
        """
        # Get field value using attribute path (supports nested attributes with dot notation)
        field_path = filter_expr.field.split('.')
        value = car
        
        for part in field_path:
            if hasattr(value, part):
                value = getattr(value, part)
            elif isinstance(value, dict) and part in value:
                value = value[part]
            else:
                # Field not found, handle based on operator
                if filter_expr.operator == FilterOperator.IS_NULL:
                    return True
                elif filter_expr.operator == FilterOperator.IS_NOT_NULL:
                    return False
                else:
                    # For other operators, treat as not matching
                    return False
        
        # Apply operator logic
        try:
            return self._apply_operator(value, filter_expr.operator, filter_expr.value)
        except Exception as e:
            logger.warning(f"Error evaluating filter {filter_expr.field} {filter_expr.operator}: {str(e)}")
            return False
    
    def _apply_operator(self, field_value: Any, operator: FilterOperator, filter_value: Any) -> bool:
        """
        Apply a filter operator to compare a field value against a filter value.
        
        Args:
            field_value: Value from the car object
            operator: Filter operator to apply
            filter_value: Value to compare against
            
        Returns:
            Result of the comparison
        """
        if operator == FilterOperator.EQUALS:
            return field_value == filter_value
        
        elif operator == FilterOperator.NOT_EQUALS:
            return field_value != filter_value
        
        elif operator == FilterOperator.GREATER_THAN:
            if field_value is None:
                return False
            return field_value > filter_value
        
        elif operator == FilterOperator.LESS_THAN:
            if field_value is None:
                return False
            return field_value < filter_value
        
        elif operator == FilterOperator.GREATER_EQUAL:
            if field_value is None:
                return False
            return field_value >= filter_value
        
        elif operator == FilterOperator.LESS_EQUAL:
            if field_value is None:
                return False
            return field_value <= filter_value
        
        elif operator == FilterOperator.CONTAINS:
            if field_value is None:
                return False
            # Handle different types that support contains operation
            if isinstance(field_value, str) and isinstance(filter_value, str):
                return filter_value.lower() in field_value.lower()
            elif isinstance(field_value, (list, set, tuple)):
                return filter_value in field_value
            return False
        
        elif operator == FilterOperator.STARTS_WITH:
            if field_value is None or not isinstance(field_value, str):
                return False
            return field_value.lower().startswith(filter_value.lower())
        
        elif operator == FilterOperator.ENDS_WITH:
            if field_value is None or not isinstance(field_value, str):
                return False
            return field_value.lower().endswith(filter_value.lower())
        
        elif operator == FilterOperator.IN_LIST:
            return field_value in filter_value
        
        elif operator == FilterOperator.BETWEEN:
            if field_value is None:
                return False
            min_val, max_val = filter_value
            return min_val <= field_value <= max_val
        
        elif operator == FilterOperator.IS_NULL:
            return field_value is None
        
        elif operator == FilterOperator.IS_NOT_NULL:
            return field_value is not None
        
        else:
            # Unknown operator
            logger.warning(f"Unknown filter operator: {operator}")
            return False
    
    def _evaluate_compound_filter(self, car: Car, filter_expr: CompoundFilter) -> bool:
        """
        Evaluate a compound filter against a car.
        
        Args:
            car: Car object to evaluate
            filter_expr: Compound filter expression to apply
            
        Returns:
            True if the car matches the filter, False otherwise
        """
        # Empty expressions list always matches
        if not filter_expr.expressions:
            return True
        
        if filter_expr.operator == LogicalOperator.AND:
            return all(self._evaluate_expression(car, expr) for expr in filter_expr.expressions)
        
        elif filter_expr.operator == LogicalOperator.OR:
            return any(self._evaluate_expression(car, expr) for expr in filter_expr.expressions)
        
        elif filter_expr.operator == LogicalOperator.NOT:
            # NOT should have exactly one sub-expression
            if len(filter_expr.expressions) != 1:
                logger.warning(f"NOT operator expects 1 expression, got {len(filter_expr.expressions)}")
                return True
            
            return not self._evaluate_expression(car, filter_expr.expressions[0])
        
        else:
            # Unknown logical operator
            logger.warning(f"Unknown logical operator: {filter_expr.operator}")
            return True


class FilterManager:
    """Manager for filter operations."""
    
    def __init__(self):
        """Initialize a filter manager."""
        self.engine = FilterEngine()
        self.saved_filters: Dict[str, Dict] = {}
    
    def create_query(self) -> FilterQueryBuilder:
        """Create a new filter query builder."""
        return FilterQueryBuilder()
    
    def filter_cars(self, cars: Union[List[Car], CarCollection], 
                  query: Optional[FilterQueryBuilder] = None) -> List[Car]:
        """
        Filter a collection of cars using a query.
        
        Args:
            cars: Car collection to filter
            query: Filter query to apply
            
        Returns:
            Filtered list of cars
        """
        if query is None or query.expression is None:
            if isinstance(cars, CarCollection):
                return cars.cars
            return cars
        
        return self.engine.apply_filter(cars, query.expression)
    
    def _serialize_filter_expression(self, expr: FilterExpression) -> Dict:
        """
        Serialize a filter expression to a dictionary.
        
        Args:
            expr: Filter expression to serialize
            
        Returns:
            Serialized expression
        """
        if isinstance(expr, SimpleFilter):
            return {
                "type": "simple",
                "field": expr.field,
                "operator": expr.operator.name,
                "value": expr.value
            }
        elif isinstance(expr, CompoundFilter):
            return {
                "type": "compound",
                "operator": expr.operator.name,
                "expressions": [self._serialize_filter_expression(e) for e in expr.expressions]
            }
        else:
            raise ValueError(f"Unknown expression type: {type(expr)}")
    
    def _deserialize_filter_expression(self, data: Dict) -> Optional[FilterExpression]:
        """
        Deserialize a filter expression from a dictionary.
        
        Args:
            data: Serialized expression
            
        Returns:
            Deserialized expression
        """
        try:
            expr_type = data.get("type")
            
            if expr_type == "simple":
                return SimpleFilter(
                    field=data["field"],
                    operator=FilterOperator[data["operator"]],
                    value=data["value"]
                )
            elif expr_type == "compound":
                expressions = [
                    self._deserialize_filter_expression(e) for e in data["expressions"]
                ]
                expressions = [e for e in expressions if e is not None]
                
                return CompoundFilter(
                    operator=LogicalOperator[data["operator"]],
                    expressions=expressions
                )
            else:
                logger.warning(f"Unknown expression type: {expr_type}")
                return None
        except Exception as e:
            logger.error(f"Error deserializing filter expression: {str(e)}")
            return None
    
    def save_filter(self, name: str, query: FilterQueryBuilder) -> bool:
        """
        Save a filter query with a name.
        
        Args:
            name: Name to save the filter as
            query: Filter query to save
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if query.expression is None:
                logger.warning(f"Cannot save empty filter: {name}")
                return False
            
            serialized = self._serialize_filter_expression(query.expression)
            self.saved_filters[name] = serialized
            logger.info(f"Saved filter: {name}")
            return True
        except Exception as e:
            logger.error(f"Error saving filter {name}: {str(e)}")
            return False
    
    def load_filter(self, name: str) -> Optional[FilterQueryBuilder]:
        """
        Load a saved filter by name.
        
        Args:
            name: Name of the filter to load
            
        Returns:
            Loaded filter query or None if not found
        """
        try:
            if name not in self.saved_filters:
                logger.warning(f"Filter not found: {name}")
                return None
            
            serialized = self.saved_filters[name]
            expression = self._deserialize_filter_expression(serialized)
            
            if expression is None:
                logger.warning(f"Failed to deserialize filter: {name}")
                return None
            
            query = self.create_query()
            query.expression = expression
            return query
        except Exception as e:
            logger.error(f"Error loading filter {name}: {str(e)}")
            return None
    
    def delete_filter(self, name: str) -> bool:
        """
        Delete a saved filter by name.
        
        Args:
            name: Name of the filter to delete
            
        Returns:
            True if successful, False otherwise
        """
        if name not in self.saved_filters:
            logger.warning(f"Filter not found: {name}")
            return False
        
        del self.saved_filters[name]
        logger.info(f"Deleted filter: {name}")
        return True
    
    def get_saved_filters(self) -> List[str]:
        """
        Get a list of saved filter names.
        
        Returns:
            List of filter names
        """
        return list(self.saved_filters.keys())


# Create a singleton instance
filter_manager = FilterManager() 