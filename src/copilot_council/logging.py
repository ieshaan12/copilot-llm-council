"""Logging configuration with session GUID tracking."""

from __future__ import annotations

import json
import logging
import sys
import textwrap
from collections.abc import MutableMapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

# Maximum line width for log output
MAX_LINE_WIDTH = 120


def _format_multiline_json(data: dict[str, Any], indent: int = 2) -> str:
    """Format a dict as JSON with multiline strings properly displayed.

    Long string values are wrapped and displayed with actual newlines
    instead of escaped \\n characters for better readability.

    Parameters
    ----------
    data : dict[str, Any]
        The data to format.
    indent : int
        Indentation level.

    Returns
    -------
    str
        Formatted JSON-like string.
    """
    lines = ["{"]
    items = list(data.items())
    wrap_width = MAX_LINE_WIDTH - indent - 10  # Leave room for key and punctuation

    for i, (key, value) in enumerate(items):
        comma = "," if i < len(items) - 1 else ""

        if isinstance(value, str) and (len(value) > wrap_width or "\n" in value):
            # Format long/multiline strings with actual newlines
            lines.append(f'{" " * indent}"{key}": |')
            # Wrap and indent each line of the content
            for content_line in value.split("\n"):
                if len(content_line) > wrap_width:
                    wrapped = textwrap.wrap(content_line, width=wrap_width)
                    for w in wrapped:
                        lines.append(f"{' ' * (indent + 2)}{w}")
                else:
                    lines.append(f"{' ' * (indent + 2)}{content_line}")
            if comma:
                lines[-1] = lines[-1]  # comma handled by next field
        elif isinstance(value, dict):
            lines.append(f'{" " * indent}"{key}": {json.dumps(value)}{comma}')
        elif isinstance(value, list):
            lines.append(f'{" " * indent}"{key}": {json.dumps(value)}{comma}')
        elif isinstance(value, bool):
            lines.append(f'{" " * indent}"{key}": {str(value).lower()}{comma}')
        elif value is None:
            lines.append(f'{" " * indent}"{key}": null{comma}')
        elif isinstance(value, int | float):
            lines.append(f'{" " * indent}"{key}": {value}{comma}')
        else:
            # Escape the string value properly
            escaped = json.dumps(value)
            lines.append(f'{" " * indent}"{key}": {escaped}{comma}')

    lines.append("}")
    return "\n".join(lines)


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging with pretty printing."""

    # Extra fields to include in log output
    EXTRA_FIELDS = (
        "session_id",
        "council_name",
        "member_name",
        "role",
        "model",
        "round",
        "prompt",
        "system_prompt",
        "content",
        "raw_output",
        "input_tokens",
        "output_tokens",
        "duration_api",
        "duration_wall",
        "is_valid",
        "validation_errors",
        # CLI execution fields
        "cli_command",
        "cli_command_full",
        "cli_raw_output",
        "cli_returncode",
        "cli_stderr",
        "cli_timeout_seconds",
    )

    def __init__(self, pretty: bool = True) -> None:
        """Initialize the formatter.

        Parameters
        ----------
        pretty : bool
            Whether to pretty-print JSON output, by default True.
        """
        super().__init__()
        self.pretty = pretty

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON.

        Parameters
        ----------
        record : logging.LogRecord
            The log record to format.

        Returns
        -------
        str
            JSON formatted log output.
        """
        log_data: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Add all known extra fields if present
        for field in self.EXTRA_FIELDS:
            if hasattr(record, field):
                log_data[field] = getattr(record, field)

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        if self.pretty:
            # Pretty print with multiline strings and separator
            formatted = _format_multiline_json(log_data)
            return formatted + "\n" + "-" * 80
        else:
            return json.dumps(log_data, ensure_ascii=False)


class SessionLoggerAdapter(logging.LoggerAdapter):
    """Logger adapter that includes session context in all log messages."""

    def process(
        self, msg: str, kwargs: MutableMapping[str, Any]
    ) -> tuple[str, MutableMapping[str, Any]]:
        """Process log message with session context.

        Parameters
        ----------
        msg : str
            Log message.
        kwargs : MutableMapping[str, Any]
            Keyword arguments.

        Returns
        -------
        tuple[str, MutableMapping[str, Any]]
            Processed message and kwargs.
        """
        extra = kwargs.get("extra", {})
        if isinstance(extra, dict):
            extra.update(self.extra or {})
            kwargs["extra"] = extra
        return msg, kwargs


def setup_logging(
    level: int = logging.INFO,
    log_file: str | Path | None = None,
    format_type: str = "json",
) -> None:
    """Set up logging configuration.

    Parameters
    ----------
    level : int, optional
        Logging level, by default logging.INFO.
    log_file : str | Path | None, optional
        Path to log file, by default None (console only).
    format_type : str, optional
        Log format: "json" or "text", by default "json".
    """
    root_logger = logging.getLogger("copilot_council")
    root_logger.setLevel(level)

    # Clear existing handlers
    root_logger.handlers.clear()

    # Console handler - compact JSON for terminal readability
    console_formatter: logging.Formatter
    if format_type == "json":
        console_formatter = JSONFormatter(pretty=False)
    else:
        console_formatter = logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)

    # File handler - pretty JSON with line wrapping
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_formatter: logging.Formatter
        if format_type == "json":
            file_formatter = JSONFormatter(pretty=True)
        else:
            file_formatter = logging.Formatter(
                "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        file_handler = logging.FileHandler(log_path)
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)


def get_session_logger(
    session_id: str,
    council_name: str,
) -> SessionLoggerAdapter:
    """Get a logger with session context.

    Parameters
    ----------
    session_id : str
        The session UUID.
    council_name : str
        The council name.

    Returns
    -------
    SessionLoggerAdapter
        Logger with session context attached.
    """
    logger = logging.getLogger("copilot_council")
    return SessionLoggerAdapter(
        logger,
        extra={"session_id": session_id, "council_name": council_name},
    )
