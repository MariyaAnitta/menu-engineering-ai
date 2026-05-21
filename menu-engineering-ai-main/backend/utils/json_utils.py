import numpy as np

def convert_numpy_types(data):
    """
    Recursively converts NumPy and Pandas scalar/array types into standard Python types
    to ensure Firestore and JSON serialization compatibility.
    """
    if isinstance(data, dict):
        return {
            key: convert_numpy_types(value)
            for key, value in data.items()
        }

    elif isinstance(data, list):
        return [
            convert_numpy_types(item)
            for item in data
        ]

    elif isinstance(data, tuple):
        return tuple(
            convert_numpy_types(item)
            for item in data
        )

    elif isinstance(data, np.integer):
        return int(data)

    elif isinstance(data, np.floating):
        return float(data)

    elif isinstance(data, np.bool_):
        return bool(data)

    elif isinstance(data, np.ndarray):
        return convert_numpy_types(data.tolist())

    return data
