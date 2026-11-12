---
name: sms-alert
description: Use when the user wants to send an SMS or OTP, schedule or cancel a scheduled SMS, check SMS credits, list sender IDs, manage SMS groups, contacts or templates, shorten a URL, or look up SMS delivery reports through SMS Alert (smsalert.co.in).
---

# SMS Alert

SMS Alert (https://www.smsalert.co.in) is an SMS gateway. This skill lets you operate the account through its HTTP API using the bundled helper script, `scripts/smsalert.py` (Python 3, standard library only).

## Setup

The API key comes from the environment variable `SMSALERT_API_KEY`. It is the API key generated in the user's SMS Alert account.

- Never ask the user to paste the key into chat if it can be set in their environment, never print it, and never write it into a file.
- If the variable is missing, tell the user to set it (`export SMSALERT_API_KEY=...`) and stop.
- Optional: `SMSALERT_BASE_URL` overrides the default `https://www.smsalert.co.in`.

## Running calls

```
python3 "${CLAUDE_PLUGIN_ROOT}/skills/sms-alert/scripts/smsalert.py" <command> [--param value ...]
```

Run `... smsalert.py --help` for the full command list. Add `--dry-run` to print the request (API key masked) without sending it.

| Task | Command |
| --- | --- |
| Check credits | `balance` |
| Account profile | `profile` |
| List approved sender IDs | `senders` |
| Send SMS | `send --sender ID --mobileno N[,N] --text "..."` |
| Schedule SMS | `send ... --schedule "YYYY-MM-DD HH:MM:SS"` |
| Edit / cancel a schedule | `edit-schedule --batchid B --schedule ...`, `cancel-schedule --batchid B` |
| Sent SMS report | `report --limit 10 --page 1` |
| Delivery status of a batch | `pull --batchid B` |
| Send OTP | `otp-send --mobileno N --template "Your OTP is [otp length=\"6\" validity=\"10\"]"` |
| Verify OTP | `otp-verify --mobileno N --code 123456` |
| Templates | `templates`, `template-create`, `template-edit`, `template-delete` |
| Groups | `groups`, `group-create`, `group-edit`, `group-delete`, `group-send` |
| Contacts | `contacts --group_id G`, `contact-create`, `contact-edit`, `contact-delete` |
| Short URLs | `shorten --url ...`, `shorten-delete --id ...` |

Full parameter and response details are in `references/api-reference.md`. Read it when you need a parameter that is not obvious.

## Rules for using it

1. **Confirm before sending.** Sending costs credits and cannot be undone. Before `send`, `group-send` or `otp-send`, show the user the sender ID, every recipient (or the count and group for bulk), and the exact message text, and get a clear yes. A scheduled message needs the same confirmation, including the send time.
2. **Check what you are sending from.** If the user has not named a sender ID, run `senders` and ask which approved one to use. Do not invent one.
3. **Check credits before large sends.** Run `balance` first when sending to many numbers.
4. **Read the response, not just the status.** The API can answer `"status":"success"` while individual messages carry a status such as `AWAITED-DLR` (accepted, awaiting delivery report) or `BLACKLST` (blocked). Report per-message results from `batch_dtl`, and give the `batchid` so the user can cancel a schedule or pull delivery status later.
5. **Keep OTP codes out of chat.** For `otp-send`, the `template` must contain `[otp]`. Defaults are length 4, 5 retries and 15 minutes validity, changeable with `[otp length="6" retry="2" validity="10"]`. Only call `otp-verify` with a code the user gives you.
6. **Destructive actions need a yes.** Deleting groups, contacts, templates or short URLs, and cancelling schedules, need explicit confirmation naming the item.
7. **Account security endpoints are deliberately not included.** This plugin does not change passwords, register accounts or trigger password resets. Send the user to the SMS Alert dashboard for those.
8. **Messages for Indian numbers** generally have to use a registered sender ID and a template approved for that route. If a send is rejected or blocked, say so and suggest checking the sender and template in the SMS Alert dashboard or with SMS Alert support rather than retrying blindly.
9. **Do not spam.** Decline to send unsolicited bulk messages. SMS Alert has a no-spam policy at https://kb.smsalert.co.in/tos/.
10. Phone numbers can be given with or without the country code. Multiple numbers are comma-separated.

## Errors

- `401` / `"invalid api key"` or `"invalid username/password."`: the key is wrong or the account is inactive. Ask the user to check `SMSALERT_API_KEY`.
- `"account expired."`: the account has expired and needs renewing in the dashboard.
- `400` with `"sms text can not be blank"` and similar: a required parameter is missing or empty.
- `429`: too many requests; wait and retry once.
- `5xx`: server error on SMS Alert's side; retry once, then report it.
