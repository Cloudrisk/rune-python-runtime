'''Utility functions (runtime) for rune models.'''
from __future__ import annotations
import keyword
from enum import Enum
from typing import Callable, Any

__all__ = [
    'if_cond', 'if_cond_fn', 'Multiprop', 'any_elements', 'get_only_element',
    'rune_filter', 'all_elements', 'contains', 'disjoint', 'join',
    'flatten_list', 'rune_resolve_attr', 'rune_count', 'rune_attr_exists',
    '_get_rune_object', 'rune_set_attr', 'rune_add_attr', 'check_cardinality',
    'rune_str'
]


def if_cond(ifexpr, thenexpr: str, elseexpr: str, obj: object):
    '''A helper to return the value of the ternary operator.'''
    expr = thenexpr if ifexpr else elseexpr
    return eval(expr, globals(), {'self': obj})  # pylint: disable=eval-used


def if_cond_fn(ifexpr, thenexpr: Callable, elseexpr: Callable) -> Any:
    ''' A helper to return the value of the ternary operator
        (functional version).
    '''
    expr = thenexpr if ifexpr else elseexpr
    return expr()


def _to_list(obj) -> list | tuple:
    if isinstance(obj, (list, tuple)):
        return obj
    return (obj, )


def mangle_name(attrib: str) -> str:
    ''' Mangle any attrib that is a Python keyword, is a Python soft keyword
        or begins with _
    '''
    if (keyword.iskeyword(attrib) or keyword.issoftkeyword(attrib)
            or attrib.startswith('_')):
        return 'rune_attr_' + attrib
    return attrib


def rune_resolve_attr(obj: Any | None, attrib: str) -> Any | list[Any] | None:
    ''' rune semantics compliant attribute resolver.
        Lists and mangled attributes are treated as defined by
        the rune definition (list flattening).
    '''
    if obj is None:
        return None
    if isinstance(obj, (list, tuple)):
        res = [
            item for elem in obj
            for item in _to_list(rune_resolve_attr(elem, attrib))
            if item is not None
        ]
        return res if res else None
    attrib = mangle_name(attrib)
    return getattr(obj, attrib, None)


def rune_count(obj: Any | None) -> int:
    '''Implements the lose count semantics of the rune DSL'''
    if not obj:
        return 0
    try:
        return len(obj)
    except TypeError:
        return 1


def rune_attr_exists(val: Any) -> bool:
    '''Implements the rune semantics of property existence'''
    if val is None or val == []:
        return False
    return True


def rune_str(x: Any) -> str:
    '''Returns a rune conform string representation'''
    if isinstance(x, Enum):
        x = x.value
    return str(x)


def _get_rune_object(base_model: str, attribute: str, value: Any) -> Any:
    model_class = globals()[base_model]
    instance_kwargs = {attribute: value}
    instance = model_class(**instance_kwargs)
    return instance


class Multiprop(list):
    ''' A class allowing for dot access to a attribute of all elements of a
        list.
    '''

    def __getattr__(self, attr):
        # return multiprop(getattr(x, attr) for x in self)
        res = Multiprop()
        for x in self:
            if isinstance(x, Multiprop):
                res.extend(x.__getattr__(attr))
            else:
                res.append(getattr(x, attr))
        return res


def _ntoz(v):
    '''Support the lose rune treatment of None in comparisons'''
    if v is None:
        return 0
    return v


_cmp = {
    '=': lambda x, y: _ntoz(x) == _ntoz(y),
    '<>': lambda x, y: _ntoz(x) != _ntoz(y),
    '>=': lambda x, y: _ntoz(x) >= _ntoz(y),
    '<=': lambda x, y: _ntoz(x) <= _ntoz(y),
    '>': lambda x, y: _ntoz(x) > _ntoz(y),
    '<': lambda x, y: _ntoz(x) < _ntoz(y)
}


def all_elements(lhs, op, rhs) -> bool:
    '''Checks that two lists have the same elements'''
    cmp = _cmp[op]
    op1 = _to_list(lhs)
    op2 = _to_list(rhs)

    return all(cmp(el1, el2) for el1 in op1 for el2 in op2)


def disjoint(op1, op2):
    '''Checks if two lists have no common elements'''
    op1 = set(_to_list(op1))
    op2 = set(_to_list(op2))
    return not op1 & op2


def contains(op1, op2):
    ''' Checks if op2 is contained in op1
        (e.g. every element of op2 is in op1)
    '''
    op1 = set(_to_list(op1))
    op2 = set(_to_list(op2))

    return op2.issubset(op1)


def join(lst, sep=''):
    ''' Joins the string representation of the list elements, optionally
        separated.
    '''
    return sep.join([str(el) for el in lst])


def any_elements(lhs, op, rhs) -> bool:
    '''Checks if to lists have any common element(s)'''
    cmp = _cmp[op]
    op1 = _to_list(lhs)
    op2 = _to_list(rhs)

    return any(cmp(el1, el2) for el1 in op1 for el2 in op2)


def check_cardinality(prop, inf: int, sup: int | None = None) -> bool:
    ''' If the supremum is not supplied (e.g. is None), the property is
        unbounded (e.g. it corresponds to (x..*) in rune).
    '''
    if not prop:
        prop_card = 0
    elif isinstance(prop, (list, tuple)):
        prop_card = len(prop)
    else:
        prop_card = 1

    if sup is None:
        sup = prop_card

    return inf <= prop_card <= sup


def get_only_element(collection):
    ''' Returns the single element of a collection, if the list contains more
        more than one element or is empty, None is returned.
    '''
    if isinstance(collection, (list, tuple)) and len(collection) == 1:
        return collection[0]
    return None


def flatten_list(nested_list):
    '''flattens the list of lists (no-recursively)'''
    return [item for sublist in nested_list for item in sublist]


def rune_filter(items, filter_func, item_name='item'):
    """
    Filters a list of items based on a specified filtering criteria provided as
    a boolean lambda function.

    :param items: List of items to be filtered.
    :param filter_func: A lambda function representing the boolean expression
        for filtering.
    :param item_name: The name used to refer to each item in the boolean
        expression.
    :return: Filtered list.
    """
    return [item for item in items if filter_func(locals()[item_name])]


def rune_set_attr(obj: Any, path: str, value: Any) -> None:
    """
    Sets an attribute of a rune model object to a specified value using a
    path.

    Parameters:
    obj (Any): The object whose attribute is to be set.
    path (str): The path to the attribute, with components separated by '->'.
    value (Any): The value to set the attribute to.

    Raises:
    ValueError: If the object or attribute at any level in the path is None.
    AttributeError: If an invalid attribute path is provided.
    """
    if obj is None:
        raise ValueError(
            "Cannot set attribute on a None object in set_rune_attr.")

    path_components = path.split('->')  # Use '->' for splitting the path
    parent_obj = obj

    # Iterate through the path components, except the last one
    for attrib in path_components[:-1]:
        parent_obj = rune_resolve_attr(parent_obj, attrib)
        if parent_obj is None:
            raise ValueError(
                f"Attribute '{attrib}' in the path is None, cannot "
                "proceed to set value.")

    # Set the value to the last attribute in the path
    final_attr = path_components[-1]
    if hasattr(parent_obj, final_attr):
        setattr(parent_obj, final_attr, value)
    else:
        raise AttributeError(f"Invalid attribute '{final_attr}' for object of "
                             f"type {type(parent_obj).__name__}")


def rune_add_attr(obj: Any, attrib: str, value: Any) -> None:
    """
    Adds a value to a list-like attribute of a rune model object.

    Parameters:
    obj (Any): The object whose attribute is to be modified.
    attrib (str): The list-like attribute to add the value to.
    value (Any): The value to add to the attribute.
    """
    if obj is not None:
        if hasattr(obj, attrib):
            current_attr = getattr(obj, attrib)
            if isinstance(current_attr, list):
                current_attr.append(value)
            else:
                raise TypeError(f"Attribute {attrib} is not list-like.")
        else:
            setattr(obj, attrib, [value])
    else:
        raise ValueError("Object for add_rune_attr cannot be None.")

# EOF
