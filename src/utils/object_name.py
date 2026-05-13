def get_full_class_name(cls: type) -> str:
    """
    Returns the fully qualified name of a class, including its module and qualname.

    Args:
        cls (type): The class for which to retrieve the full name.

    Returns:
        str: The full class name in the format `{module}.{qualname}`.

    Example:
        >>> class MyClass: pass
        >>> get_full_class_name(MyClass)
        '__main__.MyClass'
    """
    return f"{cls.__module__}.{cls.__qualname__}"
