import time
from datetime import timedelta
from functools import wraps
import humanize

def how_long(resolution='seconds'):
  def _decorator(func):
    @wraps(func)
    async def _wrapper(*args, **kwargs):
      start_time = time.perf_counter()
      result = await func(*args, **kwargs)
      end_time = time.perf_counter()
      total_time = end_time - start_time
      interval = humanize.precisedelta(
        timedelta(seconds=total_time), 
        minimum_unit=resolution,
        format='%0.4f'
      )
      print(f'func "{func.__name__}" took {interval} to execute.')
      return result
    return _wrapper
  return _decorator