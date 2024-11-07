from datetime import datetime, timedelta

def process_time(time_range):
    start_time_str, end_time_str = time_range.split(' - ')
    start_time = datetime.strptime(start_time_str, "%H:%M")
    end_time = datetime.strptime(end_time_str, "%H:%M")
    start_time_12 = start_time.strftime("%I:%M")
    start_period = start_time.strftime("%p")

    duration = end_time - start_time
    duration_hours = duration.seconds // 3600
    duration_minutes = (duration.seconds % 3600) // 60
    if duration_minutes > 45:
        duration_minutes_rounded = 0
        duration_hours += 1
    else:
        duration_minutes_rounded = ((duration_minutes + 14) // 15) * 15 % 60

    return start_time_12, start_period, duration_hours, duration_minutes_rounded


