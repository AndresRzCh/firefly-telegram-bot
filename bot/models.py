class FireFlyBotException(Exception):
    pass

class CategoryError(FireFlyBotException):
    pass

class SourceError(FireFlyBotException):
    pass

class DestinationError(FireFlyBotException):
    pass

class StartError(FireFlyBotException):
    pass

def safe_math_eval(string):
    """
    Safely evaluate a mathematical expression contained in a string.

    :param str string: The input string containing the mathematical expression
    :raises Exception: If the input string contains unsafe characters
    :return: The result of the evaluated mathematical expression
    :rtype: float or int
    """
    allowed_chars = "0123456789+-*(). /"
    for char in string:
        if char not in allowed_chars:
            raise Exception("Unsafe eval")
    return eval(string)
