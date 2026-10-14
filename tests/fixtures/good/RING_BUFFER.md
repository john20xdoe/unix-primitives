# Log Stream Truncation
Process output streams pipe through a constant-bound FIFO circular ring buffer.
Buffer capacity maintains strict memory invariants under high volume:
- Total buffer capacity is bounded at a fixed capacity of fifty lines.
- Head lines capture the initial execution commands and environment headers.
- Intermediate lines exceeding capacity are evicted from buffer memory.
- Tail lines retain the final error traces and diagnostic return codes.
A truncation notice indicates omitted line counts between head and tail segments.
Context window consumption remains strictly O(1) regardless of output size.
Streaming sinks ingest bounded output frames without buffer overflow risks.