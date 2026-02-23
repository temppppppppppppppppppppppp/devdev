import re
import sys

filepath = r'C:\Users\wjjo\Desktop\글도비\modules\core\db_manager.py'

with open(filepath, encoding='utf-8') as f:
    content = f.read()

original_content = content

# ── Step 1: Replace bad commit check pattern ──────────────────────────────
# Pattern: "<indent>if not self.conn.in_transaction:\n<same-indent>    self.conn.commit()"
bad_commit_re = re.compile(
    r'([ \t]+)if not self\.conn\.in_transaction:\n\1    self\.conn\.commit\(\)'
)

count_before = len(bad_commit_re.findall(content))
new_content = bad_commit_re.sub(
    r'\1if not nested:\n\1    self.commit()',
    content
)
count_after = len(bad_commit_re.findall(new_content))
print(f"Step 1 replacements: {count_before} -> remaining {count_after}")
assert count_after == 0, f"Still {count_after} bad patterns remain!"

# ── Step 2: Add "nested = self.conn.in_transaction" at start of each ──────
# `with self._lock:` block that now contains `if not nested:` but does NOT
# already have `nested = self.conn.in_transaction`

lines = new_content.split('\n')
result = []
i = 0
added = 0

while i < len(lines):
    line = lines[i]

    # Match "        with self._lock:" (8-space method body indent)
    m = re.match(r'^(        )with self\._lock:\s*$', line)
    if m:
        base_indent = m.group(1)          # 8 spaces
        block_indent = base_indent + '    '  # 12 spaces

        # Collect all lines in this block (>=12-space indent or blank)
        j = i + 1
        while j < len(lines):
            bl = lines[j]
            if not bl.strip():
                j += 1
                continue
            bl_indent_len = len(bl) - len(bl.lstrip())
            if bl_indent_len >= len(block_indent):
                j += 1
            else:
                break
        # block is lines[i+1 .. j-1]
        block_text = '\n'.join(lines[i+1:j])

        needs_nested = (
            'if not nested:' in block_text
            and 'nested = self.conn.in_transaction' not in block_text
        )

        result.append(line)
        i += 1

        if needs_nested:
            # Skip any blank lines right after "with self._lock:"
            while i < len(lines) and not lines[i].strip():
                result.append(lines[i])
                i += 1
            # Insert nested assignment before the first real line of the block
            result.append(block_indent + 'nested = self.conn.in_transaction')
            added += 1
        continue

    result.append(line)
    i += 1

final_content = '\n'.join(result)
print(f"Step 2 additions: {added}")

# ── Sanity check ──────────────────────────────────────────────────────────
nested_new = final_content.count('nested = self.conn.in_transaction')
nested_old = original_content.count('nested = self.conn.in_transaction')
print(f"nested assignments: {nested_old} -> {nested_new} (+{nested_new - nested_old})")

remaining_bad = len(bad_commit_re.findall(final_content))
print(f"Remaining bad patterns: {remaining_bad}")

# Make sure commit_episode_factory was not touched (uses nested_transaction, not nested)
if 'nested_transaction = self.conn.in_transaction' not in final_content:
    print("WARNING: commit_episode_factory nested_transaction may have been mangled!")
    sys.exit(1)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(final_content)

print("Patch written successfully.")
