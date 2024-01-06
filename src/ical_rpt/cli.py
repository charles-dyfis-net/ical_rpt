import argparse
import csv
import fnmatch
import functools
import os.path
import sys
import typing

import icalendar
import icalendar.cal
import icalendar.prop
from icalendar.prop import vText
import httpx

ap = argparse.ArgumentParser()
ap.add_argument(
    "--use-addresses",
    action="append",
    type=str,
    help="A glob to match email addresses for attendeees to include in the report; can call several times",
)
ap.add_argument("ical_uri_or_file")
ap.add_argument("output_file")


def require_match(glob_list: list[str], value: str) -> bool:
    for glob in glob_list:
        if fnmatch.fnmatch(value, glob):
            return True
    return False


def main():
    args = ap.parse_args()

    if args.use_addresses:
        require_match_fn = functools.partial(require_match, args.use_addresses)
    else:
        require_match_fn = lambda _: True

    ical_src = args.ical_uri_or_file
    ical_content: str
    if os.path.exists(ical_src):
        ical_content = open(ical_src, "r").read()
    else:
        req = httpx.get(ical_src)
        req.raise_for_status()
        ical_content = req.text
    cal = icalendar.Calendar.from_ical(ical_content)

    if args.output_file == "-":
        dest_file = sys.stdout
    else:
        dest_file = open(args.output_file, "w")
    writer = csv.writer(dest_file)

    for event in cal.walk("VEVENT"):
        assert isinstance(event, icalendar.cal.Event)
        summary = event.get("SUMMARY", None)
        if summary is None:
            continue
        assert isinstance(summary, vText)

        startTime = event.decoded("DTSTART")

        attendees = event.get("ATTENDEE", None)
        if attendees is None:
            continue
        if not isinstance(attendees, (list, tuple)):
            attendees = [attendees]
        attendees: list[icalendar.prop.vCalAddress]
        reportable_attendees: typing.Iterable[str] = [
            str(attendee).removeprefix("mailto:") for attendee in attendees
        ]
        if args.use_addresses:
            reportable_attendees = filter(require_match_fn, reportable_attendees)

        for attendee in reportable_attendees:
            writer.writerow((str(startTime), str(summary).strip(), attendee))
    pass


if __name__ == "__main__":
    main()
