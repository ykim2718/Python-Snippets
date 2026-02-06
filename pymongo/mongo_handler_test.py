# mongo_handler_test.py
"""
MongoHandler Independent Test Snippet
Custom handler test for saving logs to MongoDB
"""

import logging
import os
import sys
from datetime import datetime
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError


class MongoHandler(logging.Handler):
    """Custom logging handler that saves logs to MongoDB"""

    def __init__(self, database_name, collection_name, host='localhost', port=27017,
                 username=None, password=None, log_name=None, enable_count=True):
        """
        Initialize MongoHandler

        Args:
            database_name (str): MongoDB database name
            collection_name (str): Collection name
            host (str): MongoDB host
            port (int): MongoDB port
            username (str): Username (optional)
            password (str): Password (optional)
            log_name (str): Log identifier
            enable_count (bool): Enable count feature
        """
        super().__init__()

        # Get authentication info from environment variables (security enhancement)
        self.username = username or os.getenv('MONGO_USERNAME')
        self.password = password or os.getenv('MONGO_PASSWORD')
        self.host = host
        self.port = port
        self.database_name = database_name
        self.collection_name = collection_name
        self.log_name = log_name or 'default_logger'
        self.enable_count = enable_count

        # Connect to MongoDB
        self._connect_to_mongodb()

    def _connect_to_mongodb(self):
        """Setup MongoDB connection"""
        try:
            # Create connection string
            if self.username and self.password:
                connection_string = f"mongodb://{self.username}:{self.password}@{self.host}:{self.port}/"
            else:
                connection_string = f"mongodb://{self.host}:{self.port}/"

            # Create MongoDB client
            self.client = MongoClient(
                connection_string,
                serverSelectionTimeoutMS=5000  # 5 second timeout
            )

            # Setup database and collection
            self.db = self.client[self.database_name]
            self.collection = self.db[self.collection_name]

            # Test connection
            self.client.admin.command('ping')
            print(f"✅ MongoDB connection successful: {self.host}:{self.port}/{self.database_name}")

        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            print(f"❌ MongoDB connection failed: {e}")
            raise
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            raise

    def emit(self, record):
        """Save log record to MongoDB"""
        try:
            # Create log entry
            log_entry = self._create_log_entry(record)

            # Insert into MongoDB
            result = self.collection.insert_one(log_entry)

            # Update count (if enabled)
            if self.enable_count:
                self._update_count()

        except Exception as e:
            # Output to console if log saving fails
            print(f"⚠️ Log saving failed: {e}")
            self.handleError(record)

    def _create_log_entry(self, record):
        """Convert log record to MongoDB document"""
        log_entry = {
            'timestamp': datetime.now(),
            'level': record.levelname,
            'logger_name': record.name,
            'message': self.format(record),
            'module': record.module,
            'filename': record.filename,
            'line_number': record.lineno,
            'function_name': record.funcName,
            'process_id': record.process,
            'thread_id': record.thread,
            'log_source': self.log_name
        }

        # Add exception information
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)

        # Include additional information if available
        if hasattr(record, '__dict__'):
            for key, value in record.__dict__.items():
                if key not in ['name', 'msg', 'args', 'levelname', 'levelno',
                               'pathname', 'filename', 'module', 'lineno',
                               'funcName', 'created', 'msecs', 'relativeCreated',
                               'thread', 'threadName', 'processName', 'process',
                               'getMessage', 'exc_info', 'exc_text', 'stack_info']:
                    log_entry[f'extra_{key}'] = value

        return log_entry

    def _update_count(self):
        """Update log count"""
        try:
            self.collection.update_one(
                {'_id': 'log_counter'},
                {'$inc': {'count': 1}, '$set': {'last_updated': datetime.now()}},
                upsert=True
            )
        except Exception as e:
            print(f"⚠️ Count update failed: {e}")

    def get_log_count(self):
        """Return current log count"""
        try:
            counter_doc = self.collection.find_one({'_id': 'log_counter'})
            return counter_doc['count'] if counter_doc else 0
        except Exception as e:
            print(f"⚠️ Count retrieval failed: {e}")
            return 0

    def get_logs(self, level=None, limit=10, sort_desc=True):
        """Retrieve logs"""
        try:
            query = {'_id': {'$ne': 'log_counter'}}
            if level:
                query['level'] = level.upper()

            sort_order = -1 if sort_desc else 1
            cursor = self.collection.find(query).sort('timestamp', sort_order).limit(limit)

            return list(cursor)
        except Exception as e:
            print(f"⚠️ Log retrieval failed: {e}")
            return []

    def clear_logs(self):
        """Delete all logs (except counter)"""
        try:
            result = self.collection.delete_many({'_id': {'$ne': 'log_counter'}})
            print(f"🗑️ {result.deleted_count} logs have been deleted.")
            return result.deleted_count
        except Exception as e:
            print(f"⚠️ Log deletion failed: {e}")
            return 0

    def close(self):
        """Close connection"""
        try:
            if hasattr(self, 'client'):
                self.client.close()
                print("🔌 MongoDB connection has been closed.")
        except Exception as e:
            print(f"⚠️ Error during connection closure: {e}")


def setup_logger(name='test_logger'):
    """Setup test logger"""
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # Remove existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    return logger


def test_basic_logging():
    """Basic logging test"""
    print("\n" + "=" * 50)
    print("🧪 Basic Logging Test")
    print("=" * 50)

    logger = setup_logger('basic_test')

    try:
        # Create MongoHandler
        mongo_handler = MongoHandler(
            database_name='test_logs_db',
            collection_name='basic_logs',
            log_name='basic_test'
        )

        # Setup formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        mongo_handler.setFormatter(formatter)

        # Add handler
        logger.addHandler(mongo_handler)

        # Also add console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        # Generate logs of various levels
        logger.debug("This is a debug message")
        logger.info("This is an info message")
        logger.warning("This is a warning message")
        logger.error("This is an error message")
        logger.critical("This is a critical error message")

        # Display current log count
        count = mongo_handler.get_log_count()
        print(f"📊 Current log count: {count}")

        mongo_handler.close()

    except Exception as e:
        print(f"❌ Basic logging test failed: {e}")


def test_exception_logging():
    """Exception logging test"""
    print("\n" + "=" * 50)
    print("🧪 Exception Logging Test")
    print("=" * 50)

    logger = setup_logger('exception_test')

    try:
        mongo_handler = MongoHandler(
            database_name='test_logs_db',
            collection_name='exception_logs',
            log_name='exception_test'
        )

        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        mongo_handler.setFormatter(formatter)
        logger.addHandler(mongo_handler)

        # Intentionally cause exceptions
        try:
            result = 10 / 0
        except ZeroDivisionError:
            logger.exception("Division by zero exception occurred")

        try:
            undefined_variable = some_undefined_variable
        except NameError:
            logger.exception("Undefined variable reference exception")

        try:
            my_list = [1, 2, 3]
            value = my_list[10]
        except IndexError:
            logger.exception("List index out of range exception")

        mongo_handler.close()

    except Exception as e:
        print(f"❌ Exception logging test failed: {e}")


def test_structured_logging():
    """Structured logging test"""
    print("\n" + "=" * 50)
    print("🧪 Structured Logging Test")
    print("=" * 50)

    logger = setup_logger('structured_test')

    try:
        mongo_handler = MongoHandler(
            database_name='test_logs_db',
            collection_name='structured_logs',
            log_name='structured_test'
        )

        formatter = logging.Formatter('%(message)s')
        mongo_handler.setFormatter(formatter)
        logger.addHandler(mongo_handler)

        # Logging with structured data
        logger.info("User login", extra={
            'user_id': 'user123',
            'ip_address': '192.168.1.100',
            'user_agent': 'Mozilla/5.0...',
            'session_id': 'sess_abc123'
        })

        logger.info("API call", extra={
            'endpoint': '/api/users',
            'method': 'GET',
            'response_time': 150,
            'status_code': 200
        })

        logger.error("Database error", extra={
            'error_code': 'DB_CONNECTION_FAILED',
            'retry_count': 3,
            'last_attempt': datetime.now().isoformat()
        })

        mongo_handler.close()

    except Exception as e:
        print(f"❌ Structured logging test failed: {e}")


def test_log_retrieval():
    """Log retrieval test"""
    print("\n" + "=" * 50)
    print("🧪 Log Retrieval Test")
    print("=" * 50)

    try:
        mongo_handler = MongoHandler(
            database_name='test_logs_db',
            collection_name='basic_logs',
            log_name='retrieval_test'
        )

        # Retrieve recent 5 logs
        recent_logs = mongo_handler.get_logs(limit=5)
        print(f"📋 Recent {len(recent_logs)} logs:")

        for i, log in enumerate(recent_logs, 1):
            timestamp = log.get('timestamp', 'N/A')
            level = log.get('level', 'N/A')
            message = log.get('message', 'N/A')
            print(f"  {i}. [{level}] {timestamp} - {message}")

        # Retrieve only ERROR level logs
        error_logs = mongo_handler.get_logs(level='ERROR', limit=3)
        print(f"\n🚨 {len(error_logs)} ERROR logs:")

        for i, log in enumerate(error_logs, 1):
            timestamp = log.get('timestamp', 'N/A')
            message = log.get('message', 'N/A')
            print(f"  {i}. {timestamp} - {message}")

        mongo_handler.close()

    except Exception as e:
        print(f"❌ Log retrieval test failed: {e}")


def check_mongodb_status():
    """Check MongoDB connection status"""
    print("\n" + "=" * 50)
    print("🔍 MongoDB Connection Status Check")
    print("=" * 50)

    try:
        client = MongoClient('mongodb://localhost:27017/', serverSelectionTimeoutMS=3000)
        client.admin.command('ping')

        print("✅ MongoDB server connection successful")

        # Server information
        server_info = client.server_info()
        print(f"📊 MongoDB version: {server_info.get('version', 'Unknown')}")

        # Database list
        db_names = client.list_database_names()
        print(f"📁 Database list: {db_names}")

        client.close()
        return True

    except Exception as e:
        print(f"❌ MongoDB connection failed: {e}")
        print("\n💡 Solutions:")
        print("1. Check if MongoDB is installed")
        print("2. Check if MongoDB service is running")
        print("3. Check if port 27017 is available")
        print("4. For Docker: docker run -d -p 27017:27017 mongo")
        return False


def cleanup_test_data():
    """Clean up test data"""
    print("\n" + "=" * 50)
    print("🗑️ Test Data Cleanup")
    print("=" * 50)

    collections = ['basic_logs', 'exception_logs', 'structured_logs']

    for collection_name in collections:
        try:
            mongo_handler = MongoHandler(
                database_name='test_logs_db',
                collection_name=collection_name,
                log_name='cleanup'
            )

            deleted_count = mongo_handler.clear_logs()
            print(f"📦 {collection_name}: {deleted_count} logs deleted")

            mongo_handler.close()

        except Exception as e:
            print(f"❌ {collection_name} cleanup failed: {e}")


def main():
    """Main function"""
    print("🚀 MongoHandler Test Snippet")
    print("=" * 60)

    while True:
        print("\n📋 Menu:")
        print("1. Check MongoDB connection")
        print("2. Basic logging test")
        print("3. Exception logging test")
        print("4. Structured logging test")
        print("5. Log retrieval test")
        print("6. Clean up test data")
        print("7. Run all tests")
        print("0. Exit")

        choice = input("\nSelect option (0-7): ").strip()

        if choice == '0':
            print("👋 Exiting program.")
            break
        elif choice == '1':
            check_mongodb_status()
        elif choice == '2':
            if check_mongodb_status():
                test_basic_logging()
        elif choice == '3':
            if check_mongodb_status():
                test_exception_logging()
        elif choice == '4':
            if check_mongodb_status():
                test_structured_logging()
        elif choice == '5':
            if check_mongodb_status():
                test_log_retrieval()
        elif choice == '6':
            if check_mongodb_status():
                cleanup_test_data()
        elif choice == '7':
            if check_mongodb_status():
                test_basic_logging()
                test_exception_logging()
                test_structured_logging()
                test_log_retrieval()
        else:
            print("❌ Invalid selection.")


if __name__ == "__main__":
    main()
