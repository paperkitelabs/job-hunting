/* Off-campus application list. Plain JS, no build step. */
(function () {
  "use strict";

  var JOBS = (window.JOBS || []).slice();
  var COS = (window.COMPANIES || []).slice();
  var sort = "priority", view = "apply", city = "all", q = "", open = null;

  var TIER_LABEL = {
    1: "Apply first — BFSI, risk and analyst roles you clear",
    2: "Apply — consulting arms and BFSI-adjacent",
    3: "Stretch — referral first, then apply",
    4: "Live, but off your current direction",
    8: "Closed since the last check",
    9: "Checked and rejected earlier"
  };
  function tierOf(j) { return j.tier || 4; }

  // LinkedIn people searches for finding a referrer. Search pages only; nothing is sent.
  function liSearch(words) {
    return "https://www.linkedin.com/search/results/people/?keywords=" + encodeURIComponent(words) + "&origin=GLOBAL_SEARCH_HEADER";
  }

  function esc(s) {
    var d = document.createElement("div");
    d.textContent = s == null ? "" : String(s);
    return d.innerHTML;
  }

  var CITIES = ["Mumbai", "Bengaluru", "Hyderabad", "Pune", "Gurgaon", "Chennai", "Remote"];
  function cityOf(j) {
    var s = ((j.location || "") + " " + (j.company || "")).toLowerCase();
    if (/bangalore|bengaluru/.test(s)) return "Bengaluru";
    if (/mumbai|thane|vashi/.test(s)) return "Mumbai";
    if (/hyderabad|telangana/.test(s)) return "Hyderabad";
    if (/pune/.test(s)) return "Pune";
    if (/gurgaon|gurugram|delhi|noida/.test(s)) return "Gurgaon";
    if (/chennai/.test(s)) return "Chennai";
    if (/remote|virtual/.test(s)) return "Remote";
    return "Other";
  }

  var SPEED_RANK = { fast: 0, medium: 1, slow: 2 };

  function passes(j) {
    if (city !== "all" && cityOf(j) !== city) return false;
    if (q) {
      var hay = (j.title + " " + j.company + " " + j.location + " " + (j.why || "") + " " +
                 (j.team || "") + " " + (j.years_bar || "")).toLowerCase();
      if (hay.indexOf(q) === -1) return false;
    }
    var isLive = j.live !== "closed";
    switch (view) {
      case "all": return true;
      case "no": return j.status === "rejected" || j.eligible === "no";
      case "closed": return j.live === "closed";
      case "intern": return isLive && j.type === "internship" && j.eligible !== "no";
      case "grad": return isLive && j.type === "graduate" && j.eligible !== "no";
      case "clear": return isLive && j.eligible === "yes";
      case "pay15": return isLive && (j.ctc_hi || 0) >= 15 && j.eligible !== "no";
      default: return isLive && j.status !== "rejected" && j.eligible !== "no";
    }
  }

  function sorted(list) {
    var l = list.slice();
    if (sort === "priority") l.sort(function (a, b) { return tierOf(a) - tierOf(b) || (a.tier_order || 99) - (b.tier_order || 99) || b.chance - a.chance || b.score - a.score; });
    else if (sort === "chance") l.sort(function (a, b) { return b.chance - a.chance || b.score - a.score; });
    else if (sort === "pay") l.sort(function (a, b) { return (b.ctc_hi || 0) - (a.ctc_hi || 0) || b.score - a.score; });
    else if (sort === "speed") l.sort(function (a, b) {
      return (SPEED_RANK[a.speed] || 1) - (SPEED_RANK[b.speed] || 1) || b.chance - a.chance;
    });
    else if (sort === "deadline") l.sort(function (a, b) {
      return (b.deadline ? 1 : 0) - (a.deadline ? 1 : 0) || b.score - a.score;
    });
    else l.sort(function (a, b) { return b.score - a.score || b.chance - a.chance; });
    return l;
  }

  var TYPE_LABEL = { internship: "Internship", graduate: "Graduate programme", fulltime: "Full-time" };

  function rowHtml(j, i) {
    var id = "j" + j.rank, isOpen = open === id;
    var elClass = j.eligible === "yes" ? "yes" : (j.eligible === "stretch" ? "stretch" : "no");
    var elText = j.eligible === "yes" ? "eligible" : (j.eligible === "stretch" ? "stretch" : "below the bar");
    var pay = j.type === "internship" ? "stipend" : (j.ctc_lo + "–" + j.ctc_hi);

    var h = '<button class="row' + (j.eligible === "no" ? " out" : "") + '" data-id="' + id +
      '" aria-expanded="' + isOpen + '">' +
      '<span class="rk">' + (i + 1) + '</span>' +
      '<span><span class="t">' + esc(j.title) + '</span>' +
        '<span class="m">' +
          '<span class="co">' + esc(j.company) + '</span>' +
          '<span>' + esc(j.location || cityOf(j)) + '</span>' +
          '<span>' + TYPE_LABEL[j.type] + '</span>' +
          '<span class="' + elClass + '">' + elText + '</span>' +
          (j.live === "closed" ? '<span class="no">closed</span>' : '') +
          (j.deadline && j.live !== "closed" ? '<span class="no">deadline</span>' : '') +
          (j.status === "verified" ? '<span>verified</span>' : '') +
          (j.status === "unscreened" ? '<span>unscreened</span>' : '') +
        '</span></span>' +
      '<span class="num"><span class="big">' + j.score + '</span><span class="sm">match</span>' +
        '<span class="big">' + j.chance + '%</span><span class="sm">chance</span>' +
        '<span class="big">' + pay + '</span><span class="sm">' + (j.type === "internship" ? "" : "LPA") + '</span>' +
      '</span></button>';

    if (isOpen) {
      var d = "";
      function add(k, v, cls) { if (v) d += '<dt>' + k + '</dt><dd' + (cls ? ' class="' + cls + '"' : '') + '>' + esc(v) + '</dd>'; }
      add("Priority", j.tier_note);
      add("Bar", j.years_bar);
      if (j.deadline) add("Deadline", j.deadline, "warn");
      add("Why you", j.why);
      add("Gaps", j.gaps, "warn");
      add("Learn first", j.learnable);
      add("Timing", j.timing);
      add("Pay", j.ctc_note);
      add("Referral", j.referral);
      add("Ruling", j.ruling);
      add("Source", j.source);
      add("Checked", j.checked ? j.checked + " — " + (j.live || "") + (j.live_evidence ? " (" + j.live_evidence + ")" : "") : "");
      d += '</dl>';
      var refs = "";
      if (j.live !== "closed" && j.status !== "rejected") {
        var team = j.li_team || j.company;
        refs = '<div class="refs"><span class="ctl-label">Find a referrer</span>' +
          '<a href="' + esc(liSearch(j.company + " Dwarkadas J. Sanghvi")) + '" target="_blank" rel="noopener">DJSCE alumni at ' + esc(j.company) + '</a>' +
          '<a href="' + esc(liSearch(team)) + '" target="_blank" rel="noopener">People in this team</a>' +
          '<a href="' + esc(liSearch(j.company + " campus recruiter India")) + '" target="_blank" rel="noopener">Recruiters</a></div>';
      }
      h += '<div class="det"><dl>' + d + refs +
        (j.url && j.live !== "closed" ? '<a class="apply" href="' + esc(j.url) + '" target="_blank" rel="noopener">Open the posting and apply →</a>' : '') +
        '</div>';
    }
    return h;
  }

  function render() {
    var list = sorted(JOBS.filter(passes));
    var host = document.getElementById("list");
    if (!list.length) {
      host.innerHTML = '<p class="empty">Nothing matches that combination. Try a wider filter.</p>';
    } else {
      var html = "", lastGrp = null;
      list.forEach(function (j, i) {
        var g = sort === "priority" ? TIER_LABEL[tierOf(j)]
          : sort === "score"
          ? (j.score >= 80 ? "Strongest matches" : j.score >= 65 ? "Good matches" : j.score >= 45 ? "Worth a look" : "Weak or already rejected")
          : sort === "chance"
            ? (j.chance >= 75 ? "Best odds" : j.chance >= 55 ? "Reasonable odds" : j.chance >= 35 ? "Long shots" : "Very unlikely")
            : sort === "pay"
              ? ((j.ctc_hi || 0) >= 25 ? "25+ LPA" : (j.ctc_hi || 0) >= 15 ? "15–25 LPA" : "Under 15 LPA")
              : sort === "speed"
                ? ({ fast: "Fast processes", medium: "Medium", slow: "Slow" }[j.speed] || "Medium")
                : (j.deadline ? "Has a deadline" : "Rolling");
        if (g !== lastGrp) { html += '<p class="grp">' + g + '</p>'; lastGrp = g; }
        html += rowHtml(j, i);
      });
      host.innerHTML = html;
    }
    document.getElementById("count").textContent =
      list.length + " of " + JOBS.length + " shown";
  }

  function renderStats() {
    var live = JOBS.filter(function (j) { return j.live === "live"; });
    var closed = JOBS.filter(function (j) { return j.live === "closed"; }).length;
    var t1 = live.filter(function (j) { return j.tier === 1; }).length;
    var t2 = live.filter(function (j) { return j.tier === 2; }).length;
    var cos = {}; live.forEach(function (j) { cos[j.company] = 1; });
    document.getElementById("stats").innerHTML =
      "<b>" + live.length + "</b> openings still live across <b>" + Object.keys(cos).length + "</b> employers &nbsp;·&nbsp; " +
      "<b>" + t1 + "</b> to apply to first &nbsp;·&nbsp; <b>" + t2 + "</b> more worth applying &nbsp;·&nbsp; " +
      "<b>" + closed + "</b> closed since September";
  }

  function renderUrgent() {
    var closed = JOBS.filter(function (j) { return j.live === "closed"; }).length;
    document.getElementById("urgent").innerHTML =
      '<h2>Rechecked 27 October 2026</h2>' +
      '<p>Every opening was rechecked against the employer’s own hiring system. <strong>' + closed +
      ' have closed</strong> since 25 September, including the old #1 (Amazon Business Research Analyst), all three ' +
      'Tetriz internships, and both Deutsche Bank / Nomura overseas graduate windows (deadlines passed). ' +
      'The list is now ranked for BFSI, fintech, risk and business-analyst roles first, then consulting arms, then product. ' +
      'Open any row for a priority note and LinkedIn searches to find a referrer.</p>';
  }

  function renderCities() {
    var counts = { all: JOBS.length };
    JOBS.forEach(function (j) { var c = cityOf(j); counts[c] = (counts[c] || 0) + 1; });
    var html = '<button class="lnk" data-city="all" aria-pressed="true">All</button>';
    CITIES.forEach(function (c) {
      if (!counts[c]) return;
      html += '<button class="lnk" data-city="' + c + '" aria-pressed="false">' + c + '</button>';
    });
    document.getElementById("cities").innerHTML = html;
  }

  function renderCompanies() {
    var seen = {}, out = [];
    COS.forEach(function (c) {
      var k = c.name.toLowerCase();
      if (seen[k]) return; seen[k] = 1; out.push(c);
    });
    out.sort(function (a, b) { return (b.ctc_hi || 0) - (a.ctc_hi || 0); });
    document.getElementById("cos").innerHTML = out.map(function (c) {
      var OC = { high: "direct", med: "harder", low: "campus" };
      return '<div class="crow"><div><div class="cn">' +
        (c.url ? '<a href="' + esc(c.url) + '" target="_blank" rel="noopener">' + esc(c.name) + '</a>' : esc(c.name)) +
        '</div>' + (c.dept ? '<div class="cd">' + esc(c.dept) + '</div>' : '') + '</div>' +
        '<div class="cc">' + esc(c.cities || "") + '</div>' +
        '<div class="cp' + ((c.ctc_hi || 0) >= 15 ? " hi" : "") + '">' + c.ctc_lo + '–' + c.ctc_hi + ' LPA</div>' +
        '<div class="co2">' + (OC[c.offcampus] || "") + '</div></div>';
    }).join("");
  }

  function press(sel, el) {
    document.querySelectorAll(sel).forEach(function (b) {
      b.setAttribute("aria-pressed", String(b === el));
    });
  }

  document.addEventListener("click", function (e) {
    var r = e.target.closest(".row");
    if (r) { var id = r.getAttribute("data-id"); open = open === id ? null : id; render(); return; }
    var b = e.target.closest(".lnk");
    if (!b) return;
    if (b.dataset.sort) { sort = b.dataset.sort; press("[data-sort]", b); open = null; render(); }
    else if (b.dataset.view) { view = b.dataset.view; press("[data-view]", b); open = null; render(); }
    else if (b.dataset.city) { city = b.dataset.city; press("[data-city]", b); open = null; render(); }
  });

  var qi = document.getElementById("q");
  qi.addEventListener("input", function () { q = qi.value.trim().toLowerCase(); open = null; render(); });

  renderStats(); renderUrgent(); renderCities(); renderCompanies(); render();
})();
