import inspect
import json
import types
import functools
import logging
import pandas as pd
import numpy as np
import pymongo
import pathlib
import datetime as dt


# ObjectEncoder class definition (keeping original intact)
class ObjectEncoder(json.JSONEncoder):
    """
    y (copyRight)
        2016.5.15, 10.25 - 26, 11.10
        2017.3.18, 5.11, 6.6, 6.21, 9.22, 9.25, 9.28
        2018.5.4, 12.29
        2019.9.30*

    References
    ----------
    [1] https://docs.python.org/3/library/json.html

    Notes
    -----
    [1] To use a custom JSONDecoder subclass, specify it with the cls kwarg; otherwise JSONDecoder is used.
        Additional keyword arguments will be passed to the constructor of the class.
    """

    skip_types = (
        classmethod, staticmethod, property,  # 2019.7.19
        types.BuiltinFunctionType, types.BuiltinMethodType,  # 2017.6.21
        pd.Series, pd.DataFrame, pd.Index,  # 2016.10.25, 2019.8.24
        functools.partial,  # 2017.7.20
        logging.Logger, logging.RootLogger,  # 2017.9.28
    )

    def __init__(self, *args, **kwargs):
        """
        y,  2018.12.29 - 30
            2019.9.30
        """
        skip_types = list(kwargs.pop('skip_types', ()))  # () is tuple(), 2018.12.30; type(()) is tuple, 2019.9.30
        self.skip_types = tuple(set(list(self.skip_types) + skip_types))
        super().__init__(*args, **kwargs)

    def default(self, obj):
        """
        y,  2016.5.15 ~, 5.31, 10.26
            2017.5.11, 6.6, 6.21
            2018.5.4
            2019.1.22, 1.24, 7.19, 8.27, 9.30
            2020.1.24, 4.22, 4.28 - 29, 11.17

        Note
        ----
        # override super().default()
        """

        def _is_mongo_object(obj):
            """ y, 2019.8.27 """
            return isinstance(obj, (pymongo.mongo_client.MongoClient, pymongo.database.Database,
                                    pymongo.collection.Collection))

        # 2019.9.30
        if isinstance(obj, self.skip_types):
            return None
        # 2017.5.11
        # 2018.5.4
        elif isinstance(obj, (type, set, frozenset)):
            return str(obj)
        # 2016.5.31, 10.26
        # 2019.8.27
        # 2020.4.22, 4.28 - 29
        elif hasattr(obj, 'isoformat'):  # datetime like
            if pd.isnull(obj):
                return None
            elif not _is_mongo_object(obj):
                return obj.isoformat()
            else:
                return str(obj)
        # 2017.6.6
        elif isinstance(obj, (np.int_, np.intc, np.intp, np.int8, np.int16, np.int32, np.int64,
                              np.uint8, np.uint16, np.uint32, np.uint64)):
            # np.issubdtype(int, np.integer)
            return int(obj)
        # 2017.6.6
        elif isinstance(obj, (np.float_, np.float16, np.float32, np.float64)):
            # np.issubdtype(int, np.float64)
            return float(obj)
        # 2020.4.28
        elif isinstance(obj, (np.ndarray,)):
            return obj.tolist()
        # 2017.6.21
        # return string to avoid 'circular reference' error coming from builtin function in list or dict
        elif isinstance(obj, (types.BuiltinFunctionType, types.BuiltinMethodType)):
            return str(obj)
        # 2020.11.17
        elif isinstance(obj, (types.SimpleNamespace,)):
            return vars(obj)  # Note: return obj.__dict__, 2020.11.28
        # 2019.1.22
        elif isinstance(obj, pathlib.Path):
            return str(obj)
        # 2020.1.24
        elif isinstance(obj, dt.timezone):
            return str(obj)
        # 2016.5.15 ~
        elif hasattr(obj, "__dict__"):
            a_dict = dict()
            obj_class_dict = dict(obj.__class__.__dict__)  # 2016.10.25
            obj_class_dict.update(obj.__dict__)  # 2017.3.18
            for key in obj_class_dict.keys():  # 2016.10.25, 2017.3.18
                value = getattr(obj, key)
                if (key.startswith('__')  # to keep public attributes only
                    and key.endswith('__')) or callable(value):
                    continue
                a_dict[key] = value
            return a_dict
        else:
            return super().default(obj)


# Sanity Check Functions
def check_class_structure():
    """Check class structure and member functions"""
    print("=== ObjectEncoder Class Structure Check ===")

    # Basic class information
    print(f"Class name: {ObjectEncoder.__name__}")
    print(f"Parent classes: {ObjectEncoder.__bases__}")
    print(f"MRO: {[cls.__name__ for cls in ObjectEncoder.__mro__]}")

    # Check member functions and attributes
    print("\n--- Member Functions and Attributes ---")
    members = inspect.getmembers(ObjectEncoder)
    for name, member in members:
        if not name.startswith('_') or name in ['__init__']:
            member_type = type(member).__name__
            print(f"  {name}: {member_type}")

            if inspect.ismethod(member) or inspect.isfunction(member):
                try:
                    sig = inspect.signature(member)
                    print(f"    Signature: {sig}")
                except:
                    print(f"    Signature: Unable to determine")


def check_class_attributes():
    """Check class attributes"""
    print("\n=== Class Attributes Check ===")

    # Check skip_types
    print(f"skip_types (class level): {ObjectEncoder.skip_types}")
    print(f"skip_types type: {type(ObjectEncoder.skip_types)}")
    print(f"skip_types length: {len(ObjectEncoder.skip_types)}")

    # Check each skip_type
    print("\n--- skip_types Details ---")
    for i, skip_type in enumerate(ObjectEncoder.skip_types):
        print(f"  [{i}] {skip_type} ({type(skip_type)})")


def check_instance_creation():
    """Check instance creation and initialization"""
    print("\n=== Instance Creation Check ===")

    try:
        # Basic instance creation
        encoder1 = ObjectEncoder()
        print("✓ Basic instance creation successful")
        print(f"  Instance skip_types: {encoder1.skip_types}")

        # Custom skip_types instance creation
        custom_skip = [str, int]
        encoder2 = ObjectEncoder(skip_types=custom_skip)
        print("✓ Custom skip_types instance creation successful")
        print(f"  Instance skip_types: {encoder2.skip_types}")

        # Check skip_types merging
        original_count = len(ObjectEncoder.skip_types)
        merged_count = len(encoder2.skip_types)
        print(f"  Original skip_types count: {original_count}")
        print(f"  Merged skip_types count: {merged_count}")

    except Exception as e:
        print(f"✗ Instance creation failed: {e}")


def check_method_functionality():
    """Check method functionality"""
    print("\n=== Method Functionality Check ===")

    try:
        encoder = ObjectEncoder()

        # Check default method
        print("--- default Method Test ---")

        # Test various object types
        test_cases = [
            ("string", "test_string"),
            ("integer", 42),
            ("list", [1, 2, 3]),
            ("dict", {"key": "value"}),
            ("set", {1, 2, 3}),
            ("numpy int", np.int32(10)),
            ("numpy float", np.float64(3.14)),
            ("numpy array", np.array([1, 2, 3])),
            ("pathlib Path", pathlib.Path("/test/path")),
            ("datetime", dt.datetime.now()),
            ("timezone", dt.timezone.utc),
        ]

        for test_name, test_obj in test_cases:
            try:
                result = encoder.default(test_obj)
                print(f"  ✓ {test_name}: {type(result).__name__} - {str(result)[:50]}...")
            except TypeError as e:
                print(f"  ○ {test_name}: TypeError (expected for some types) - {e}")
            except Exception as e:
                print(f"  ✗ {test_name}: Unexpected error - {e}")

    except Exception as e:
        print(f"✗ Method test failed: {e}")


def check_inheritance():
    """Check inheritance relationship"""
    print("\n=== Inheritance Relationship Check ===")

    encoder = ObjectEncoder()

    print(f"isinstance(encoder, json.JSONEncoder): {isinstance(encoder, json.JSONEncoder)}")
    print(f"isinstance(encoder, ObjectEncoder): {isinstance(encoder, ObjectEncoder)}")

    # Check parent class methods
    parent_methods = [method for method in dir(json.JSONEncoder) if not method.startswith('_')]
    print(f"Parent class public methods: {parent_methods}")

    # Check overridden methods
    overridden = []
    for method_name in parent_methods:
        if hasattr(ObjectEncoder, method_name):
            parent_method = getattr(json.JSONEncoder, method_name)
            child_method = getattr(ObjectEncoder, method_name)
            if parent_method != child_method:
                overridden.append(method_name)

    print(f"Overridden methods: {overridden}")


def check_json_encoding():
    """Check JSON encoding functionality"""
    print("\n=== JSON Encoding Functionality Check ===")

    try:
        encoder = ObjectEncoder()

        # Test JSON encoding with various objects
        test_objects = {
            "simple_dict": {"name": "test", "value": 42},
            "with_numpy": {"array": np.array([1, 2, 3]), "int": np.int32(10)},
            "with_datetime": {"now": dt.datetime.now(), "tz": dt.timezone.utc},
            "with_path": {"path": pathlib.Path("/test")},
            "with_set": {"data": {1, 2, 3}},
        }

        for test_name, test_obj in test_objects.items():
            try:
                json_str = json.dumps(test_obj, cls=ObjectEncoder, indent=2)
                print(f"  ✓ {test_name}: Successfully encoded")
                print(f"    Length: {len(json_str)} characters")
            except Exception as e:
                print(f"  ✗ {test_name}: Encoding failed - {e}")

    except Exception as e:
        print(f"✗ JSON encoding test failed: {e}")


def run_sanity_check():
    """Run complete sanity check"""
    print("ObjectEncoder Class Sanity Check Started\n")

    check_class_structure()
    check_class_attributes()
    check_instance_creation()
    check_method_functionality()
    check_inheritance()
    check_json_encoding()

    print("\n=== Sanity Check Completed ===")


# Execute
if __name__ == "__main__":
    run_sanity_check()
