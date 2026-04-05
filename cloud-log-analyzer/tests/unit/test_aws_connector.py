# src/tests/unit/test_aws_connector.py

import json
import pytest
from src.data_collection.aws_connector import AWSConnector

# ─── Fixtures ────────────────────────────────────────────────
# A fixture is a reusable setup block — pytest injects it automatically

@pytest.fixture
def connector():
    """Returns a fresh AWSConnector instance for each test"""
    return AWSConnector()

@pytest.fixture
def valid_json_file(tmp_path):
    """Creates a temporary valid CloudTrail JSON file"""
    data = {
        "Records": [
            {
                "eventName": "ConsoleLogin",
                "eventSource": "signin.amazonaws.com",
                "sourceIPAddress": "1.2.3.4",
                "userIdentity": {"type": "IAMUser", "userName": "alice"},
                "eventTime": "2026-01-25T10:00:00Z"
            },
            {
                "eventName": "CreateUser",
                "eventSource": "iam.amazonaws.com",
                "sourceIPAddress": "5.6.7.8",
                "userIdentity": {"type": "IAMUser", "userName": "bob"},
                "eventTime": "2026-01-25T11:00:00Z"
            }
        ]
    }
    # tmp_path is a pytest built-in — creates a temp folder auto-deleted after test
    file = tmp_path / "sample_cloudtrail.json"
    file.write_text(json.dumps(data))
    return str(file)

@pytest.fixture
def empty_json_file(tmp_path):
    """Creates a temporary JSON file with no Records"""
    data = {"Records": []}
    file = tmp_path / "empty_cloudtrail.json"
    file.write_text(json.dumps(data))
    return str(file)

@pytest.fixture
def corrupted_json_file(tmp_path):
    """Creates a temporary file with invalid JSON content"""
    file = tmp_path / "corrupted.json"
    file.write_text("this is not valid json {{{{")
    return str(file)


# ─── Tests : _load_from_file() ───────────────────────────────

class TestLoadFromFile:

    def test_returns_list_of_events_on_valid_file(self, connector, valid_json_file):
        """Should return a list of dicts when file is valid"""
        # Arrange — valid_json_file fixture already prepared

        # Act
        result = connector._load_from_file(valid_json_file)

        # Assert
        assert isinstance(result, list)
        assert len(result) == 2

    def test_returns_correct_event_fields(self, connector, valid_json_file):
        """Each event should contain expected CloudTrail fields"""
        # Arrange — valid file with known content

        # Act
        result = connector._load_from_file(valid_json_file)

        # Assert — first event must have these keys
        first_event = result[0]
        assert "eventName" in first_event
        assert "eventSource" in first_event
        assert "sourceIPAddress" in first_event
        assert "eventTime" in first_event

    def test_returns_empty_list_on_missing_file(self, connector):
        """Should return empty list when file does not exist"""
        # Arrange — path that does not exist
        fake_path = "data/does_not_exist.json"

        # Act
        result = connector._load_from_file(fake_path)

        # Assert — never crash, always return list
        assert result == []

    def test_returns_empty_list_on_corrupted_json(self, connector, corrupted_json_file):
        """Should return empty list when JSON is invalid"""
        # Arrange — corrupted file fixture

        # Act
        result = connector._load_from_file(corrupted_json_file)

        # Assert
        assert result == []

    def test_returns_empty_list_when_records_key_missing(self, connector, tmp_path):
        """Should return empty list when Records key is absent"""
        # Arrange — JSON without Records key
        data = {"SomethingElse": []}
        file = tmp_path / "no_records.json"
        file.write_text(json.dumps(data))

        # Act
        result = connector._load_from_file(str(file))

        # Assert
        assert result == []

    def test_returns_empty_list_on_empty_records(self, connector, empty_json_file):
        """Should return empty list when Records array is empty"""
        # Arrange — empty Records fixture

        # Act
        result = connector._load_from_file(empty_json_file)

        # Assert
        assert result == []


# ─── Tests : fetch_logs() routing ────────────────────────────

class TestFetchLogsRouting:

    def test_fetch_logs_file_source_returns_list(self, connector, valid_json_file):
        """fetch_logs with source=file should call _load_from_file"""
        # Arrange
        # Act
        result = connector.fetch_logs(source="file", file_path=valid_json_file)

        # Assert
        assert isinstance(result, list)
        assert len(result) == 2

    def test_fetch_logs_unknown_source_returns_empty_list(self, connector):
        """fetch_logs with unknown source should return empty list"""
        # Arrange — invalid source name

        # Act
        result = connector.fetch_logs(source="azure")

        # Assert
        assert result == []

    def test_fetch_logs_aws_without_connect_returns_empty_list(self, connector):
        """fetch_logs with source=aws before connect() should return empty list"""
        # Arrange — connector not connected (client is None)
        from datetime import datetime, timedelta
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=1)

        # Act
        result = connector.fetch_logs(
            source="aws",
            start_time=start_time,
            end_time=end_time
        )

        # Assert — should fail gracefully, not crash
        assert result == []