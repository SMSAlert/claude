---
description: Verify an OTP that SMS Alert sent to a mobile number
argument-hint: <mobile number> <code>
---

Use the `sms-alert` skill to verify an OTP.

Request: $ARGUMENTS

1. Take the mobile number and the code from the request. If either is missing, ask for it. Only use a code the user gave you.
2. Run `otp-verify --mobileno <number> --code <code>`.
3. The API returns `"status":"success"` whether or not the code is right, so read `description.desc`:
   - `Code Matched successfully.` means the OTP is valid. Say it is verified.
   - `Code does not match.` means it is wrong. Say so and offer to send a new OTP with `/sms-alert:send-otp`.
4. Any `"status":"error"` response (for example an invalid API key or an expired OTP) should be reported as is, without guessing the cause.
