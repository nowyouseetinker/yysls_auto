from __future__ import annotations

import threading
from collections.abc import Callable

from services.log_service import LogService

# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def _make_collector() -> tuple[list[dict[str, str]], Callable[[dict[str, str]], None]]:
    """Return a list and a callback that appends every received entry to it."""
    collected: list[dict[str, str]] = []

    def collect(entry: dict[str, str]) -> None:
        collected.append(entry)

    return collected, collect


# ---------------------------------------------------------------------------
# TestInitEmpty
# ---------------------------------------------------------------------------


class TestInitEmpty:
    """Tests for LogService initialisation."""

    def test_get_logs_returns_empty_list(self) -> None:
        svc = LogService()
        assert svc.get_logs() == []


# ---------------------------------------------------------------------------
# TestAdd
# ---------------------------------------------------------------------------


class TestAdd:
    """Tests for LogService.add()."""

    def test_add_appends_to_deque(self) -> None:
        svc = LogService()
        svc.add("first")
        svc.add("second")

        logs = svc.get_logs()
        assert len(logs) == 2
        assert logs[0]["message"] == "first"
        assert logs[1]["message"] == "second"

    def test_timestamp_is_iso8601_utc_string(self) -> None:
        svc = LogService()
        svc.add("hello")

        logs = svc.get_logs()
        assert len(logs) == 1
        # ISO 8601 UTC strings end with '+00:00' or 'Z'
        ts = logs[0]["timestamp"]
        assert ts.endswith("+00:00") or ts.endswith("Z")

    def test_timestamps_are_monotonic(self) -> None:
        svc = LogService()
        svc.add("a")
        svc.add("b")

        logs = svc.get_logs()
        assert logs[0]["timestamp"] <= logs[1]["timestamp"]

    def test_notifies_subscriber_with_entry(self) -> None:
        collected, collect = _make_collector()
        svc = LogService()
        svc.subscribe(collect)
        svc.add("sub-test")

        assert len(collected) == 1
        assert collected[0]["message"] == "sub-test"
        assert "timestamp" in collected[0]

    def test_notifies_all_subscribers(self) -> None:
        c1, cb1 = _make_collector()
        c2, cb2 = _make_collector()
        svc = LogService()
        svc.subscribe(cb1)
        svc.subscribe(cb2)
        svc.add("broadcast")

        assert len(c1) == 1
        assert len(c2) == 1
        assert c1[0]["message"] == "broadcast"
        assert c2[0]["message"] == "broadcast"


# ---------------------------------------------------------------------------
# TestGetLogs
# ---------------------------------------------------------------------------


class TestGetLogs:
    """Tests for LogService.get_logs()."""

    def test_returns_shallow_copy_not_live_view(self) -> None:
        svc = LogService()
        svc.add("one")

        snapshot = svc.get_logs()
        assert len(snapshot) == 1

        svc.add("two")
        # Snapshot must not reflect later mutations
        assert len(snapshot) == 1

    def test_entries_have_expected_keys(self) -> None:
        svc = LogService()
        svc.add("check keys")

        logs = svc.get_logs()
        assert set(logs[0].keys()) == {"timestamp", "message"}


# ---------------------------------------------------------------------------
# TestSubscribeUnsubscribe
# ---------------------------------------------------------------------------


class TestSubscribeUnsubscribe:
    """Tests for LogService.subscribe() and .unsubscribe()."""

    def test_unsubscribed_callback_is_not_called(self) -> None:
        collected, collect = _make_collector()
        svc = LogService()
        svc.subscribe(collect)
        svc.unsubscribe(collect)
        svc.add("should not be collected")

        assert collected == []

    def test_duplicate_subscription_is_ignored(self) -> None:
        collected, collect = _make_collector()
        svc = LogService()
        svc.subscribe(collect)
        svc.subscribe(collect)  # duplicate
        svc.add("once")

        # Callback must still fire exactly once
        assert len(collected) == 1

    def test_unsubscribe_nonexistent_is_noop(self) -> None:
        svc = LogService()

        def dummy(entry: dict[str, str]) -> None:
            pass

        svc.unsubscribe(dummy)  # must not raise

    def test_subscribe_while_add_is_calling_callbacks_is_safe(self) -> None:
        """Subscribe from inside a callback — must not deadlock."""
        svc = LogService()

        second: list[dict[str, str]] = []

        def first_cb(entry: dict[str, str]) -> None:
            def second_cb(e: dict[str, str]) -> None:
                second.append(e)

            svc.subscribe(second_cb)

        svc.subscribe(first_cb)
        svc.add("trigger")

        # The second subscriber was added during add(), so this next add()
        # should notify both.
        svc.add("trigger-2")
        assert len(second) == 1
        assert second[0]["message"] == "trigger-2"


# ---------------------------------------------------------------------------
# TestClear
# ---------------------------------------------------------------------------


class TestClear:
    """Tests for LogService.clear()."""

    def test_clear_empties_deque(self) -> None:
        svc = LogService()
        svc.add("a")
        svc.add("b")
        assert len(svc.get_logs()) == 2

        svc.clear()
        assert svc.get_logs() == []

    def test_clear_on_already_empty_is_noop(self) -> None:
        svc = LogService()
        svc.clear()  # must not raise
        assert svc.get_logs() == []

    def test_clear_does_not_affect_subscribers(self) -> None:
        collected, collect = _make_collector()
        svc = LogService()
        svc.subscribe(collect)
        svc.clear()
        svc.add("after clear")

        assert len(collected) == 1
        assert collected[0]["message"] == "after clear"


# ---------------------------------------------------------------------------
# TestMaxEntries
# ---------------------------------------------------------------------------


class TestMaxEntries:
    """Tests for deque maxlen bounding."""

    def test_deque_holds_at_most_maxlen_entries(self) -> None:
        svc = LogService()
        for i in range(svc._MAX_ENTRIES + 50):
            svc.add(str(i))

        logs = svc.get_logs()
        assert len(logs) == svc._MAX_ENTRIES
        # Oldest entries must have been evicted
        assert logs[0]["message"] == "50"
        assert logs[-1]["message"] == str(svc._MAX_ENTRIES + 49)


# ---------------------------------------------------------------------------
# TestThreadSafety
# ---------------------------------------------------------------------------


class TestThreadSafety:
    """Smoke tests for thread safety."""

    def test_concurrent_adds_dont_corrupt_deque(self) -> None:
        svc = LogService()
        n_per_thread = 250
        barrier = threading.Barrier(4)

        def worker() -> None:
            barrier.wait()
            for i in range(n_per_thread):
                svc.add(str(i))

        threads = [threading.Thread(target=worker) for _ in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        logs = svc.get_logs()
        assert len(logs) == svc._MAX_ENTRIES  # bounded deque

    def test_concurrent_subscribe_unsubscribe_is_safe(self) -> None:
        svc = LogService()
        exceptions: list[Exception] = []

        def subscribe_loop() -> None:
            try:
                for i in range(100):
                    def cb(entry: dict[str, str], n: int = i) -> None:
                        pass

                    svc.subscribe(cb)
                    svc.unsubscribe(cb)
            except Exception as exc:
                exceptions.append(exc)

        def add_loop() -> None:
            try:
                for _ in range(100):
                    svc.add("concurrent")
            except Exception as exc:
                exceptions.append(exc)

        t1 = threading.Thread(target=subscribe_loop)
        t2 = threading.Thread(target=add_loop)
        t1.start()
        t2.start()
        t1.join()
        t2.join()

        assert exceptions == []
