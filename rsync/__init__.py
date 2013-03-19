# outer __init__.py
from rsync.rsync import rsync
from rsync.rsync import connection

__all__ = [rsync, connection]
