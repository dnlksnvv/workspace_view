from bson import ObjectId
from datetime import datetime, timedelta

def find_closest_meeting(conferences, expected_start, expected_end, tolerance_minutes=60):
    closest_meeting = None
    closest_start_diff = timedelta.max
    closest_end_diff = timedelta.max
    expected_start = datetime.strptime(expected_start, "%Y-%m-%dT%H:%M:%S%z")
    expected_end = datetime.strptime(expected_end, "%Y-%m-%dT%H:%M:%S%z")
    print(f"Expected Start: {expected_start}, Expected End: {expected_end}")
    tolerance = timedelta(minutes=tolerance_minutes)

    for conference in conferences:
        start_time = datetime.strptime(conference['start'], "%Y-%m-%dT%H:%M:%S%z")
        end_time = datetime.strptime(conference['end'], "%Y-%m-%dT%H:%M:%S%z")
        print(f"Start Time: {start_time}, End Time: {end_time}")

        start_diff = abs(start_time - expected_start)
        end_diff = abs(end_time - expected_end)

        if start_diff <= tolerance and end_diff <= tolerance:
            if start_diff < closest_start_diff or end_diff < closest_end_diff:
                closest_meeting = conference
                closest_start_diff = start_diff
                closest_end_diff = end_diff

                print(f"Closest Meeting: {closest_meeting}")

    return closest_meeting
