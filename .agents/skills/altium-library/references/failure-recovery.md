# Diagnosing and correcting script failures

Use the deterministic library tools instead of rewriting CAD scripts. A timeout may leave modified unsaved objects; it is not evidence that nothing ran.

The bridge retains request.json, the exact Pascal source, step log and result in each isolated job. `altium_diagnose_job` reads these artifacts and checks the recorded editor PID without launching another script. States distinguish FINISHED, NOT_STARTED, EDITOR_EXITED and STARTED_WITHOUT_COMPLETION. The last state cannot distinguish an error dialog from a running or wedged script without further evidence; do not invent an error message.

Before unfamiliar native operations, place explicit `LogStep` calls before document open, API acquisition, object creation, model linking, registration, save and readback. Avoid one giant untraced body. Test unsupported APIs on disposable documents before a user-library mutation.

Known interpreter hazards are rejected before launch: raise Exception.Create, DoFileLoad on an already-open library and the nonexistent eSheetCustom constant. Correct the code using the verified alternatives in native-api.md. This preflight does not validate arbitrary DelphiScript syntax or every API property.

After an unresolved script timeout the circuit breaker refuses subsequent scripts. Inspect the failed job and saved target. If a modal debugger/interpreter error prevents native calls, ask the user to close the error and Run → Stop. The recovery tool **does not** stop/restart Altium or dismiss dialogs; it runs a five-second read-only probe and clears the breaker only if the exact response returns. Never terminate the primary editor or discard unsaved documents.

After recovery, inspect the target natively and compare it against its checkpoint. Correct demonstrated code errors autonomously on a disposable/new copy once the failed operation and resulting state are established. Each retry needs a specific correction or new evidence, a new job and explicit logs. Stop after three attempts without new evidence or ten minutes without progress. If state cannot be established, stop writes immediately and report that uncertainty. Do not repeat partially executed writes.

Patch mismatches, wrong paths and Python/DelphiScript syntax errors are the agent's responsibility, not automatic permission questions. When logs suggest a network/provider/tool/version constraint, notify the user promptly with facts and hypotheses. Do not claim that VPN or an old Altium version caused the failure without evidence. Ask for AI workaround versus human handoff when human action or a new strategy is required; honor a path already chosen in the conversation.

Current implementation provides diagnosis, preflight and guarded recovery, not a general exception-catching debugger or universal self-healing. Expand correction recipes only from reproducible failures and successful disposable tests.
