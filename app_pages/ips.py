import re

def compute_ips_screen(fund_blocks, is_passive_fn):
    """
    fund_blocks: list of dicts, each with "Fund Name" and "Metrics" (same shape as in existing session_state)
    is_passive_fn: callable taking fund name -> bool, to decide passive vs active behavior

    Returns: list of dicts per fund with:
      - individual criterion booleans
      - overall status ("Passed IPS Screen", "Informal Watch (IW)", "Formal Watch (FW)")
      - fail count
    """
    IPS_CRITERIA = [
        "Manager Tenure",
        "Excess Performance (3Yr)",
        "R-Squared (3Yr)",
        "Peer Return Rank (3Yr)",
        "Sharpe Ratio Rank (3Yr)",
        "Sortino Ratio Rank (3Yr)",
        "Tracking Error Rank (3Yr)",
        "Excess Performance (5Yr)",
        "R-Squared (5Yr)",
        "Peer Return Rank (5Yr)",
        "Sharpe Ratio Rank (5Yr)",
        "Sortino Ratio Rank (5Yr)",
        "Tracking Error Rank (5Yr)",
        "Expense Ratio Rank"
    ]

    results = []

    for b in fund_blocks:
        name = b["Fund Name"]
        passive = is_passive_fn(name)
        metrics = {m["Metric"]: m["Info"] for m in b["Metrics"]}
        statuses = {}
        reasons = {}

        # Manager Tenure ≥ 3
        info = metrics.get("Manager Tenure", "")
        yrs = float(re.search(r"(\d+\.?\d*)", info).group(1)) if re.search(r"(\d+\.?\d*)", info) else 0.0
        ok = yrs >= 3
        statuses["Manager Tenure"] = ok
        reasons["Manager Tenure"] = f"{yrs} yrs {'≥3' if ok else '<3'}"

        # Helper to extract numeric pieces
        def extract_percent(s):
            m = re.search(r"([-+]?\d*\.?\d+)%", s)
            return float(m.group(1)) if m else None

        def extract_rank(s):
            m = re.search(r"(\d+)", s)
            return int(m.group(1)) if m else None

        # Map other criteria
        for crit in IPS_CRITERIA[1:]:
            if "Excess Performance" in crit:
                key = crit  # uses exact naming convention assumption
                info = next((v for k, v in metrics.items() if crit.split()[0] in k), "")
                val = extract_percent(info) or 0.0
                ok = val > 0
                statuses[crit] = ok
                reasons[crit] = f"{val}%"
            elif "R-Squared" in crit:
                info = next((v for k, v in metrics.items() if "R-Squared" in k or "R-Squared" in k), "")
                pct = extract_percent(info) or 0.0
                ok = (pct >= 95) if passive else True
                statuses[crit] = ok
                reasons[crit] = f"{pct}%"
            elif "Peer Return" in crit or "Sharpe Ratio" in crit or "Sortino Ratio" in crit:
                info = next((v for k, v in metrics.items() if crit.split()[0] in k), "")
                rank = extract_rank(info) or 999
                if "Sortino" in crit and not passive:
                    ok = rank <= 50
                elif "Tracking Error" in crit and passive:
                    ok = rank < 90
                else:
                    ok = rank <= 50
                statuses[crit] = ok
                reasons[crit] = f"Rank {rank}"
            elif "Tracking Error" in crit:
                info = next((v for k, v in metrics.items() if "Tracking Error" in k), "")
                rank = extract_rank(info) or 999
                if passive:
                    ok = rank < 90
                else:
                    ok = True
                statuses[crit] = ok
                reasons[crit] = f"Rank {rank}"
            elif "Expense Ratio" in crit:
                info = next((v for k, v in metrics.items() if "Expense Ratio" in k), "")
                rank = extract_rank(info) or 999
                ok = rank <= 50
                statuses[crit] = ok
                reasons[crit] = f"Rank {rank}"
            else:
                # fallback: mark as fail
                statuses[crit] = False
                reasons[crit] = "Unknown"

        fails = sum(1 for v in statuses.values() if not v)
        if fails <= 4:
            overall = "Passed IPS Screen"
        elif fails == 5:
            overall = "Informal Watch (IW)"
        else:
            overall = "Formal Watch (FW)"

        results.append({
            "Fund Name": name,
            "Is Passive": passive,
            "Statuses": statuses,
            "Reasons": reasons,
            "Fail Count": fails,
            "Overall": overall
        })

    return results
