"""Shared test fixtures."""

import n3map.log as log


def pytest_configure(config):
    """Initialize the n3map logger so modules that call log.info() don't crash."""
    log.logger = log.Logger(loglevel=log.LOG_WARN)
