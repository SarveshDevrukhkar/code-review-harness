from __future__ import annotations

import sys


class StatusReporter:
    """Phased CLI status on stderr (same flow for local and remote)."""

    TOTAL_STEPS = 7

    def __init__(self, *, quiet: bool = False) -> None:
        self.quiet = quiet
        self._step = 0

    def _line(self, step: int, message: str) -> None:
        if self.quiet:
            return
        print(f"[{step}/{self.TOTAL_STEPS}] {message}", file=sys.stderr)

    def _detail(self, message: str) -> None:
        if self.quiet:
            return
        print(f"      → {message}", file=sys.stderr)

    def configuration_loaded(self, provider: str, model: str, base_url: str) -> None:
        self._step = 1
        self._line(
            self._step,
            f"Configuration loaded (provider: {provider}, model: {model}, base: {base_url})",
        )

    def collecting_files(self) -> None:
        self._step = 2
        self._line(self._step, "Collecting files to review")

    def chunking(self, num_chunks: int, num_passes: int) -> None:
        self._step = 3
        self._line(
            self._step,
            f"Chunking prepared ({num_chunks} chunk(s), {num_passes} pass(es))",
        )

    def llm_calling(self, chunk_index: int, total_chunks: int, pass_name: str, backend: str) -> None:
        self._step = 4
        self._detail(
            f"Chunk {chunk_index}/{total_chunks} — {pass_name} — calling {backend}…"
        )

    def llm_generating(self) -> None:
        self._detail("Generating response…")

    def llm_done(self, finding_count: int) -> None:
        self._detail(f"Done ({finding_count} finding(s) in chunk)")

    def merging_findings(self) -> None:
        self._step = 5
        self._line(self._step, "Merging and scoring findings")

    def generating_report(self) -> None:
        self._step = 6
        self._line(self._step, "Generating report (markdown/json)")

    def writing_report(self, destination: str) -> None:
        self._step = 7
        self._line(self._step, f"Writing report to {destination}")