# secrets/

Local-only secret env files live here.

Recommended file for ClickUp sync:

- `secrets/clickup.env`

Example:

```env
CLICKUP_API_TOKEN=pk_your_clickup_personal_token_here
CLICKUP_LIST_ID=your_clickup_list_id_here
# Optional
# CLICKUP_STATUS_MAP_JSON={"Ready":"To Do","Realizing":"In Progress","Proof Pending":"Review","Blocked":"Blocked","Parked":"Backlog","Closed":"Done"}
```

Notes:

- `secrets/*.env` is gitignored
- this folder is intentionally visible so the file is easy to find later
- `scripts/sync_clickup_queue.py` loads root `.env` first, then `secrets/clickup.env`
