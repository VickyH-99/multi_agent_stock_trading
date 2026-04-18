"""
Helpers for calling AkShare safely in environments with broken proxy vars.
"""
from __future__ import annotations

import asyncio
import importlib
from contextlib import contextmanager
from functools import partial
from typing import Any, Callable, Iterator, Optional
from concurrent.futures import Executor
import requests.sessions


def _disabled_tqdm(enable: bool = True):
    return lambda iterable, *args, **kwargs: iterable


@contextmanager
def _disable_requests_proxy() -> Iterator[None]:
    original = requests.sessions.Session.merge_environment_settings

    def merge_without_proxy(self, url, proxies, stream, verify, cert):
        settings = original(self, url, {}, stream, verify, cert)
        settings["proxies"] = {}
        return settings

    requests.sessions.Session.merge_environment_settings = merge_without_proxy
    try:
        yield
    finally:
        requests.sessions.Session.merge_environment_settings = original


@contextmanager
def _disable_akshare_progress() -> Iterator[None]:
    patched: list[tuple[Any, str, Any]] = []
    targets = (
        ("akshare.stock.stock_zh_a_sina", "get_tqdm"),
        ("akshare.stock_feature.stock_hist_tx", "get_tqdm"),
    )

    try:
        for module_name, attr_name in targets:
            try:
                module = importlib.import_module(module_name)
                original = getattr(module, attr_name, None)
                if original is None:
                    continue
                patched.append((module, attr_name, original))
                setattr(module, attr_name, _disabled_tqdm)
            except Exception:
                continue
        yield
    finally:
        for module, attr_name, original in patched:
            setattr(module, attr_name, original)


def call_akshare(func: Callable[..., Any], /, *args: Any, **kwargs: Any) -> Any:
    with _disable_requests_proxy(), _disable_akshare_progress():
        return func(*args, **kwargs)


async def run_akshare_in_executor(
    func: Callable[..., Any],
    /,
    *args: Any,
    executor: Optional[Executor] = None,
    **kwargs: Any,
) -> Any:
    loop = asyncio.get_running_loop()
    bound = partial(call_akshare, func, *args, **kwargs)
    return await loop.run_in_executor(executor, bound)
