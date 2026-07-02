from tenacity import retry, stop_after_attempt, wait_exponential
import time

# Mock object to track attempts
class MockStats:
    attempts = 0

stats = MockStats()

print("Defining retriable function...")

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=5),
    reraise=True
)
def unstable_function():
    stats.attempts += 1
    print(f"Attempt #{stats.attempts}")
    raise Exception("Simulated 429 Error")

try:
    print("Calling unstable function...")
    unstable_function()
except Exception as e:
    print(f"Caught expected final exception: {e}")

print(f"Total attempts made: {stats.attempts}")
if stats.attempts == 3:
    print("SUCCESS: Retry logic worked (3 attempts made).")
else:
    print(f"FAILURE: Expected 3 attempts, got {stats.attempts}")
