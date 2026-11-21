"""Poll resolved native snapshots, never Promise truthiness in wait_for_function."""
import time

def wait_for_snapshot(read, predicate, pump, timeout=15):
    deadline=time.monotonic()+timeout
    while True:
        snapshot=read()
        if predicate(snapshot):
            return snapshot
        remaining=deadline-time.monotonic()
        if remaining<=0:
            raise AssertionError(f'Native snapshot condition timed out: {snapshot}')
        pump(min(50,remaining*1000))
