from builtins import filter as filter_
from builtins import map as map_
from typing import Annotated, Any, Literal

from tracecat.expressions.common import build_safe_lambda, eval_jsonpath
from typing_extensions import Doc

from tracecat_registry import ActionIsInterfaceError, registry


@registry.register(
    default_title="Reshape",
    description="Reshapes the input value to the output. You can use this to reshape a JSON-like structure into another easier to manipulate JSON object.",
    display_group="Data Transform",
    namespace="core.transform",
)
def reshape(
    value: Annotated[
        Any | list[Any] | dict[str, Any],
        Doc("The value to reshape"),
    ],
) -> Any:
    return value


@registry.register(
    default_title="Filter",
    description="Filter a collection using a Python lambda function.",
    display_group="Data Transform",
    namespace="core.transform",
)
def filter(
    items: Annotated[
        list[Any],
        Doc("Items to filter."),
    ],
    python_lambda: Annotated[
        str,
        Doc(
            'Filter condition as a Python lambda expression (e.g. `"lambda x: x > 2"`).'
        ),
    ],
) -> Any:
    fn = build_safe_lambda(python_lambda)
    return list(filter_(fn, items))


@registry.register(
    default_title="Is in",
    description="Filters items in a list based on whether they are in a collection.",
    display_group="Data Transform",
    namespace="core.transform",
)
def is_in(
    items: Annotated[
        list[Any],
        Doc("Items to filter."),
    ],
    collection: Annotated[
        list[Any],
        Doc("Collection of hashable items to check against."),
    ],
    python_lambda: Annotated[
        str | None,
        Doc(
            "Python lambda applied to each item before checking membership (e.g. `\"lambda x: x.get('name')\"`). Similar to `key` in the Python `sorted` function."
        ),
    ] = None,
) -> list[Any]:
    col_set = set(collection)
    if python_lambda:
        fn = build_safe_lambda(python_lambda)
        result = [item for item in items if fn(item) in col_set]
    else:
        result = [item for item in items if item in col_set]
    return result


@registry.register(
    default_title="Not in",
    description="Filters items in a list based on whether they are not in a collection.",
    display_group="Data Transform",
    namespace="core.transform",
)
def not_in(
    items: Annotated[
        list[Any],
        Doc("Items to filter."),
    ],
    collection: Annotated[
        list[Any],
        Doc("Collection of hashable items to check against."),
    ],
    python_lambda: Annotated[
        str | None,
        Doc(
            "Python lambda applied to each item before checking membership (e.g. `\"lambda x: x.get('name')\"`). Similar to `key` in the Python `sorted` function."
        ),
    ] = None,
) -> list[Any]:
    col_set = set(collection)
    if python_lambda:
        fn = build_safe_lambda(python_lambda)
        result = [item for item in items if fn(item) not in col_set]
    else:
        result = [item for item in items if item not in col_set]
    return result


@registry.register(
    default_title="Deduplicate",
    description="Deduplicate list of JSON objects given a list of keys.",
    display_group="Data Transform",
    namespace="core.transform",
)
def deduplicate(
    items: Annotated[list[dict[str, Any]], Doc("List of JSON objects to deduplicate.")],
    keys: Annotated[
        list[str],
        Doc(
            "List of keys to deduplicate by. Supports dot notation for nested keys (e.g. `['user.id']`)."
        ),
    ],
) -> list[dict[str, Any]]:
    if not items:
        return []

    def get_nested_values(item: dict[str, Any], keys: list[str]) -> tuple[Any, ...]:
        values = []
        for key in keys:
            # Convert dot notation to jsonpath format
            jsonpath_expr = "$." + key
            value = eval_jsonpath(jsonpath_expr, item, strict=True)
            values.append(value)
        return tuple(values)

    seen = {}
    for item in items:
        key = get_nested_values(item, keys)
        if key in seen:
            seen[key].update(item)
        else:
            seen[key] = item.copy()

    return list(seen.values())


@registry.register(
    default_title="Apply",
    description="Apply a Python lambda function to a value.",
    display_group="Data Transform",
    namespace="core.transform",
)
def apply(
    value: Annotated[
        Any,
        Doc("Value to apply the lambda function to."),
    ],
    python_lambda: Annotated[
        str,
        Doc("Python lambda function as a string (e.g. `\"lambda x: x.get('name')\"`)."),
    ],
) -> Any:
    fn = build_safe_lambda(python_lambda)
    return fn(value)


@registry.register(
    default_title="Map",
    description="Map a Python lambda function to each item in a list.",
    display_group="Data Transform",
    namespace="core.transform",
)
def map(
    items: Annotated[
        list[Any],
        Doc("Items to map the lambda function to."),
    ],
    python_lambda: Annotated[
        str,
        Doc("Python lambda function as a string (e.g. `\"lambda x: x.get('name')\"`)."),
    ],
) -> list[Any]:
    fn = build_safe_lambda(python_lambda)
    return list(map_(fn, items))


@registry.register(
    default_title="Compact",
    description="Remove all null or empty string values from a list.",
    display_group="Data Transform",
    namespace="core.transform",
)
def compact(
    items: Annotated[list[Any], Doc("List of items to compact.")],
) -> list[Any]:
    return [item for item in items if item is not None and item != ""]


@registry.register(
    default_title="Scatter",
    description=(
        "Transform a collection of items into parallel execution streams, "
        "where each item is processed independently."
    ),
    display_group="Data Transform",
    namespace="core.transform",
)
def scatter(
    collection: Annotated[
        str | list[Any],
        Doc(
            "The collection to scatter. Each item in the collection will be"
            " processed independently in its own execution stream. This should"
            " be a JSONPath expression to a collection or a list of items."
        ),
    ],
) -> Any:
    raise ActionIsInterfaceError()


@registry.register(
    default_title="Gather",
    description="Collect the results of a list of execution streams into a single list.",
    display_group="Data Transform",
    namespace="core.transform",
)
def gather(
    items: Annotated[
        str,
        Doc(
            "The JSONPath expression referencing the item to gather in the current execution stream."
        ),
    ],
    drop_nulls: Annotated[
        bool,
        Doc(
            "Whether to drop null values from the final result. If True, any null values encountered during the gather operation will be omitted from the output list."
        ),
    ] = False,
    error_strategy: Annotated[
        Literal["partition", "include", "drop"],
        Doc(
            "Controls how errors are handled when gathering. "
            '"partition" puts successful results in `.result` and errors in `.error`. '
            '"include" puts errors in `.result` as JSON objects. '
            '"drop" removes errors from `.result`.'
        ),
    ] = "partition",
) -> list[Any]:
    raise ActionIsInterfaceError()
