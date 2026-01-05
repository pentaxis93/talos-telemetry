"""Pytest configuration and fixtures for Talos Telemetry tests."""

import os
import shutil
import sys
import tempfile
from pathlib import Path

import pytest

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Use temp directory for test database
TEST_DB_PATH = None
TEST_TELEMETRY_PATH = None


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Set up test environment with temp directories."""
    global TEST_DB_PATH, TEST_TELEMETRY_PATH

    # Create temp directories
    TEST_DB_PATH = Path(tempfile.mkdtemp()) / "test_kuzu"
    TEST_TELEMETRY_PATH = Path(tempfile.mkdtemp()) / "test_telemetry"

    # Set environment variables
    os.environ["TALOS_DB_PATH"] = str(TEST_DB_PATH)
    os.environ["TALOS_TELEMETRY_PATH"] = str(TEST_TELEMETRY_PATH)
    os.environ["TALOS_EMBEDDING_CACHE"] = str(Path(tempfile.mkdtemp()) / "embeddings")

    yield

    # Cleanup
    if TEST_DB_PATH and TEST_DB_PATH.exists():
        shutil.rmtree(TEST_DB_PATH.parent, ignore_errors=True)
    if TEST_TELEMETRY_PATH and TEST_TELEMETRY_PATH.exists():
        shutil.rmtree(TEST_TELEMETRY_PATH.parent, ignore_errors=True)


@pytest.fixture
def fresh_db():
    """Provide a fresh database for each test that needs it."""
    from talos_telemetry.db.connection import close_connection, get_connection, init_database
    from talos_telemetry.db.kuzu_schema import deploy_schema
    from talos_telemetry.db.seed import seed_reference_data

    # Close any existing connection
    close_connection()

    # Remove existing test db
    global TEST_DB_PATH
    if TEST_DB_PATH and TEST_DB_PATH.exists():
        shutil.rmtree(TEST_DB_PATH, ignore_errors=True)

    # Initialize fresh db
    init_database()
    deploy_schema()
    seed_reference_data()

    yield get_connection()

    # Cleanup
    close_connection()


@pytest.fixture
def fresh_telemetry():
    """Provide a fresh telemetry sink for each test."""
    from talos_telemetry.telemetry.sink import TelemetrySink

    # Create new temp directory for this test
    test_path = Path(tempfile.mkdtemp()) / "telemetry"
    sink = TelemetrySink(test_path)

    yield sink

    # Cleanup
    shutil.rmtree(test_path.parent, ignore_errors=True)
