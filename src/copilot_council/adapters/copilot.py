"""Copilot CLI adapter for subprocess execution."""

from __future__ import annotations

import asyncio
import logging
import re
from typing import TYPE_CHECKING

from copilot_council.exceptions import CopilotExecutionError, CopilotTimeoutError
from copilot_council.models.response import CopilotResponse

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class CopilotAdapter:
    """Adapter for interacting with Copilot CLI.

    Handles subprocess execution, output parsing, and response validation.

    Attributes
    ----------
    timeout : int
        Maximum seconds to wait for CLI response.
    """

    def __init__(self, timeout: int = 120) -> None:
        """Initialize the adapter.

        Parameters
        ----------
        timeout : int, optional
            CLI timeout in seconds, by default 120.
        """
        self.timeout = timeout

    async def query(
        self,
        prompt: str,
        model: str = "gpt-5",
        allowed_tools: list[str] | None = None,
        denied_tools: list[str] | None = None,
        system_prompt: str | None = None,
    ) -> CopilotResponse:
        """Execute a query through Copilot CLI.

        Parameters
        ----------
        prompt : str
            The prompt to send.
        model : str, optional
            Model identifier, by default "gpt-5".
        allowed_tools : list[str] | None, optional
            Tools to allow.
        denied_tools : list[str] | None, optional
            Tools to deny.
        system_prompt : str | None, optional
            System prompt to prepend.

        Returns
        -------
        CopilotResponse
            Parsed and validated response.

        Raises
        ------
        CopilotExecutionError
            If CLI execution fails.
        CopilotTimeoutError
            If CLI times out.
        """
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"

        cmd = self._build_command(full_prompt, model, allowed_tools, denied_tools)
        raw_output = await self._execute(cmd)
        response = self._parse_response(raw_output, model)
        # Attach prompt info for logging
        response.prompt = prompt
        response.system_prompt = system_prompt or ""
        return self._validate_response(response)

    def _build_command(
        self,
        prompt: str,
        model: str,
        allowed_tools: list[str] | None,
        denied_tools: list[str] | None,
    ) -> list[str]:
        """Build CLI command arguments.

        Parameters
        ----------
        prompt : str
            The prompt text.
        model : str
            Model identifier.
        allowed_tools : list[str] | None
            Tools to allow.
        denied_tools : list[str] | None
            Tools to deny.

        Returns
        -------
        list[str]
            Command arguments for subprocess.
        """
        cmd = [
            "copilot",
            "--model",
            model,
            "-p",
            prompt,
            "--no-color",
            "--stream",
            "off",
        ]

        if allowed_tools:
            for tool in allowed_tools:
                cmd.extend(["--allow-tool", tool])
        else:
            cmd.append("--allow-all-tools")

        if denied_tools:
            for tool in denied_tools:
                cmd.extend(["--deny-tool", tool])

        return cmd

    async def _execute(self, cmd: list[str]) -> str:
        """Execute CLI command asynchronously.

        Parameters
        ----------
        cmd : list[str]
            Command arguments.

        Returns
        -------
        str
            Raw CLI output.

        Raises
        ------
        CopilotExecutionError
            If command fails.
        CopilotTimeoutError
            If command times out.
        """
        # Build a safe command string for logging (mask the prompt content for brevity)
        cmd_for_log = " ".join(cmd[:4]) + " [prompt...] " + " ".join(cmd[5:])
        logger.debug(
            "Executing Copilot CLI",
            extra={
                "cli_command": cmd_for_log,
                "cli_command_full": " ".join(cmd),
                "model": cmd[2] if len(cmd) > 2 else "unknown",
            },
        )

        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=self.timeout,
            )

            raw_output = stdout.decode()
            stderr_output = stderr.decode().strip()

            if process.returncode != 0:
                error_msg = stderr_output or "Unknown error"
                logger.debug(
                    "Copilot CLI failed",
                    extra={
                        "cli_returncode": process.returncode,
                        "cli_stderr": stderr_output,
                        "cli_stdout": raw_output,
                    },
                )
                raise CopilotExecutionError(
                    f"CLI failed with code {process.returncode}: {error_msg}"
                )

            logger.debug(
                "Copilot CLI raw response",
                extra={
                    "cli_returncode": process.returncode,
                    "cli_raw_output": raw_output,
                    "cli_stderr": stderr_output if stderr_output else None,
                },
            )

            return raw_output

        except TimeoutError as e:
            logger.debug(
                "Copilot CLI timeout",
                extra={"cli_timeout_seconds": self.timeout},
            )
            raise CopilotTimeoutError(f"CLI timed out after {self.timeout}s") from e

    def _parse_response(self, raw_output: str, model: str) -> CopilotResponse:
        """Parse CLI output into structured response.

        Parameters
        ----------
        raw_output : str
            Raw CLI output.
        model : str
            Model identifier.

        Returns
        -------
        CopilotResponse
            Parsed response.
        """
        # Split content from usage stats
        parts = raw_output.split("\n\nTotal usage est:")
        content = parts[0].strip()

        input_tokens = 0
        output_tokens = 0
        duration_api = 0.0
        duration_wall = 0.0

        if len(parts) > 1:
            stats = parts[1]

            # Parse tokens - handles both "5.5k input" and "5500 input" formats
            token_match = re.search(r"([\d.]+)(k)?\s+input,\s+(\d+)\s+output", stats, re.IGNORECASE)
            if token_match:
                input_val = float(token_match.group(1))
                if token_match.group(2):  # Has 'k' suffix
                    input_tokens = int(input_val * 1000)
                else:
                    input_tokens = int(input_val)
                output_tokens = int(token_match.group(3))

            # Parse durations
            api_match = re.search(r"duration \(API\):\s*(\d+)s", stats)
            wall_match = re.search(r"duration \(wall\):\s*(\d+)s", stats)
            if api_match:
                duration_api = float(api_match.group(1))
            if wall_match:
                duration_wall = float(wall_match.group(1))

        return CopilotResponse(
            content=content,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            duration_api=duration_api,
            duration_wall=duration_wall,
            raw_output=raw_output,
        )

    def _validate_response(self, response: CopilotResponse) -> CopilotResponse:
        """Validate response content.

        Parameters
        ----------
        response : CopilotResponse
            Response to validate.

        Returns
        -------
        CopilotResponse
            Response with validation status set.
        """
        errors: list[str] = []

        if not response.content.strip():
            errors.append("Empty response received")

        error_patterns = [
            (r"error:", "Error indicator in response"),
            (r"rate limit", "Rate limit detected"),
            (r"authentication required", "Authentication required"),
            (r"unauthorized", "Unauthorized access"),
        ]
        for pattern, message in error_patterns:
            if re.search(pattern, response.content, re.IGNORECASE):
                errors.append(message)

        response.is_valid = len(errors) == 0
        response.validation_errors = errors
        return response
