import datetime as dt
import json
import os
import urllib.request
from pathlib import Path

USERNAME = os.getenv("GITHUB_USERNAME", "Deepesh2606")
TOKEN = os.getenv("GITHUB_TOKEN", "")
OUT_PATH = Path("data/contributions.json")

GRAPHQL_QUERY = """
query($login: String!) {
  user(login: $login) {
    repositories(privacy: PUBLIC, isFork: false) {
      totalCount
    }
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks {
          contributionDays {
            date
            contributionCount
            contributionLevel
          }
        }
      }
    }
  }
}
"""

LEVEL_MAP = {
    "NONE": 0,
    "FIRST_QUARTILE": 1,
    "SECOND_QUARTILE": 2,
    "THIRD_QUARTILE": 3,
    "FOURTH_QUARTILE": 4,
}


def fetch_from_github() -> dict:
    payload = json.dumps({"query": GRAPHQL_QUERY, "variables": {"login": USERNAME}}).encode()
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=payload,
        headers={
            "Authorization": f"Bearer {TOKEN}",
            "Content-Type": "application/json",
            "User-Agent": "readme-card-bot",
        },
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        raw = json.loads(resp.read().decode())

    user = raw["data"]["user"]
    cal = user["contributionsCollection"]["contributionCalendar"]
    days = []
    for week in cal["weeks"]:
        for d in week["contributionDays"]:
            days.append(
                {
                    "date": d["date"],
                    "count": d["contributionCount"],
                    "level": LEVEL_MAP.get(d["contributionLevel"], 0),
                }
            )
    return {
        "username": USERNAME,
        "public_repos": user["repositories"]["totalCount"],
        "total": cal["totalContributions"],
        "days": days,
    }


def generate_fallback() -> dict:
    today = dt.date.today()
    start = today - dt.timedelta(days=364)
    days = []
    total = 0
    for i in range(365):
        cur = start + dt.timedelta(days=i)
        val = (cur.day * 3 + cur.month * 5 + cur.weekday() * 2) % 9
        count = 0 if val < 3 else val - 2
        level = 0 if count == 0 else min(4, (count + 1) // 2)
        total += count
        days.append({"date": cur.isoformat(), "count": count, "level": level})
    return {
        "username": USERNAME,
        "public_repos": 14,
        "total": total,
        "days": days,
    }


def summarize(raw: dict) -> dict:
    days = sorted(raw["days"], key=lambda x: x["date"])
    active_days = sum(1 for d in days if d["count"] > 0)

    streak = 0
    for idx in range(len(days) - 1, -1, -1):
        if days[idx]["count"] > 0:
            streak += 1
        elif idx == len(days) - 1:
            continue
        else:
            break

    best_streak = 0
    running = 0
    for d in days:
        if d["count"] > 0:
            running += 1
            best_streak = max(best_streak, running)
        else:
            running = 0

    busiest = max(days, key=lambda d: d["count"], default={"date": "", "count": 0})

    monthly_map = {}
    for d in days:
        ym = d["date"][:7]
        monthly_map[ym] = monthly_map.get(ym, 0) + d["count"]

    months = []
    for ym in sorted(monthly_map.keys())[-12:]:
        dt_obj = dt.date.fromisoformat(f"{ym}-01")
        months.append({"ym": ym, "label": dt_obj.strftime("%b").upper(), "count": monthly_map[ym]})

    return {
        "username": raw["username"],
        "updated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "public_repos": raw["public_repos"],
        "total": raw["total"],
        "active_days": active_days,
        "current_streak": streak,
        "best_streak": best_streak,
        "busiest_day": busiest,
        "months": months,
        "days": days,
    }


def main() -> None:
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    raw = fetch_from_github() if TOKEN else generate_fallback()
    summary = summarize(raw)
    OUT_PATH.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"Wrote {OUT_PATH} (total={summary['total']}, streak={summary['current_streak']})")


if __name__ == "__main__":
    main()
