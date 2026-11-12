---
description: Send an OTP via SMS Alert, or verify a code the user received
argument-hint: send <mobile number> | verify <mobile number> <code>
---

Use the `sms-alert` skill.

Request: $ARGUMENTS

- For `send`: confirm the number with the user, then run `otp-send` with a template containing `[otp]` (for example `Your OTP is [otp length="6" validity="10"]`). Do not display any OTP value.
- For `verify`: run `otp-verify` with the number and the code the user provided, and read `description.desc` to say whether it matched.
