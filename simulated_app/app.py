import time

import pandas as pd
import streamlit as st

from config import PATCHES_DIR, db_display_name
from db.database import fetch_all, get_applied_patches, get_connection, init_db
from services.patch_service import apply_patches, list_patch_files

st.set_page_config(page_title="Simulated App", page_icon="📦", layout="wide")

st.title("Simulated App")
st.caption("Drop patch files into `patches/` to update data. Database is the source of truth for the UI.")


@st.cache_resource
def get_db():
    conn = get_connection()
    init_db(conn)
    return conn


conn = get_db()

with st.sidebar:
    st.header("Controls")
    auto_refresh = st.toggle("Auto-refresh (5s)", value=False)
    if st.button("Apply patches now", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    st.divider()
    st.subheader("Patch files")
    patch_files = list_patch_files()
    if patch_files:
        for pf in patch_files:
            st.text(f"• {pf.name}")
    else:
        st.info(f"No patch files in `{PATCHES_DIR.name}/`")

    st.divider()
    st.caption(f"DB: `{db_display_name()}`")

results = apply_patches(conn)
newly_applied = [r for r in results if not r.skipped and not r.error and (r.inserted or r.updated)]

if newly_applied:
    for r in newly_applied:
        if getattr(r, "kind", "rows") == "sql":
            st.success(f"Applied SQL `{r.filename}` — ~{r.inserted} changes")
        else:
            st.success(f"Applied `{r.filename}` — {r.inserted} inserted, {r.updated} updated")

errors = [r for r in results if r.error]
for r in errors:
    st.error(f"Failed `{r.filename}`: {r.error}")

col1, col2, col3 = st.columns(3)
rows = fetch_all(conn)
applied = get_applied_patches(conn)

with col1:
    st.metric("Total rows", len(rows))
with col2:
    st.metric("Applied patches", len(applied))
with col3:
    st.metric("Patch files", len(patch_files))

st.subheader("Data from database")
if rows:
    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True, hide_index=True)
else:
    st.info("No data yet. Add a patch file to `patches/` to seed rows.")

with st.expander("Patch activity"):
    if results:
        activity = []
        for r in results:
            if r.skipped:
                status = "already applied"
            elif r.error:
                status = f"error: {r.error}"
            else:
                status = f"+{r.inserted} / ~{r.updated}"
            activity.append({"file": r.filename, "status": status})
        st.dataframe(pd.DataFrame(activity), use_container_width=True, hide_index=True)
    else:
        st.write("No patch files found.")

st.divider()
st.markdown(
    """
**Adding a patch**

Drop `.json`, `.csv`, or `.sql` into `patches/` — applied once, in filename order.

Or run SQL manually (dialect must match backend):
```bash
./apply patches/examples/006_postgres_example.sql   # postgres
./apply patches/examples/005_sqlite_example.sql   # sqlite
```

Set `DB_BACKEND=postgres` (and `DATABASE_URL` or `PG*` vars) to use Postgres.
Only `.json` / `.csv` / `.sql` files directly in `patches/` are auto-applied.
Use `patches/examples/` for backend-specific SQL you run manually.
"""
)

if auto_refresh:
    time.sleep(5)
    st.rerun()
