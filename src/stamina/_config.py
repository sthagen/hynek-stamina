# SPDX-FileCopyrightText: 2022 Hynek Schlawack <hs@ox.cx>
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

from threading import Lock
from typing import Callable

from .instrumentation import RetryHookFactory
from .instrumentation._hooks import get_default_hooks, init_hooks
from .typing import RetryHook


class _Testing:
    """
    Test mode specification.

    Strictly private.
    """

    __slots__ = ("attempts",)

    attempts: int

    def __init__(self, attempts: int) -> None:
        self.attempts = attempts


class _Config:
    """
    Global stamina configuration.

    Strictly private.
    """

    __slots__ = (
        "lock",
        "_is_active",
        "_on_retry",
        "_get_on_retry",
        "_testing",
    )

    lock: Lock
    _is_active: bool
    _testing: _Testing | None
    _on_retry: (
        tuple[RetryHook, ...] | tuple[RetryHook | RetryHookFactory, ...] | None
    )
    _get_on_retry: Callable[[], tuple[RetryHook, ...]]

    def __init__(self, lock: Lock) -> None:
        self.lock = lock
        self._is_active = True
        self._testing = None

        # Prepare delayed initialization.
        self._on_retry = None
        self._get_on_retry = self._init_on_first_retry

    @property
    def is_active(self) -> bool:
        return self._is_active

    @is_active.setter
    def is_active(self, value: bool) -> None:
        with self.lock:
            self._is_active = value

    @property
    def testing(self) -> _Testing | None:
        return self._testing

    @testing.setter
    def testing(self, value: _Testing | None) -> None:
        with self.lock:
            self._testing = value

    @property
    def on_retry(self) -> tuple[RetryHook, ...]:
        return self._get_on_retry()

    @on_retry.setter
    def on_retry(
        self, value: tuple[RetryHook | RetryHookFactory, ...] | None
    ) -> None:
        with self.lock:
            self._get_on_retry = self._init_on_first_retry
            self._on_retry = value

    def _init_on_first_retry(self) -> tuple[RetryHook, ...]:
        """
        Perform delayed initialization of on_retry hooks.
        """
        with self.lock:
            # Ensure hooks didn't init while waiting for the lock.
            if self._get_on_retry == self._init_on_first_retry:
                if self._on_retry is None:
                    self._on_retry = get_default_hooks()

                self._on_retry = init_hooks(self._on_retry)

                self._get_on_retry = lambda: self._on_retry  # type: ignore[assignment, return-value]

        return self._on_retry  # type: ignore[return-value]


CONFIG = _Config(Lock())


def is_active() -> bool:
    """
    Check whether retrying is active.

    Returns:
        Whether retrying is active.
    """
    return CONFIG.is_active


def set_active(active: bool) -> None:
    """
    Activate or deactivate retrying.

    Is idempotent and can be called repeatedly with the same value.
    """
    CONFIG.is_active = bool(active)


def is_testing() -> bool:
    """
    Check whether test mode is enabled.

    .. versionadded:: 24.3.0
    """
    return CONFIG.testing is not None


def set_testing(testing: bool, *, attempts: int = 1) -> None:
    """
    Activate or deactivate test mode.

    In testing mode, backoffs are disabled, and attempts are capped to
    *attempts*.

    Is idempotent and can be called repeatedly with the same values.

    .. versionadded:: 24.3.0
    """
    CONFIG.testing = _Testing(attempts) if testing else None
