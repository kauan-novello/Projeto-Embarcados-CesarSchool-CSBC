import logging
import math
import threading
import time
from collections.abc import Callable

logger = logging.getLogger(__name__)

REFRESH_SECONDS = 600


class RefreshingCache[T]:
    def __init__(self, loader: Callable[[], T], clock: Callable[[], float] = time.monotonic) -> None:
        self._loader = loader
        self._clock = clock
        self._value: T | None = None
        self._loaded_at = -math.inf
        self._lock = threading.Lock()

    def get(self) -> T | None:
        with self._lock:
            if self._clock() - self._loaded_at >= REFRESH_SECONDS:
                try:
                    self._value = self._loader()
                except Exception:
                    logger.exception("could not load from MLflow")
                self._loaded_at = self._clock()
            return self._value
