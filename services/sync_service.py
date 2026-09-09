from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

IST = ZoneInfo("Asia/Kolkata")

# Placeholder schedule. Replace with the exact source/schedule used by the server.
def next_expected_sync(now=None):
    now = now or datetime.now(IST)
    targets = {
        "Pokémon GO": (23, 20),
        "Ingress / Wayfarer map": (3, 45),
    }
    result = {}
    for name, (hour, minute) in targets.items():
        candidate = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if candidate <= now:
            candidate += timedelta(days=1)
        mins = int((candidate - now).total_seconds() // 60)
        result[name] = f"{candidate:%I:%M %p} IST (about {mins} min)"
    return result
