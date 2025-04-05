"""Unit tests for the FoxESS Cloud API Client."""
import pytest
from aiohttp import ClientSession

# Import the class to test
from custom_components.foxess.api import FoxEssApiClient

# Constants for testing
TEST_API_KEY = "test_api_key_123"
TEST_DEVICE_SN = "test_sn_456"


@pytest.fixture
def mock_session() -> ClientSession:
    """Fixture for a mock ClientSession."""
    # In a real scenario, you might mock methods on this session
    # For now, just return a basic instance for initialization
    return ClientSession()


def test_md5c_lower(mock_session):
    """Test the _md5c helper method for lowercase output."""
    client = FoxEssApiClient(mock_session, TEST_API_KEY, TEST_DEVICE_SN)
    text_to_hash = "hello_world"
    expected_hash = "8d777f385d3dfec8815d20f7496026dc"
    assert client._md5c(text_to_hash, _type="lower") == expected_hash
    # Test default type is lower
    assert client._md5c(text_to_hash) == expected_hash


def test_md5c_upper(mock_session):
    """Test the _md5c helper method for uppercase output."""
    client = FoxEssApiClient(mock_session, TEST_API_KEY, TEST_DEVICE_SN)
    text_to_hash = "hello_world"
    expected_hash = "8D777F385D3DFEC8815D20F7496026DC"
    assert client._md5c(text_to_hash, _type="upper") == expected_hash


# Add more tests here for:
# - _get_signature method
# - _request method (using aresponses or aiohttp_client fixture)
# - Each public API method (get_device_detail, get_raw_data, etc.)
#   - Test success cases with mock JSON responses
#   - Test API error cases (e.g., errno != 0)
#   - Test HTTP error cases (e.g., 401, 403, 500)
#   - Test timeout cases
#   - Test invalid JSON response cases