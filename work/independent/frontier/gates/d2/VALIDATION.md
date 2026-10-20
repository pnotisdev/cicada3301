# D2 post-run artifact checks

Document/source validation only; the gate was NOT re-executed.

- All 14 input SHA-256 records, including frozen gate source/protocol and native
  binary, still matched the files read during the invocation.
- Gate source parsed as Python without importing or executing it.
- 34 markdown citation occurrences checked for existing files and valid line bounds.
- Every then-present file in this folder was text-scanned for absolute drive paths
  and private environment-name values; no matches.
- Recorded invocation count1 and elapsed time below120 seconds checked.
- Experimental reinvocations by this validation: zero.

These checks do not turn FAILED_RECOVERY_GATE into a pass and do not prove
semantic citation fidelity or decoder power. The result, protocol and source
remain unchanged. The D1 artifacts were checked separately in the same read-only
validation command; no model code or engine was executed by it.
