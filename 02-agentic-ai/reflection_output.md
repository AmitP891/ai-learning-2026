# Reflection run

| Req | First draft passes rules | After reflection passes rules | Reflection rounds |
| --- | --- | --- | --- |
| REQ-002 | 1/1 | 1/1 | 3 |
| REQ-003 | 5/5 | 2/2 | 3 |
| REQ-004 | 3/3 | 3/3 | 3 |
| REQ-005 | 2/2 | 1/1 | 3 |
| REQ-007 | 1/1 | 1/1 | 3 |
| REQ-008 | 3/3 | 1/1 | 3 |

**Fully passing: 6/6 without reflection, 6/6 with reflection.**

## REQ-002
Original: The system shall be fast.

- Round 0: (first draft)
    - [PASS] The system shall respond to 95 percent [assumed] of user-initiated requests within 2 seconds [assumed] of request receipt, measured under a load of 100 [assumed] concurrent users.
- Round 1: The draft passes the rule check and every invented value is tagged. The one weak spot is that 'respond' does not say when the response counts as finished (first byte or complete), so two testers could measure different things. The rewrite fixes that without adding any new values.
    - [PASS] The system shall deliver the complete response to 95 percent [assumed] of user-initiated requests within 2 seconds [assumed] of request receipt, measured under a load of 100 [assumed] concurrent users.
- Round 2: The draft passes the rule-checker and every invented value is tagged, but it is not fully clean. Reading 'fast' as response time is itself an unflagged assumption, and the end point of the measurement ('complete response') is loosely defined. The load condition is also written as a measurement note rather than an operating condition of the requirement.
    - [PASS] While serving 100 [assumed] concurrent users, the system shall send the last byte of the response to 95 percent [assumed] of user-initiated requests within 2 seconds [assumed] of receiving the request.
- Round 3: The draft passes the rule check and every invented value is tagged [assumed]. Two small weaknesses remain: the start of the timing window ('receiving the request') is ambiguous, and '95 percent' lacks 'at least', so it could be read as exactly 95 percent. The draft also quietly interprets 'fast' as interactive response time, which the original never stated, so that interpretation needs stakeholder confirmation.
    - [PASS] While serving 100 [assumed] concurrent users, the system shall send the last byte of the response to at least 95 percent [assumed] of user-initiated requests within 2 seconds [assumed] of receiving the last byte of the request.

## REQ-003
Original: The display should be user-friendly.

- Round 0: (first draft)
    - [PASS] The display shall enable a first-time operator who has received 15 minutes [assumed] of training to complete each of the 10 [assumed] core tasks listed in the operator task list with a success rate of at least 90 % [assumed].
    - [PASS] The display shall achieve a System Usability Scale score of at least 75 points [assumed] when rated by a panel of at least 10 [assumed] representative operators.
    - [PASS] The display shall render all text with a character height of at least 4 mm [assumed] when viewed from a distance of 500 mm [assumed].
    - [PASS] The display shall present a visible response to each operator input within 200 ms [assumed] of that input.
    - [PASS] The display shall render text with a contrast ratio of at least 4.5:1 [assumed] against its background.
- Round 1: The rule-checker passes every line, but it cannot judge intent or verifiability. Response time (200 ms) and contrast (4.5:1) are my own additions that 'user-friendly' did not clearly ask for. The first requirement also points to an undefined 'operator task list', and the panel size in the SUS requirement is a verification condition, not a product requirement.
    - [PASS] The display shall enable a first-time operator who has received 15 minutes [assumed] of training to complete each of the 10 [assumed] core tasks in the operator task list [assumed: document to be defined] with a success rate of at least 90 % [assumed].
    - [PASS] The display shall achieve a System Usability Scale score of at least 75 points [assumed].
    - [PASS] The display shall render all text with a character height of at least 4 mm [assumed] when viewed from a distance of 500 mm [assumed].
- Round 2: The rule checker only tests form, and the draft still has content problems. The character-height requirement adds a legibility requirement the original never asked for. The task-success requirement does not say whether 90 % applies per task or overall, or what counts as 'success', and the SUS requirement does not say whether the score is a mean or an individual result. The two usability requirements remain as faithful readings of 'user-friendly', but their ambiguities are now resolved and the test conditions moved into the verification.
    - [PASS] The display shall enable first-time operators who have received 15 minutes [assumed] of training to complete each of the 10 [assumed] core tasks in the operator task list [assumed: document to be defined] with a success rate of at least 90 % [assumed] per task.
    - [PASS] The display shall achieve a mean System Usability Scale score of at least 75 points [assumed] on the 0–100 scale.
- Round 3: The checker passed both statements, but the first fixes a count of 10 tasks while pointing to a task list that doesn't exist yet, so the count may contradict the list. The second gives no operator population or training level, so a mean SUS score can't be reproduced. Neither statement says how it will be verified, such as sample size or test conditions.
    - [PASS] The display shall enable first-time operators who have completed 15 minutes [assumed] of training to complete each core task in the operator task list [assumed: document to be defined] with a success rate of at least 90 % [assumed] per task.
    - [PASS] The display shall achieve a mean System Usability Scale score of at least 75 points [assumed] on the 0–100 scale when rated by first-time operators who have completed 15 minutes [assumed] of training.

## REQ-004
Original: The logger shall store at least 72 hours of data and shall encrypt it and shall upload it daily.

- Round 0: (first draft)
    - [PASS] The logger shall store at least 72 hours of recorded data in non-volatile memory.
    - [PASS] The logger shall encrypt all stored data using AES with a 256-bit [assumed] key length.
    - [PASS] The logger shall upload stored data to the data server once every 24 hours, with a tolerance of ±1 hour [assumed].
- Round 1: The rule checker passes all three, but the draft breaks checklist item 2 and part of item 3. 'Non-volatile memory' and 'to the data server' add design constraints the original never asked for. 'AES' is an invented choice left untagged, with only the key length tagged. The ±1 hour tolerance is also new, though it is at least tagged.
    - [PASS] The logger shall store at least 72 hours of recorded data.
    - [PASS] The logger shall encrypt all stored data using AES [assumed] with a 256-bit [assumed] key.
    - [PASS] The logger shall upload stored data once every 24 hours, with a tolerance of ±1 hour [assumed].
- Round 2: The rule checker passes all three, but the draft still breaks checklist item 2: it invents an algorithm (AES) and a ±1 hour tolerance that REQ-004 never asked for, and it reads 'daily' as an exact 24-hour period without flagging that as an interpretation. The rewrite below drops the algorithm and the tolerance, keeps the one number the checklist needs for encryption (key length), and uses 'at least once every 24 hours' so no extra tolerance is needed.
    - [PASS] The logger shall store at least 72 hours of recorded data.
    - [PASS] The logger shall encrypt all stored data using a key length of at least 256 bits [assumed].
    - [PASS] The logger shall upload stored data at least once every 24 hours [assumed interpretation of 'daily'].
- Round 3: The rule-checker only tests wording, so its PASS verdicts don't cover the intent checks. The 256-bit key length is an invented value that goes beyond the original's bare 'encrypt'. It is tagged [assumed] and the checklist asks for a number and unit, so I kept it, but it needs stakeholder confirmation. The [assumed] tags also sit at the end of the sentences, so it is unclear which value each one covers. I moved each tag next to its value.
    - [PASS] The logger shall store at least 72 hours of recorded data.
    - [PASS] The logger shall encrypt all stored data using a key length of at least 256 bits [assumed].
    - [PASS] The logger shall upload stored data at intervals of no more than 24 hours [assumed interpretation of 'daily'].

## REQ-005
Original: Battery life shall be adequate for typical missions.

- Round 0: (first draft)
    - [PASS] The battery shall provide a continuous operating endurance of at least 120 minutes [assumed] when discharged from 100% state of charge to 20% state of charge [assumed] under the reference mission load profile at an ambient temperature of 20 °C [assumed].
    - [PASS] The reference mission load profile shall be defined as an average electrical load of 50 W [assumed] with a peak load of 120 W [assumed] lasting no more than 30 seconds [assumed] per occurrence.
- Round 1: The draft passes the rule-checker but still has gaps. The second sentence is a definition of test conditions written as a 'shall', so it is not a capability and gives a second 'shall' for one need. The peak load has no occurrence rate, so the profile cannot be reproduced exactly. The draft also silently reads 'battery life' as per-charge endurance rather than cycle or calendar life, and it does not say so. Splitting the profile from the endurance figure also weakens traceability.
    - [PASS] The battery shall supply the reference mission load profile, defined as an average load of 50 W [assumed] with peaks of up to 120 W [assumed] lasting no more than 30 s [assumed] each and totalling no more than 10 % [assumed] of the run time, for at least 120 min [assumed] when discharged from 100 % [assumed] to 20 % [assumed] state of charge at an ambient temperature of 20 °C [assumed].
- Round 2: The draft passes the rule-checker but over-reaches: the original only asked for adequate battery life for typical missions, yet the draft invents a peak-load profile, a 20 % end-of-discharge state of charge, and an ambient temperature, for ten [assumed] values in one sentence. That makes the requirement hard to confirm with stakeholders and hard to test. The rewrite keeps one measurable endurance figure and one load figure, each tagged [assumed].
    - [REVIEW] The battery shall supply the typical mission average load of 50 W [assumed] for at least 120 min [assumed] from a full charge. (Vague, untestable wording: typical)
- Round 3: The draft still uses the vague word 'typical' ('typical mission average load'), which the rule-checker flagged. It also never defines the load or the conditions (temperature, end-of-discharge cutoff), so the requirement can't be tested as written. The 50 W and 120 min values are tagged [assumed], which is correct, but the mission load needs a defined reference profile in place of 'typical'.
    - [PASS] The battery shall supply a constant load of 50 W [assumed] for at least 120 min [assumed] from a full charge, at an ambient temperature of 20 °C [assumed], before reaching its end-of-discharge voltage.

## REQ-007
Original: The data upload rate shall be TBD.

- Round 0: (first draft)
    - [PASS] The system shall sustain a data upload rate of at least 10 Mbit/s [assumed] measured as average application-layer throughput over a continuous 60-second [assumed] interval.
- Round 1: The draft passes the rule-checker, but 'application-layer throughput' is an invented measurement basis with no [assumed] tag, and 'sustain' adds a duration obligation the original never stated. The 10 Mbit/s value and the averaging interval are placeholders for the original TBD and need stakeholder confirmation.
    - [PASS] The system shall provide a data upload rate of at least 10 Mbit/s [assumed], averaged over a 60-second [assumed] interval.
- Round 2: The wording is acceptable: one 'shall', a number and unit, and both invented values (10 Mbit/s, 60 s) are tagged [assumed]. The 60-second averaging window is the only addition, and it is needed to make the rate measurable. The weakness is that the draft gave no verification method, and the assumed values still need stakeholder confirmation to replace the original TBD.
    - [PASS] The system shall provide a data upload rate of at least 10 Mbit/s [assumed], averaged over a 60-second [assumed] interval.
- Round 3: The draft is well-formed: one 'shall', a number with a unit, a measurable averaging window, and both invented values tagged [assumed]. The remaining weaknesses are that the upload path and test conditions are unspecified, and the 60-second window is an extra parameter the original never mentioned. I kept it only because the rate can't be measured without one, and both [assumed] values need stakeholder confirmation to replace the original TBD.
    - [PASS] The system shall provide a data upload rate of at least 10 Mbit/s [assumed], averaged over a 60-second [assumed] interval.

## REQ-008
Original: The logger may support Bluetooth if appropriate.

- Round 0: (first draft)
    - [PASS] The logger shall establish a Bluetooth Low Energy connection with a paired host device within 10 s [assumed] at a separation distance of 5 m [assumed] in line of sight.
    - [PASS] The logger shall transfer stored log data to a connected host device over Bluetooth Low Energy at a throughput of at least 20 kbit/s [assumed].
    - [PASS] The logger shall switch off its Bluetooth radio within 5 s [assumed] of receiving a disable command through its configuration interface.
- Round 1: The rule checker passed all three, but the draft added requirements the original never asked for (data transfer throughput, a disable command and radio switch-off), and it chose Bluetooth Low Energy without tagging that as assumed. The vague 'if appropriate' was also replaced by an unstated decision to include Bluetooth, which needs stakeholder confirmation.
    - [PASS] The logger shall establish a Bluetooth Low Energy [assumed] connection with a paired host device within 10 s [assumed] at a separation distance of up to 5 m [assumed] in line of sight.
- Round 2: The checker passes, but the draft breaks checklist item 2: the original only said the logger may support Bluetooth, and the draft invents Low Energy, pairing, a 5 m range and line of sight. Only some of these are tagged [assumed], so 'paired' and 'line of sight' are untagged inventions. The draft also silently resolves the 'may … if appropriate' optionality into a mandatory 'shall', which the stakeholder must confirm.
    - [PASS] The logger shall establish a Bluetooth connection with a host device within 10 s [assumed] of connection initiation.
- Round 3: The draft passes the rule checks, but it turns 'may support... if appropriate' into a mandatory shall without flagging that decision, and it gives no test conditions (such as distance), so the 10 s figure can't be repeatably verified. The rewrite adds a tagged distance condition; the shall/mandatory decision should still be confirmed with the stakeholder.
    - [PASS] When a host device is within 1 m [assumed] of the logger, the logger shall establish a Bluetooth connection with the host device within 10 s [assumed] of connection initiation.

