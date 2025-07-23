def step3_process_scorecard(pdf, start_page, declared_total):
    # collect all "Fund Scorecard" pages
    pages = []
    for p in pdf.pages[start_page-1:]:
        txt = p.extract_text() or ""
        if "Fund Scorecard" in txt:
            pages.append(txt)
        else:
            break
    lines = "\n".join(pages).splitlines()

    # skip down to after "Criteria Threshold"
    idx = next((i for i,l in enumerate(lines) if "Criteria Threshold" in l), None)
    if idx is not None:
        lines = lines[idx+1:]

    fund_blocks = []
    curr_name = None
    curr_metrics = []
    capturing = False

    metric_re = re.compile(r"^(Manager Tenure|.*?)\s+(Pass|Review)\s+(.+)$")

    for i, line in enumerate(lines):
        line = line.strip()
        # start of a new fund block: capture the Manager Tenure line too
        if line.startswith("Manager Tenure"):
            # save previous
            if curr_name:
                fund_blocks.append({"Fund Name": curr_name, "Metrics": curr_metrics})
            # new fund name is the previous non-empty line
            prev = lines[i-1].strip()
            curr_name = re.sub(r"Fund (Meets Watchlist Criteria|has been placed.*)", "", prev).strip()
            curr_metrics = []
            capturing = True

            # also capture the tenure metric itself
            m = metric_re.match(line)
            if m:
                metric, _, info = m.groups()
                curr_metrics.append({"Metric": metric, "Info": info})

        elif capturing:
            # stop if we've got all 14
            if len(curr_metrics) >= 14:
                capturing = False
                continue
            if not line or "Fund Scorecard" in line:
                continue
            m = metric_re.match(line)
            if m:
                metric, _, info = m.groups()
                curr_metrics.append({"Metric": metric, "Info": info})

    # append last fund
    if curr_name and curr_metrics:
        fund_blocks.append({"Fund Name": curr_name, "Metrics": curr_metrics})

    st.session_state["fund_blocks"] = fund_blocks

    # Step 3.5: Key Numbers & Notes
    st.subheader("Step 3.5: Key Details per Fund")
    perf_pattern = re.compile(r"\b(outperformed|underperformed)\b.*?(\d+\.?\d+%?)", re.IGNORECASE)
    peer_phrases = [
        "within it's Peer Group",
        "percentile rank",
        "as calculated against it's Benchmark"
    ]

    for b in fund_blocks:
        st.markdown(f"### {b['Fund Name']}")
        for m in b["Metrics"]:
            info = m["Info"]
            # pull any numbers
            nums = re.findall(r"[-+]?\d*\.\d+%?|\d+%?", info)
            nums_str = ", ".join(nums) if nums else "—"
            # performance notes
            perf_notes = "; ".join(f"{grp[0].capitalize()} {grp[1]}" 
                                   for grp in perf_pattern.findall(info))
            # peer/benchmark context
            context = "; ".join(p for p in peer_phrases if p.lower() in info.lower())
            bullet = f"- **{m['Metric']}**: {nums_str}"
            if perf_notes:
                bullet += f"; {perf_notes}"
            if context:
                bullet += f"; {context}"
            st.write(bullet)

    # Step 3.6: count validation
    st.subheader("Step 3.6: Investment Option Count")
    extracted = len(fund_blocks)
    st.write(f"- Declared: **{declared_total}**")
    st.write(f"- Extracted: **{extracted}**")
    if extracted == declared_total:
        st.success("✅ Counts match.")
    else:
        st.error(f"❌ Mismatch: expected {declared_total}, found {extracted}.")
