------------------------------ MODULE TaskLifecycle ------------------------------
(***************************************************************************)
(* A formal model of the task lifecycle state machine, model-checked by    *)
(* TLC. It mirrors tasks/domain/state_machine.py and entities.transition_to *)
(* and proves the same invariants the code enforces — but over the ENTIRE   *)
(* reachable state space, not a sample.                                     *)
(*                                                                          *)
(* KEEP IN SYNC with the Python transition table (`Allowed`, below). This   *)
(* spec is hand-written, not generated from the code — see ADR-0015 for the *)
(* drift caveat.                                                            *)
(***************************************************************************)

States == {"DRAFT", "ACTIVE", "BLOCKED", "COMPLETED", "ARCHIVED"}

\* Allowed transitions — mirrors _ALLOWED_TRANSITIONS in state_machine.py.
Allowed ==
    [ DRAFT     |-> {"ACTIVE", "ARCHIVED"},
      ACTIVE    |-> {"BLOCKED", "COMPLETED", "ARCHIVED"},
      BLOCKED   |-> {"ACTIVE", "ARCHIVED"},
      COMPLETED |-> {"ACTIVE", "ARCHIVED"},
      ARCHIVED  |-> {} ]

VARIABLES status, completedAt
vars == << status, completedAt >>

TypeOK == status \in States /\ completedAt \in BOOLEAN

Init == status = "DRAFT" /\ completedAt = FALSE

\* Move to a target permitted from the current state, keeping completedAt in
\* lockstep with COMPLETED (entering sets it; leaving clears it) — exactly what
\* Task.transition_to does.
Transition(to) ==
    /\ to \in Allowed[status]
    /\ status' = to
    /\ completedAt' = (to = "COMPLETED")

\* Archiving is available from every non-terminal state; named so we can assert
\* weak fairness on it for the liveness property below.
Archive ==
    /\ "ARCHIVED" \in Allowed[status]
    /\ status' = "ARCHIVED"
    /\ completedAt' = FALSE

Next == \E to \in States : Transition(to)

Spec == Init /\ [][Next]_vars /\ WF_vars(Archive)

--------------------------------------------------------------------------------
\* Safety invariants ("nothing bad ever happens").

\* completed_at is set iff the task is COMPLETED.
CompletedInvariant == completedAt <=> (status = "COMPLETED")

\* ARCHIVED is terminal: no transition leaves it.
ArchivedIsTerminal == (status = "ARCHIVED") => (Allowed[status] = {})

\* No dead ends: every non-terminal state can reach ARCHIVED directly.
NoDeadEnd == (status = "ARCHIVED") \/ ("ARCHIVED" \in Allowed[status])

--------------------------------------------------------------------------------
\* Liveness ("something good eventually happens"): under fair archiving a task is
\* always eventually archived — it can never get permanently stuck.
EventuallyArchived == <>(status = "ARCHIVED")

================================================================================
