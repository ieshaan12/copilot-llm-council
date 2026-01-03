"""Shared pytest fixtures for Copilot Council tests."""

import pytest

from copilot_council.models.member import CouncilMember
from copilot_council.models.response import CopilotResponse, MemberResponse
from copilot_council.models.session import CouncilSession


@pytest.fixture
def sample_member() -> CouncilMember:
    """Create a sample council member."""
    return CouncilMember(
        name="Alice",
        role="critic",
        model="gpt-5",
    )


@pytest.fixture
def sample_member_with_tools() -> CouncilMember:
    """Create a sample member with tool permissions."""
    return CouncilMember(
        name="Bob",
        role="principal_engineer",
        model="claude-sonnet-4",
        allowed_tools=["shell(git:*)", "read"],
        denied_tools=["write"],
    )


@pytest.fixture
def sample_response() -> CopilotResponse:
    """Create a sample Copilot response."""
    return CopilotResponse(
        content="This is a test response from the model.",
        model="gpt-5",
        input_tokens=100,
        output_tokens=25,
        duration_api=2.5,
        duration_wall=3.0,
    )


@pytest.fixture
def sample_member_response(sample_response: CopilotResponse) -> MemberResponse:
    """Create a sample member response."""
    return MemberResponse(
        member_name="Alice",
        role="critic",
        response=sample_response,
        round_number=1,
    )


@pytest.fixture
def sample_session() -> CouncilSession:
    """Create a sample council session."""
    return CouncilSession(
        council_name="test-council",
        task="Test task for the council",
    )


@pytest.fixture
def mock_copilot_output() -> str:
    """Sample raw Copilot CLI output for parsing tests."""
    return """This is the response content from the model.

It can span multiple lines and include code:

```python
def hello():
    print("Hello, world!")
```

Total usage est:       1 Premium request
Total duration (API):  5s
Total duration (wall): 8s
Total code changes:    0 lines added, 0 lines removed
Usage by model:
    gpt-5                5.5k input, 150 output, 0 cache read (Est. 1 Premium request)"""


@pytest.fixture
def mock_copilot_output_simple() -> str:
    """Simple Copilot CLI output."""
    return """The answer is 4.

Total usage est:       1 Premium request
Total duration (API):  2s
Total duration (wall): 3s
Usage by model:
    gpt-5                1000 input, 10 output"""


@pytest.fixture
def sample_config_dict() -> dict:
    """Sample council configuration dictionary."""
    return {
        "name": "test-council",
        "description": "A test council",
        "strategy": "parallel",
        "max_rounds": 3,
        "members": [
            {
                "name": "alice",
                "role": "critic",
                "model": "gpt-5",
            },
            {
                "name": "bob",
                "role": "principal_engineer",
                "model": "claude-sonnet-4",
            },
        ],
        "logging": {
            "level": "INFO",
            "format": "json",
        },
    }
