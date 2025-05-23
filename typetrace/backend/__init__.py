```python
"""TypeTrace - Backend for keyboard trace analysis."""

from __future__ import annotations

import logging
import os
import sys
from typing import Any, Dict, List, Optional, Tuple, Union

# Configure logging (moved to top for immediate effect)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    stream=sys.stdout,
)

logger = logging.getLogger(__name__)


class TypeTraceError(Exception):
    """Base class for TypeTrace exceptions."""

    pass


class InvalidTraceDataError(TypeTraceError):
    """Raised when trace data is invalid."""

    pass


class AnalysisError(TypeTraceError):
    """Raised during analysis if an error occurs."""

    pass


def load_trace_data(file_path: str) -> Optional[List[Dict[str, Any]]]:
    """
    Loads trace data from a JSON file.

    Args:
        file_path: The path to the JSON file.

    Returns:
        A list of dictionaries representing the trace data, or None if the file
        does not exist or an error occurs during loading.
    """
    import json

    if not os.path.exists(file_path):
        logger.error(f"File not found: {file_path}")
        return None

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if not isinstance(data, list):
                raise InvalidTraceDataError(
                    "Trace data must be a list of dictionaries."
                )
            for item in data:
                if not isinstance(item, dict):
                    raise InvalidTraceDataError(
                        "Each item in trace data must be a dictionary."
                    )
            return data
    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"Error decoding JSON from {file_path}: {e}")
        return None
    except InvalidTraceDataError as e:
        logger.error(f"Invalid trace data in {file_path}: {e}")
        return None
    except Exception as e:
        logger.exception(f"An unexpected error occurred: {e}")  # Log full exception
        return None


def validate_trace_data(trace_data: List[Dict[str, Any]]) -> bool:
    """
    Validates the structure and content of trace data.

    Args:
        trace_data: A list of dictionaries representing the trace data.

    Returns:
        True if the trace data is valid, False otherwise.
    """
    if not isinstance(trace_data, list):
        logger.error("Trace data must be a list.")
        return False

    for event in trace_data:
        if not isinstance(event, dict):
            logger.error("Each event in trace data must be a dictionary.")
            return False

        required_keys = ["timestamp", "key", "event_type"]  # Example required keys
        for key in required_keys:
            if key not in event:
                logger.error(f"Missing required key: {key} in event: {event}")
                return False
            if not isinstance(event[key], (str, int, float, bool)):
                logger.error(
                    f"Invalid data type for key: {key} in event: {event}. "
                    f"Must be str, int, float, or bool."
                )
                return False

    return True


def analyze_keystroke_timing(
    trace_data: List[Dict[str, Any]],
) -> Optional[List[float]]:
    """
    Analyzes the timing between keystrokes in the trace data.

    Args:
        trace_data: A list of dictionaries representing the trace data.

    Returns:
        A list of inter-keystroke intervals (in seconds), or None if an error occurs.
    """
    if not validate_trace_data(trace_data):
        logger.error("Invalid trace data. Analysis aborted.")
        return None

    try:
        intervals: List[float] = []
        previous_timestamp: Optional[float] = None

        for event in trace_data:
            timestamp = float(event["timestamp"])  # Ensure timestamp is a float

            if previous_timestamp is not None:
                interval = timestamp - previous_timestamp
                intervals.append(interval)

            previous_timestamp = timestamp

        return intervals

    except (ValueError, KeyError) as e:
        logger.error(f"Error during keystroke timing analysis: {e}")
        return None
    except Exception as e:
        logger.exception(f"An unexpected error occurred during analysis: {e}")
        return None


def calculate_typing_speed(
    trace_data: List[Dict[str, Any]],
    start_time: Optional[float] = None,
    end_time: Optional[float] = None,
) -> Optional[float]:
    """
    Calculates the typing speed in words per minute (WPM).

    Args:
        trace_data: A list of dictionaries representing the trace data.
        start_time: Optional start time (timestamp) for the calculation.
        end_time: Optional end time (timestamp) for the calculation.

    Returns:
        The typing speed in WPM, or None if an error occurs.
    """
    if not validate_trace_data(trace_data):
        logger.error("Invalid trace data. Calculation aborted.")
        return None

    try:
        # Filter events based on start and end times if provided
        filtered_data = trace_data
        if start_time is not None:
            filtered_data = [
                event for event in filtered_data if float(event["timestamp"]) >= start_time
            ]
        if end_time is not None:
            filtered_data = [
                event for event in filtered_data if float(event["timestamp"]) <= end_time
            ]

        if not filtered_data:
            logger.warning("No data available within the specified time range.")
            return 0.0  # Or None, depending on desired behavior

        # Count the number of characters typed (assuming each key event represents a character)
        num_characters = len(filtered_data)

        # Calculate the time duration in minutes
        start_timestamp = float(filtered_data[0]["timestamp"])
        end_timestamp = float(filtered_data[-1]["timestamp"])
        duration_minutes = (end_timestamp - start_timestamp) / 60.0

        if duration_minutes == 0:
            logger.warning("Typing duration is zero. Cannot calculate WPM.")
            return 0.0  # Avoid division by zero

        # Calculate WPM (assuming 5 characters per word)
        wpm = (num_characters / 5.0) / duration_minutes
        return wpm

    except (ValueError, KeyError) as e:
        logger.error(f"Error during WPM calculation: {e}")
        return None
    except Exception as e:
        logger.exception(f"An unexpected error occurred during calculation: {e}")
        return None


def detect_anomalies(
    trace_data: List[Dict[str, Any]], threshold: float = 2.0
) -> List[Dict[str, Any]]:
    """
    Detects anomalies in keystroke timing based on a threshold.

    Args:
        trace_data: A list of dictionaries representing the trace data.
        threshold: The threshold for anomaly detection (in standard deviations).

    Returns:
        A list of events identified as anomalies.
    """
    import numpy as np

    if not validate_trace_data(trace_data):
        logger.error("Invalid trace data. Anomaly detection aborted.")
        return []

    try:
        intervals = analyze_keystroke_timing(trace_data)
        if intervals is None or not intervals:
            logger.warning("No keystroke intervals found. No anomalies detected.")
            return []

        mean = np.mean(intervals)
        std = np.std(intervals)

        anomalies: List[Dict[str, Any]] = []
        for i, interval in enumerate(intervals):
            if std > 0 and abs(interval - mean) > threshold * std:
                # Anomaly found; the index i in intervals corresponds to the
                # *second* event that created the interval.
                anomaly_index = i + 1
                if anomaly_index < len(trace_data):
                    anomalies.append(trace_data[anomaly_index])

        return anomalies

    except Exception as e:
        logger.exception(f"An error occurred during anomaly detection: {e}")
        return []


def aggregate_key_presses(trace_data: List[Dict[str, Any]]) -> Dict[str, int]:
    """
    Aggregates the number of presses for each key.

    Args:
        trace_data: A list of dictionaries representing the trace data.

    Returns:
        A dictionary where keys are key names and values are the number of presses.
    """
    if not validate_trace_data(trace_data):
        logger.error("Invalid trace data. Aggregation aborted.")
        return {}

    key_counts: Dict[str, int] = {}
    try:
        for event in trace_data:
            key = event["key"]
            key_counts[key] = key_counts.get(key, 0) + 1
    except KeyError as e:
        logger.error(f"Missing key 'key' in event: {event}. Aggregation aborted.")
    except Exception as e:
        logger.exception(f"An unexpected error occurred during aggregation: {e}")

    return key_counts
```