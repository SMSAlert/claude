# SMS Alert API reference

Condensed from https://kb.smsalert.co.in/developers-api/. All endpoints live under `https://www.smsalert.co.in/api/` and take `apikey` as a parameter (sent by the helper script from `SMSALERT_API_KEY`). Responses are JSON with `"status": "success"` or `"status": "error"` and a `description`.

Wherever possible the helper script is used instead of raw HTTP: `python3 smsalert.py <command> --param value`.

## HTTP status codes

| Code | Meaning |
| --- | --- |
| 200 | OK |
| 202 | Request accepted |
| 400 | Malformed request or missing parameter |
| 401 | Missing or invalid credentials |
| 402 | Not available on your plan, or usage limit exceeded |
| 403 | Valid credentials, but no access to the resource |
| 404 | Not found |
| 409 | Conflict (concurrent update) |
| 429 | Too many requests |
| 5xx | Server error, retry |

Some errors are returned with HTTP 200 and `"status":"error"` (for example "no template available for your account"), so always check the JSON `status`.

## Account

| Command | Method, endpoint | Params |
| --- | --- | --- |
| `profile` | POST `user.json` | none |
| `balance` | GET `creditstatus.json` | none |
| `senders` | GET `senderlist.json` | none |

- `balance` success: `{"status":"success","description":{"desc":"transactional:85-nondnd:5","routes":[{"route":"transactional","display_name":"Transactional","credits":"85"}]}}`
- `senders` success: `{"status":"success","description":[{"Senderid":{"sender":"TESTIN","approved":true,"open":true,"datetime":"..."}}]}`. Error: `no senderid available for your account`.
- `profile` error when expired: `{"status":"error","description":"account expired."}`

## Send and schedule

| Command | Method, endpoint | Params |
| --- | --- | --- |
| `send` | POST `push.json` | `sender`*, `mobileno`*, `text`*, `schedule`, `reference`, `dlrurl` |
| `edit-schedule` | POST `modifyschedule.json` | `batchid`*, `schedule`* |
| `cancel-schedule` | POST `cancelschedule.json` | `batchid`* |

`*` required. `mobileno` can be with or without country code, comma-separated for several numbers. `schedule` format is `YYYY-MM-DD HH:MM:SS`. `reference` and `dlrurl` (callback URL for delivery reports) are optional.

- `send` success: `{"status":"success","description":{"desc":"1 messages scheduled for delievery","batchid":"32720261","batch_dtl":[{"mobileno":"8010551055","msgid":"91167733","status":"AWAITED-DLR"}]}}`. Keep the `batchid`. Per-message `status` values seen in the docs include `AWAITED-DLR` and `BLACKLST`.
- `send` error: `{"status":"error","description":"invalid api key"}` (401), `{"status":"error","description":"sms text can not be blank"}` (400).
- `edit-schedule` success: `campaign updated successfully.`
- `cancel-schedule` success: `campaign stopped successfully and credits are refunded.`

Not covered by the docs page that was read: a bulk JSON send format and route/type/unicode parameters for `push.json`. An XML push endpoint (`xmlpush.json`) exists but is not wrapped by the helper script.

## Reports

| Command | Method, endpoint | Params |
| --- | --- | --- |
| `report` | POST `smscampaignlog.json` | `limit`, `page`, `q`, `schedule` |
| `pull` | POST `pull.json` | `batchid`*, `schedule`, `sender`, `text` |

- `pull` success: `{"status":"success","description":{"desc":"displaying 1 to 1 records","report":[{"msgid":"4359345","status":"DELIVRD"}]}}`

## OTP

| Command | Method, endpoint | Params |
| --- | --- | --- |
| `otp-send` | POST `mverify.json` | `mobileno`*, `template`* (must contain `[otp]`), `sender` |
| `otp-verify` | POST `mverify.json` | `mobileno`*, `code`* |

- Template attributes: `[otp length="6" retry="2" validity="10"]`. Defaults: length 4 (allowed 3 to 8), retry 5, validity 15 minutes.
- `otp-send` errors: `OTP length should be between 3 and 8`; `Max OTP limit reached, please try after 15 minutes`.
- `otp-verify` returns `"status":"success"` in both cases. Read `description.desc`: `Code Matched successfully.` or `Code does not match.`

## Templates

| Command | Method, endpoint | Params |
| --- | --- | --- |
| `templates` | GET `templatelist.json` | `order`, `page`, `limit` |
| `template-create` | POST `createtemplate.json` | `name`*, `text`* |
| `template-edit` | POST `updatetemplate.json` | `id`*, `name`*, `text`* |
| `template-delete` | POST `deletetemplate.json` | `id`* |

Errors seen: `no template available for your account`, `invalid template`.

## Groups

| Command | Method, endpoint | Params |
| --- | --- | --- |
| `groups` | GET `grouplist.json` | `limit`, `page`, `q`, `order` |
| `group-create` | POST `creategroup.json` | `name`* |
| `group-edit` | POST `updategroup.json` | `id`*, `name`* |
| `group-delete` | POST `deletegroup.json` | `id`* |
| `group-send` | POST `grouppush.json` | `id`* (comma-separated), `sender`*, `text`*, `route`, `schedule` |

Group names allow only letters, numbers, hyphen and underscore (no spaces). Errors seen: `Group already exists`, `no groups available for your account`.

## Contacts

| Command | Method, endpoint | Params |
| --- | --- | --- |
| `contacts` | GET `contactlist.json` | `group_id`*, `limit`, `page`, `order` |
| `contact-create` | POST `createcontact.json` | `grpname`*, `name`*, `number`* |
| `contact-edit` | POST `updatecontact.json` | `id`*, `name`*, `number`* |
| `contact-delete` | POST `deletecontact.json` | `id`* |

Errors seen: `group does not exist`, `no contacts in this group`. A bulk contact import endpoint (`createcontactxml.json`, XML in a `data` field) exists but is not wrapped by the helper script.

## Short URLs

| Command | Method, endpoint | Params |
| --- | --- | --- |
| `shorten` | POST `createshorturl.json` | `url`* |
| `shorten-delete` | POST `deleteshorturl.json` | `id`* |

`shorten` returns the short link under `description.data.Link.short_url` and an `id` used for deletion.

## Known documentation inconsistencies

The docs page mixes `http` and `https` and `www` and non-`www` hosts, and a few example URLs are malformed. The helper script always uses `https://www.smsalert.co.in`. The docs list Contact List as GET in the parameter table but some samples show POST, and Send to Group uses `id` in the table but `group=` in some samples. If a call fails for one of these, check the live dashboard docs or contact SMS Alert support.

## Intentionally not wrapped

Register, Forgot Password, Change Password and Update Profile are account-security operations and are left out of the plugin on purpose.
