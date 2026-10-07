---
name: obstacle-recovery
description: Diagnose failed development or tool operations, repair agent code autonomously, distinguish external system constraints, and stop unproductive retry loops.
---

Repair patch mismatches, syntax, imports and wrong local paths autonomously. A routine agent code error is not a reason to hand work to the user.

When evidence suggests external constraints (VPN/proxy/network, provider authentication, unavailable capability, application version/API mismatch), perform a short relevant read-only diagnosis and notify the user promptly. Separate observed facts from hypotheses; an HTTP error does not prove a VPN issue, and a CAD error does not prove version incompatibility.

Continue within a path already authorized. Ask for AI workaround versus a concrete human next step when human action or a materially different strategy is required. Do not ask again for ordinary repairs inside the selected path.

Track attempts at the same obstacle. Stop after three attempts without new evidence, or ten minutes without measurable progress. State what was tested, what remains uncertain, and the two feasible next paths. Do not manufacture an AI path if none is available. A new corrective change or discriminating diagnostic is required for each retry.

For ambiguous writes/timeouts, inspect logs and actual saved/unsaved state before retrying. Preserve user documents and checkpoints. Never replay an uncertain mutation, restart a dirty editor, or modify VPN/accounts to troubleshoot without the corresponding authorization.
