"""Xây Dựng Số desktop application."""


def main() -> int:
    """Start the desktop application without GUI side effects on import."""
    import sys

    if "--reminder-worker" in sys.argv:
        sys.argv.remove("--reminder-worker")
        from xaydungso.worker import main as run_worker

        return run_worker()
    from xaydungso.app import main as run

    return run()
