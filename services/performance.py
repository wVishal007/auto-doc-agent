import time
from datetime import datetime


class _PerformanceTracker:
    def __init__(self):
        self.reset()

    def reset(self):
        self.start_time = None
        self.stage_timings = {}
        self._stage_start_times = {}
        self.llm_calls = []
        self.retry_count = 0
        self.retry_details = []
        self.fallback_used = False
        self.fallback_detail = None

    def request_started(self):
        self.reset()
        self.start_time = time.time()
        self._log(f"[{self._ts()}] Request received")

    def stage_start(self, name: str):
        self._stage_start_times[name] = time.time()
        self._log(f"[{self._ts()}] {name} started")

    def stage_end(self, name: str):
        duration = time.time() - self._stage_start_times[name]
        self.stage_timings[name] = duration
        self._log(f"[{self._ts()}] {name} completed ({duration:.2f}s)")
        return duration

    def llm_call(
        self,
        provider: str,
        model: str,
        label: str,
        duration: float,
        success: bool,
        retries: int = 0,
        error: str = None,
        prompt_chars: int = None,
        response_chars: int = None,
    ):
        if success and response_chars == 0:
            success = False
            error = "Empty response"
        self.llm_calls.append(
            {
                "provider": provider,
                "model": model,
                "label": label,
                "duration": duration,
                "success": success,
                "retries": retries,
                "error": error,
                "prompt_chars": prompt_chars,
                "response_chars": response_chars,
            }
        )
        status = "Success" if success else f"Failed: {error}"
        sizes = ""
        if prompt_chars is not None:
            sizes += f", prompt={prompt_chars}chars"
        if response_chars is not None:
            sizes += f", response={response_chars}chars"
        self._log(
            f"  LLM [{provider}] {label}: {duration:.2f}s ({status}, retries={retries}{sizes})"
        )

    def retry(self, attempt: int, reason: str, delay: float, label: str = ""):
        self.retry_count += 1
        self.retry_details.append(
            {"attempt": attempt, "reason": reason, "delay": delay, "label": label}
        )
        prefix = f"[{label}] " if label else ""
        self._log(f"  {prefix}Retry attempt {attempt}")
        self._log(f"  Reason: {reason}")
        self._log(f"  Waiting {delay:.1f}s")

    def fallback(self, primary_provider: str, fallback_provider: str):
        self.fallback_used = True
        self.fallback_detail = {
            "primary": primary_provider,
            "fallback": fallback_provider,
        }
        self._log(f"  Primary provider failed after retries.")
        self._log(f"  Switching to fallback provider.")
        self._log(f"  Primary: {primary_provider}")
        self._log(f"  Fallback: {fallback_provider}")

    def reflection(self, score: int, weak_sections: list, duration: float):
        self._log(
            f"  Reflection: score={score}/10, weak_sections={weak_sections}, duration={duration:.2f}s"
        )

    def print_summary(self):
        total = time.time() - self.start_time
        print()
        print("=" * 50)
        print("Performance Summary")
        print("=" * 50)
        print()

        for stage, dur in self.stage_timings.items():
            print(f"{stage}:")
            print(f"  {dur:.2f}s")

        print()
        print(f"Retries: {self.retry_count}")
        print(f"Fallback Used: {'Yes' if self.fallback_used else 'No'}")
        print(f"Total LLM Calls: {len(self.llm_calls)}")

        total_prompt = sum(
            c.get("prompt_chars") or 0 for c in self.llm_calls
        )
        total_response = sum(
            c.get("response_chars") or 0 for c in self.llm_calls
        )
        if total_prompt:
            print(f"Total Prompt Chars: {total_prompt}")
        if total_response:
            print(f"Total Response Chars: {total_response}")

        print(f"Total Execution Time: {total:.2f}s")
        print()
        print("=" * 50)

    @staticmethod
    def _ts():
        return datetime.now().strftime("%H:%M:%S")

    @staticmethod
    def _log(msg: str):
        print(msg)


tracker = _PerformanceTracker()
