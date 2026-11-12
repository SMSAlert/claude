# SMS Alert plugin for Claude

Operate your [SMS Alert](https://www.smsalert.co.in) account from Claude: send SMS and OTP, schedule and cancel messages, manage groups, contacts and templates, shorten URLs, and read delivery reports.

It is built from the official [SMS Alert developer API](https://kb.smsalert.co.in/developers-api/) and needs no server and no third-party packages. It uses Python 3 (standard library only).

## What is inside

| Path | Purpose |
| --- | --- |
| `.claude-plugin/plugin.json` | Plugin manifest |
| `.claude-plugin/marketplace.json` | Lets you publish this repo as its own marketplace |
| `skills/sms-alert/SKILL.md` | Instructions and safety rules Claude follows |
| `skills/sms-alert/scripts/smsalert.py` | API helper (`--help` lists every command) |
| `skills/sms-alert/references/api-reference.md` | Parameter and response details |
| `commands/send-sms.md` | `/sms-alert:send-sms` |
| `commands/check-balance.md` | `/sms-alert:check-balance` |
| `commands/send-otp.md` | `/sms-alert:send-otp` |

## Setup

1. Get your API key from your SMS Alert account.
2. Set it in the environment where Claude Code runs:
   ```bash
   export SMSALERT_API_KEY="your-api-key"
   ```
3. Try the plugin locally:
   ```bash
   claude --plugin-dir ./sms-alert
   ```
   Then ask, for example: "check my SMS Alert balance", or run `/sms-alert:send-sms`.

## Safety

- Claude shows the sender, recipients and exact text and waits for your yes before it sends anything.
- The API key is read from the environment and is never printed or stored.
- Password change, registration and password reset endpoints are deliberately not included.

## Test without sending anything

```bash
python3 skills/sms-alert/scripts/smsalert.py send \
  --sender TESTIN --mobileno 9876543210 --text "Hello" --dry-run
```

`--dry-run` prints the request with the API key masked and sends nothing.

## Publish

- Your own marketplace: push this folder to a git repository and users run
  `claude plugin marketplace add <your-repo>` then
  `claude plugin install sms-alert@sms-alert-marketplace`.
- Anthropic's community marketplace: run `claude plugin validate .`, then submit through the plugin directory submission form.

## Known limits

- The docs page mixes `http` and `https` hosts and has a few inconsistent examples. The helper always calls `https://www.smsalert.co.in`.
- Bulk JSON send, the XML push endpoint and bulk contact import are not wrapped. Ask SMS Alert for their current formats if you need them.
