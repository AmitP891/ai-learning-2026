# Sample run: `requirements_checker.py` (22 Oct 2026)

```
[tool] Claude called list_requirements()
[tool] Claude called check_requirement(REQ-001)  -> PASS
[tool] Claude called check_requirement(REQ-002)  -> REVIEW
[tool] Claude called check_requirement(REQ-003)  -> REVIEW
[tool] Claude called check_requirement(REQ-004)  -> REVIEW
[tool] Claude called check_requirement(REQ-005)  -> REVIEW
[tool] Claude called check_requirement(REQ-006)  -> PASS
[tool] Claude called check_requirement(REQ-007)  -> REVIEW
[tool] Claude called check_requirement(REQ-008)  -> REVIEW
```

**2 requirements passed (REQ-001, REQ-006). 6 need review.**

| ID | Issue | Rewrite |
| --- | --- | --- |
| REQ-002 | "fast" is vague | The system shall respond to any user input within 200 ms [assumed]. |
| REQ-003 | "should" is weak, "user-friendly" is vague | The display shall let a first-time user complete the [assumed] 5 core tasks within 3 minutes [assumed], with a success rate of at least 90% [assumed]. |
| REQ-004 | Three requirements in one statement | 004a: store at least 72 hours of data · 004b: encrypt stored data using AES-256 [assumed] · 004c: upload stored data once every 24 hours [assumed] |
| REQ-005 | "adequate" and "typical" are vague | The battery shall power the logger for at least 12 hours [assumed] of continuous operation at 25 °C [assumed]. |
| REQ-007 | Contains TBD | The logger shall upload data at a rate of at least 1 Mbit/s [assumed]. Confirm this value with the stakeholder. |
| REQ-008 | "may" and "if appropriate" make it optional and untestable | The logger shall support Bluetooth 5.0 [assumed] with a range of at least 10 m [assumed]. If Bluetooth isn't needed, delete the requirement. |

All requirements are synthetic. Values marked [assumed] were invented by Claude and need a human to confirm them.
