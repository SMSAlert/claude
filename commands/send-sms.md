---
description: Send an SMS through SMS Alert (asks for confirmation first)
argument-hint: <mobile number(s)> <message> [sender ID]
---

Use the `sms-alert` skill to send an SMS.

Request: $ARGUMENTS

1. Work out the recipient number(s), the message text and the sender ID from the request. If the sender ID is missing, run `senders` and ask which approved sender to use.
2. Show the sender, every recipient and the exact message, then ask for a clear yes before sending.
3. After approval, run `send` and report the `batchid` and the per-message status from `batch_dtl`.
