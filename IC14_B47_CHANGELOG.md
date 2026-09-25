# IC1.4 B47 ChangeLog
- Added immutable Pre-Race Entry Snapshot LOCK.
- Existing locks are never silently overwritten.
- Entry content changes invalidate the prior lock and require explicit re-lock.
- Added explicit re-lock endpoint.
- Lock scope is ENTRY_ONLY; odds and scheduled-start cutoff are explicitly not yet locked/enforced.
- Storage is explicitly disclosed as PROCESS_MEMORY_VOLATILE and not durable across Render restarts.
- No fixed rider-count or contiguous-car assumption.
