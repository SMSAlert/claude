#!/usr/bin/env python3
"""Command-line helper for the SMS Alert HTTP API (https://www.smsalert.co.in).

Standard library only. The API key is read from SMSALERT_API_KEY and is never
printed. Requests follow the SMS Alert developer docs: parameters are sent in
the query string, with GET or POST as documented for each endpoint.

Examples:
  smsalert.py balance
  smsalert.py send --sender TESTIN --mobileno 9876543210 --text "Hello"
  smsalert.py otp-send --mobileno 9876543210 --template 'Your OTP is [otp length="6"]'
  smsalert.py send --sender TESTIN --mobileno 9876543210 --text "Hi" --dry-run
"""
import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

BASE_URL = os.environ.get("SMSALERT_BASE_URL", "https://www.smsalert.co.in").rstrip("/")
TIMEOUT = 30

# name: (HTTP method, path, help, [(param, required, help), ...])
ENDPOINTS = {
    # Account
    "profile": ("POST", "user.json", "Show account profile (also validates the API key)", []),
    "balance": ("GET", "creditstatus.json", "Show remaining credits per route", []),
    "senders": ("GET", "senderlist.json", "List sender IDs available to the account", []),
    # Send and schedule
    "send": ("POST", "push.json", "Send an SMS (add --schedule to schedule it)", [
        ("sender", True, "Approved sender ID"),
        ("mobileno", True, "Recipient number(s), comma-separated"),
        ("text", True, "Message text"),
        ("schedule", False, "Send time, YYYY-MM-DD HH:MM:SS"),
        ("reference", False, "Your reference value for the message"),
        ("dlrurl", False, "Callback URL that receives delivery reports"),
    ]),
    "edit-schedule": ("POST", "modifyschedule.json", "Change the time of a scheduled SMS batch", [
        ("batchid", True, "Batch ID returned when the SMS was scheduled"),
        ("schedule", True, "New send time, YYYY-MM-DD HH:MM:SS"),
    ]),
    "cancel-schedule": ("POST", "cancelschedule.json", "Cancel a scheduled SMS batch (credits are refunded)", [
        ("batchid", True, "Batch ID of the scheduled SMS"),
    ]),
    # Reports
    "report": ("POST", "smscampaignlog.json", "Sent SMS report", [
        ("limit", False, "Records per page (default 10)"),
        ("page", False, "Page number (default 1)"),
        ("q", False, "Search text"),
        ("schedule", False, "Schedule filter"),
    ]),
    "pull": ("POST", "pull.json", "Delivery report for a batch", [
        ("batchid", True, "Batch ID returned by send"),
        ("schedule", False, "Schedule filter"),
        ("sender", False, "Sender filter"),
        ("text", False, "Text filter"),
    ]),
    # OTP
    "otp-send": ("POST", "mverify.json", "Generate and send an OTP", [
        ("mobileno", True, "Recipient number(s)"),
        ("template", True, "Message containing [otp], e.g. 'Your OTP is [otp length=\"6\" validity=\"10\"]'"),
        ("sender", False, "Sender ID (defaults to the account default)"),
    ]),
    "otp-verify": ("POST", "mverify.json", "Validate an OTP the user entered", [
        ("mobileno", True, "Number the OTP was sent to"),
        ("code", True, "OTP entered by the user"),
    ]),
    # Templates
    "templates": ("GET", "templatelist.json", "List SMS templates", [
        ("order", False, "asc or desc"),
        ("page", False, "Page number"),
        ("limit", False, "Records per page"),
    ]),
    "template-create": ("POST", "createtemplate.json", "Create an SMS template", [
        ("name", True, "Template name"),
        ("text", True, "Template text"),
    ]),
    "template-edit": ("POST", "updatetemplate.json", "Edit an SMS template", [
        ("id", True, "Template ID"),
        ("name", True, "Template name"),
        ("text", True, "Template text"),
    ]),
    "template-delete": ("POST", "deletetemplate.json", "Delete an SMS template", [
        ("id", True, "Template ID"),
    ]),
    # Groups
    "groups": ("GET", "grouplist.json", "List contact groups", [
        ("limit", False, "Records per page (default 10)"),
        ("page", False, "Page number (default 1)"),
        ("q", False, "Search text"),
        ("order", False, "asc or desc"),
    ]),
    "group-create": ("POST", "creategroup.json", "Create a group (letters, numbers, hyphen, underscore only)", [
        ("name", True, "Group name"),
    ]),
    "group-edit": ("POST", "updategroup.json", "Rename a group", [
        ("id", True, "Group ID"),
        ("name", True, "New group name"),
    ]),
    "group-delete": ("POST", "deletegroup.json", "Delete a group", [
        ("id", True, "Group ID"),
    ]),
    "group-send": ("POST", "grouppush.json", "Send an SMS to one or more groups", [
        ("id", True, "Group ID(s), comma-separated"),
        ("sender", True, "Approved sender ID"),
        ("text", True, "Message text"),
        ("route", False, "Route, e.g. transactional"),
        ("schedule", False, "Send time, YYYY-MM-DD HH:MM:SS"),
    ]),
    # Contacts
    "contacts": ("GET", "contactlist.json", "List contacts in a group", [
        ("group_id", True, "Group ID"),
        ("limit", False, "Records per page (default 10)"),
        ("page", False, "Page number (default 1)"),
        ("order", False, "asc or desc"),
    ]),
    "contact-create": ("POST", "createcontact.json", "Add a contact to a group", [
        ("grpname", True, "Name of the group to add to"),
        ("name", True, "Contact name"),
        ("number", True, "Mobile number"),
    ]),
    "contact-edit": ("POST", "updatecontact.json", "Edit a contact", [
        ("id", True, "Contact number ID"),
        ("name", True, "Contact name"),
        ("number", True, "Mobile number"),
    ]),
    "contact-delete": ("POST", "deletecontact.json", "Delete a contact", [
        ("id", True, "Contact number ID"),
    ]),
    # Short URLs
    "shorten": ("POST", "createshorturl.json", "Create a short URL", [
        ("url", True, "Long URL"),
    ]),
    "shorten-delete": ("POST", "deleteshorturl.json", "Delete a short URL", [
        ("id", True, "Short URL ID"),
    ]),
}


def die(message, code=2):
    print(f"error: {message}", file=sys.stderr)
    sys.exit(code)


def build_url(path, params):
    query = urllib.parse.urlencode(params, quote_via=urllib.parse.quote)
    return f"{BASE_URL}/api/{path}?{query}"


def call(method, path, params, dry_run=False):
    params = {k: v for k, v in params.items() if v is not None and v != ""}
    if dry_run:
        shown = dict(params, apikey="********")
        print(f"{method} {build_url(path, shown)}")
        return 0

    key = os.environ.get("SMSALERT_API_KEY", "").strip()
    if not key:
        die("SMSALERT_API_KEY is not set. Export your SMS Alert API key and retry.")

    url = build_url(path, dict(params, apikey=key))
    request = urllib.request.Request(
        url,
        method=method,
        data=b"" if method == "POST" else None,
        headers={"User-Agent": "sms-alert-claude-plugin/1.0"},
    )
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
            body = response.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as err:
        # The API returns JSON error details on 4xx/5xx; show them.
        body = err.read().decode("utf-8", errors="replace")
        print(f"HTTP {err.code}", file=sys.stderr)
    except urllib.error.URLError as err:
        die(f"could not reach SMS Alert: {err.reason}", code=1)

    try:
        data = json.loads(body)
    except ValueError:
        print(body)
        return 1
    print(json.dumps(data, indent=2, ensure_ascii=False))
    ok = isinstance(data, dict) and data.get("status") == "success"
    return 0 if ok else 1


def build_parser():
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--dry-run", action="store_true",
                        help="print the request with the API key masked, do not send it")

    parser = argparse.ArgumentParser(
        description="SMS Alert API helper. API key is read from SMSALERT_API_KEY.",
        epilog="Use '<command> --help' for the parameters of each command.",
    )
    sub = parser.add_subparsers(dest="command", metavar="<command>")
    sub.required = True
    for name, (_method, _path, help_text, params) in ENDPOINTS.items():
        p = sub.add_parser(name, help=help_text, description=help_text, parents=[common])
        for param, required, param_help in params:
            p.add_argument(f"--{param}", required=required, help=param_help)
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    method, path, _help, params = ENDPOINTS[args.command]
    values = {param: getattr(args, param) for param, _r, _h in params}

    # The OTP endpoint is shared: the template must contain the [otp] marker.
    if args.command == "otp-send" and "[otp" not in values["template"]:
        die("--template must contain [otp], e.g. 'Your OTP is [otp]'")

    return call(method, path, values, dry_run=args.dry_run)


if __name__ == "__main__":
    sys.exit(main())
