# WP11 — Session boundaries defined by the binding, and the raw-binding envelope: detailed sub-plan

Parent: `plans_and_notes/draft-0.2-candidates.md`, candidates 1 and 3.
Status: decisions E1–E4 taken 2026-11-19, all as recommended. **Drafted 2026-11-19:**
- OI-59 and D-459, with STA-4 redefined around sessions;
- the handler renamed to `on_session_start`;
- BP-53 (the envelope), BP-53a (session control) and BP-56 (session events per binding);
- the interpreter's `session_start`, `session_end` and `expect raw` forms;
- the test run-026.

## 1. The problem

**Candidate 1, a language change.** Session state and volatile resources are tied to *power-on* and *security reset*:
- STA-4: session defaults are applied at power-on;
- STA-6: the `on_power_on` handler;
- RTF-9 and PLT-19: a security reset clears session state;
- BP-14 and BP-55 in the profile.

That is card-centric. In a TEE application on a microcontroller (TrustZone-M), power-on is device boot, while clients open and close sessions many times between boots. Today, session state would outlive the client that created it.

**Candidate 3, a profile change.** The raw binding (BP-53) delivers the outcome as a pair (category, code), but leaves its encoding to the platform. Host software is therefore not portable between raw platforms.

## 2. Design

### 2.1 Sessions (candidate 1)

The language gets a defined term, a **session**:

- **A session starts and ends at events the platform's transport binding defines.**
  - At a *session start*, every `session` global holds `default(T)`, before any application code runs. The session-start handler runs then (E1).
  - At a *session end*, session state, volatile keys and session operations are discarded.
- **A security reset ends every application's session**, as now (RTF-9).
- **Sessions do not overlap within an application** (E2).
- **Rules that change:**
  - STA-4 and STA-6;
  - RTF-9 and RTF-12 ("the next initialization" becomes "the next session start");
  - PLT-18 (the platform defines its session events) and PLT-19;
  - chapter 1's glossary;
  - in the profile: BP-14 (volatile keys and `Session` operations live for a session) and BP-55.
- **What each binding defines** as the session start:

  | Binding | Session start | Session end |
  |---|---|---|
  | ISO 7816 | Power-on (the card's reset and ATR), and the first power-on after a security reset. This is unchanged | Power-off, or a security reset. Deselection does not end a session (BP-55) |
  | Raw | The host opens a session through the host interface (E4) | The host closes it, the device powers off, or a security reset |

- **Behaviour on a card is unchanged.** Only the vocabulary moves into the binding.

### 2.2 The raw-binding envelope (candidate 3)

**Recommendation:** a fixed response envelope (E3). The request stays the raw message:

```text
response = category (1 byte) || code (2 bytes, big-endian) || data
  category 0x00  success          code 0x0000   data = the count bytes the command returned
  category 0x01  application error  code = the member's code   data empty
  category 0x02  platform error   code = the CardError code (§4)  data empty
  category 0x03  trap             code 0x0000   data empty
```

- **Reporting the trap kind** stays platform-defined, as PLT-10 already says. A platform may use the code field for it in a later version.
- **No response at all** follows from a security reset or a power loss (RTF-10), as on a card.
- **Session control** (E4): the host interface has two operations, open session and close session. Their encoding is platform-defined, because they are not application messages. The interpreter models them as scenario steps.

## 3. Work

1. **Language:** STA-4, STA-6, RTF-9, RTF-12, PLT-18, PLT-19 and the glossary; open issue OI-59 and decision D-459.
2. **Profile:** BP-14, BP-53 (the envelope), BP-55, and the §12 answers.
3. **Handler rename** (if E1 is (a)), across the spec, the predeclared names (NAM-14, LEX-15, STA-8), the checkers, the interpreter, the tests and the FIDO2 applet.
4. **Interpreter:**
   - the scenario steps `session_start` and `session_end`. `power_on` becomes the ISO binding's name for `session_start`, so existing scenarios keep working;
   - for tests with `binding: raw`, an `expect raw <hex>` form that checks the encoded envelope.
5. **Tests:**
   - a raw-binding runtime test that checks the envelope for each category, and that session state is reset at each `session_start` but survives across commands within a session;
   - an ISO test confirming that the behaviour is unchanged.
6. Run all checks, and update the candidates list.

## 4. Decisions needed

| ID | Question | Options | Recommendation |
|---|---|---|---|
| E1 | The session-start handler's name | (a) rename the placeholder `on_power_on` to `on_session_start` everywhere. It is a placeholder (D-438), and the name would otherwise be wrong outside cards; (b) keep `on_power_on`, and give it the meaning "at every session start" | (a) |
| E2 | Concurrent sessions | (a) at most one session per application at a time: a new session start ends the previous session. Session globals keep exactly one instance; (b) several concurrent sessions, one session-state instance per client | (a). (b) changes the meaning of every `session` global, and the command model. Revisit when a TEE target needs it |
| E3 | The raw response envelope | (a) `category ‖ code(2) ‖ data`, as in §2.2; (b) leave it platform-defined, as now | (a) |
| E4 | Session events in the raw binding | (a) explicit open and close session operations in the host interface, encoded by the platform; (b) only power-on and security reset, as on a card | (a) |
