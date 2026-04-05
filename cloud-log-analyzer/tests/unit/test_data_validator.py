# src/tests/unit/test_data_validator.py

import pytest
import pandas as pd
import numpy as np
from src.data_processing.data_validator import DataValidator


# ─── Fixtures ────────────────────────────────────────────────

@pytest.fixture
def validator():
    """Returns a fresh DataValidator instance for each test"""
    return DataValidator()

@pytest.fixture
def valid_dataframe():
    """Clean DataFrame with all required columns and valid data"""
    return pd.DataFrame([
        {
            "eventTime":       pd.Timestamp("2026-01-25T10:00:00Z"),
            "eventName":       "ConsoleLogin",
            "eventSource":     "signin.amazonaws.com",
            "sourceIPAddress": "1.2.3.4",
            "userName":        "alice"
        },
        {
            "eventTime":       pd.Timestamp("2026-01-25T11:00:00Z"),
            "eventName":       "CreateUser",
            "eventSource":     "iam.amazonaws.com",
            "sourceIPAddress": "5.6.7.8",
            "userName":        "bob"
        },
        {
            "eventTime":       pd.Timestamp("2026-01-25T12:00:00Z"),
            "eventName":       "AssumeRole",
            "eventSource":     "sts.amazonaws.com",
            "sourceIPAddress": "unknown",
            "userName":        "unknown"
        }
    ])

@pytest.fixture
def dataframe_with_nat():
    """DataFrame containing NaT values in eventTime column"""
    return pd.DataFrame([
        {
            "eventTime":       pd.Timestamp("2026-01-25T10:00:00Z"),
            "eventName":       "ConsoleLogin",
            "eventSource":     "signin.amazonaws.com",
            "sourceIPAddress": "1.2.3.4",
            "userName":        "alice"
        },
        {
            "eventTime":       pd.NaT,   # invalid timestamp — must be removed
            "eventName":       "CreateUser",
            "eventSource":     "iam.amazonaws.com",
            "sourceIPAddress": "5.6.7.8",
            "userName":        "bob"
        }
    ])

@pytest.fixture
def dataframe_with_empty_eventname():
    """DataFrame containing empty string in eventName column"""
    return pd.DataFrame([
        {
            "eventTime":       pd.Timestamp("2026-01-25T10:00:00Z"),
            "eventName":       "ConsoleLogin",
            "eventSource":     "signin.amazonaws.com",
            "sourceIPAddress": "1.2.3.4",
            "userName":        "alice"
        },
        {
            "eventTime":       pd.Timestamp("2026-01-25T11:00:00Z"),
            "eventName":       "",   # empty event name — must be removed
            "eventSource":     "iam.amazonaws.com",
            "sourceIPAddress": "5.6.7.8",
            "userName":        "bob"
        }
    ])

@pytest.fixture
def dataframe_all_nat():
    """DataFrame where every eventTime is NaT — extreme case"""
    return pd.DataFrame([
        {
            "eventTime":       pd.NaT,
            "eventName":       "ConsoleLogin",
            "eventSource":     "signin.amazonaws.com",
            "sourceIPAddress": "1.2.3.4",
            "userName":        "alice"
        },
        {
            "eventTime":       pd.NaT,
            "eventName":       "CreateUser",
            "eventSource":     "iam.amazonaws.com",
            "sourceIPAddress": "5.6.7.8",
            "userName":        "bob"
        }
    ])

@pytest.fixture
def dataframe_missing_column():
    """DataFrame missing the eventSource column"""
    return pd.DataFrame([
        {
            "eventTime":       pd.Timestamp("2026-01-25T10:00:00Z"),
            "eventName":       "ConsoleLogin",
            # eventSource missing intentionally
            "sourceIPAddress": "1.2.3.4",
            "userName":        "alice"
        }
    ])

@pytest.fixture
def dataframe_with_unknown_values():
    """DataFrame with unknown values — should be kept, not removed"""
    return pd.DataFrame([
        {
            "eventTime":       pd.Timestamp("2026-01-25T10:00:00Z"),
            "eventName":       "AssumeRole",
            "eventSource":     "sts.amazonaws.com",
            "sourceIPAddress": "unknown",   # valid — internal AWS service
            "userName":        "unknown"    # valid — automated service
        }
    ])

@pytest.fixture
def empty_dataframe():
    """Completely empty DataFrame with correct columns"""
    return pd.DataFrame(columns=[
        "eventTime", "eventName", "eventSource",
        "sourceIPAddress", "userName"
    ])


# ─── Tests : validate_schema() ───────────────────────────────

class TestValidateSchema:

    def test_returns_true_on_valid_dataframe(self, validator, valid_dataframe):
        """Should return True when all required columns are present"""
        # Arrange — valid_dataframe has all 5 required columns

        # Act
        result = validator.validate_schema(valid_dataframe)

        # Assert
        assert result is True

    def test_returns_false_when_column_missing(self, validator, dataframe_missing_column):
        """Should return False when a required column is absent"""
        # Arrange — dataframe_missing_column has no eventSource

        # Act
        result = validator.validate_schema(dataframe_missing_column)

        # Assert
        assert result is False

    def test_returns_false_on_empty_dataframe_no_columns(self, validator):
        """Should return False when DataFrame has no columns at all"""
        # Arrange — completely empty DataFrame
        df = pd.DataFrame()

        # Act
        result = validator.validate_schema(df)

        # Assert
        assert result is False

    def test_returns_true_on_empty_dataframe_with_correct_columns(self, validator, empty_dataframe):
        """Should return True even if DataFrame is empty but has correct columns"""
        # Arrange — empty DataFrame but correct schema

        # Act
        result = validator.validate_schema(empty_dataframe)

        # Assert — schema is valid even with 0 rows
        assert result is True

    def test_detects_all_five_required_columns(self, validator):
        """Should detect when multiple required columns are missing"""
        # Arrange — DataFrame with only one column
        df = pd.DataFrame({"eventName": ["ConsoleLogin"]})

        # Act
        result = validator.validate_schema(df)

        # Assert — 4 columns missing
        assert result is False

    def test_required_columns_list_is_correct(self, validator):
        """DataValidator must define exactly the 5 expected required columns"""
        # Arrange
        expected = {
            "eventTime", "eventName", "eventSource",
            "sourceIPAddress", "userName"
        }

        # Act — check the class constant directly
        actual = set(validator.REQUIRED_COLUMNS)

        # Assert
        assert actual == expected


# ─── Tests : clean_data() ────────────────────────────────────

class TestCleanData:

    def test_returns_dataframe(self, validator, valid_dataframe):
        """Should always return a DataFrame"""
        # Arrange

        # Act
        result = validator.clean_data(valid_dataframe)

        # Assert
        assert isinstance(result, pd.DataFrame)

    def test_removes_rows_with_nat_eventtime(self, validator, dataframe_with_nat):
        """Should remove rows where eventTime is NaT"""
        # Arrange — 2 rows, 1 with NaT

        # Act
        result = validator.clean_data(dataframe_with_nat)

        # Assert — only 1 row should remain
        assert len(result) == 1
        assert result.iloc[0]["userName"] == "alice"

    def test_removes_rows_with_empty_eventname(self, validator, dataframe_with_empty_eventname):
        """Should remove rows where eventName is empty string"""
        # Arrange — 2 rows, 1 with empty eventName

        # Act
        result = validator.clean_data(dataframe_with_empty_eventname)

        # Assert — only 1 row should remain
        assert len(result) == 1
        assert result.iloc[0]["eventName"] == "ConsoleLogin"

    def test_keeps_rows_with_unknown_values(self, validator, dataframe_with_unknown_values):
        """Should keep rows where userName or sourceIPAddress is unknown"""
        # Arrange — unknown is valid, not an error

        # Act
        result = validator.clean_data(dataframe_with_unknown_values)

        # Assert — row must be kept
        assert len(result) == 1
        assert result.iloc[0]["userName"] == "unknown"
        assert result.iloc[0]["sourceIPAddress"] == "unknown"

    def test_keeps_all_rows_on_clean_dataframe(self, validator, valid_dataframe):
        """Should not remove any rows when DataFrame is already clean"""
        # Arrange — 3 valid rows

        # Act
        result = validator.clean_data(valid_dataframe)

        # Assert — all 3 rows preserved
        assert len(result) == 3

    def test_returns_empty_dataframe_when_all_nat(self, validator, dataframe_all_nat):
        """Should return empty DataFrame when all eventTime values are NaT"""
        # Arrange — extreme case: every row is invalid

        # Act
        result = validator.clean_data(dataframe_all_nat)

        # Assert — nothing left
        assert len(result) == 0
        assert isinstance(result, pd.DataFrame)

    def test_index_is_reset_after_cleaning(self, validator, dataframe_with_nat):
        """Index should be reset after rows are removed"""
        # Arrange — 2 rows, row index 1 will be removed

        # Act
        result = validator.clean_data(dataframe_with_nat)

        # Assert — index must start at 0 with no gaps
        assert list(result.index) == [0]

    def test_does_not_modify_original_dataframe(self, validator, dataframe_with_nat):
        """clean_data should not mutate the original DataFrame"""
        # Arrange — save original length
        original_length = len(dataframe_with_nat)

        # Act
        validator.clean_data(dataframe_with_nat)

        # Assert — original DataFrame unchanged
        assert len(dataframe_with_nat) == original_length