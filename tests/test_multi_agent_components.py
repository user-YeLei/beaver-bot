"""Standalone component tests for multi_agent package — no full Beaver deps needed."""

import sys
import tempfile
from pathlib import Path

# Add src to path so beaver_agent packages resolve normally
src = Path("/Users/mac/4e/beaver-agent/src")
sys.path.insert(0, str(src))

# Fake structlog so modules that import it don't crash
class FakeLogger:
    def info(self, *a, **kw): pass
    def debug(self, *a, **kw): pass
    def warning(self, *a, **kw): pass
    def error(self, *a, **kw): pass

import structlog  # noqa: E402

structlog.get_logger = lambda: FakeLogger()

from beaver_agent.core.multi_agent import (  # noqa: E402
    EventBus,
    Inbox,
    Task,
    TaskStatus,
    TaskType,
    WorkerInfo,
    WorkerPool,
)


def test_protocols():
    print("=== protocols ===")
    t = Task(type=TaskType.CODE_REVIEW, input={"file": "test.py"})
    assert t.status == TaskStatus.PENDING
    t.assign_to("worker_1")
    assert t.status == TaskStatus.ASSIGNED
    assert t.assignee == "worker_1"
    t.start()
    assert t.status == TaskStatus.RUNNING
    assert t.attempt == 1
    t.complete({"result": "ok"})
    assert t.status == TaskStatus.DONE
    assert t.result == {"result": "ok"}
    print("  Task lifecycle: OK")

    wi = WorkerInfo()
    assert wi.role == "worker"
    assert wi.status == "idle"
    print("  WorkerInfo: OK")


def test_inbox():
    print("\n=== inbox ===")
    tmpdir = tempfile.mkdtemp()
    inbox = Inbox(inbox_path=Path(tmpdir) / "tasks.json")

    t1 = Task(type=TaskType.CODE_REVIEW)
    t2 = Task(type=TaskType.DEBUG)
    inbox.submit_batch([t1, t2])
    assert len(inbox.list_pending()) == 2

    claimed = inbox.claim_next("worker_1")
    assert claimed is not None
    assert claimed.status == TaskStatus.ASSIGNED
    assert claimed.assignee == "worker_1"

    claimed.complete({"data": "done"})
    inbox.update(claimed)
    assert len(inbox.list_done()) == 1
    assert len(inbox.list_pending()) == 1
    print("  Submit/claim/complete: OK")

    # Simulate crash-recovery: new Inbox instance reads same file
    inbox2 = Inbox(inbox_path=Path(tmpdir) / "tasks.json")
    assert len(inbox2.list_done()) == 1
    print("  Persistence/recovery: OK")


def test_event_bus():
    print("\n=== event bus ===")
    bus = EventBus()
    events = []
    bus.subscribe("my_event", lambda d: events.append(d))
    bus.publish("my_event", {"msg": "hello"})
    assert len(events) == 1
    assert events[0]["msg"] == "hello"

    bus.publish("other_event", {"x": 1})  # no subscriber, should not raise
    assert len(events) == 1
    print("  Pub/sub: OK")


def test_worker_pool():
    print("\n=== worker pool ===")
    tmpdir = tempfile.mkdtemp()
    inbox = Inbox(inbox_path=Path(tmpdir) / "tasks.json")
    bus = EventBus()

    # Pool starts min_workers automatically
    pool = WorkerPool(inbox=inbox, bus=bus, min_workers=2, max_workers=4)
    st = pool.status()
    assert st["pool_size"] == 2
    assert st["min_workers"] == 2
    assert st["max_workers"] == 4
    print("  Pool init: OK")

    stats = pool.stats()
    assert stats["total_workers"] == 2
    assert stats["busy_workers"] == 0
    assert stats["idle_workers"] == 2
    print("  Pool stats: OK")

    pool.shutdown()
    assert pool.status()["pool_size"] == 0
    print("  Pool shutdown: OK")


if __name__ == "__main__":
    test_protocols()
    test_inbox()
    test_event_bus()
    test_worker_pool()
    print("\n✅ All tests passed!")
