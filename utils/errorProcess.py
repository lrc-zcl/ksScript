from functools import wraps


def raise_error(inner_func):
    wraps(inner_func)

    def wrapper(*args, **kwargs):
        try:
            inner_reslt = inner_func(*args, **kwargs)
            return inner_reslt
        except Exception as error:
            raise Exception(inner_func.__doc__ + str(error))

    return wrapper



