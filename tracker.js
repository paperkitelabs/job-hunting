/* Application tracker: renders window.TRACKER as a sheet with progress checkboxes.
   Shared by every monthly applications-*.html page. Plain JS, no build step. */
(function () {
  "use strict";

  // A page can carry several sheets (tabs) in window.TRACKER_SHEETS; ?sheet=<key> picks one.
  var SHEETS = window.TRACKER_SHEETS, T;
  if (SHEETS) {
    var keys = Object.keys(SHEETS).sort(function (a, b) { return (SHEETS[a].order || 0) - (SHEETS[b].order || 0); });
    var want = new URLSearchParams(location.search).get("sheet");
    var cur = SHEETS[want] ? want : keys[0];
    T = SHEETS[cur];
    var tabs = document.getElementById("sheets");
    if (tabs) tabs.innerHTML = keys.map(function (k) {
      return '<a href="?sheet=' + k + '"' + (k === cur ? ' aria-current="page"' : '') + '>' +
        (SHEETS[k].tab || k).replace(/&/g, "&amp;").replace(/</g, "&lt;") + ' <small>' + SHEETS[k].jobs.length + '</small></a>';
    }).join("");
  } else {
    T = window.TRACKER || { jobs: [], tiers: {} };
  }
  var KEY = "apptracker:" + T.edition;
  var STEPS = [
    ["sent", "Sent LinkedIn request"],
    ["accepted", "Request accepted"],
    ["dm", "DM'd about referral"],
    ["replied", "Replied"],
    ["referral", "Got referral"],
    ["applied", "Applied"]
  ];
  var q = "", track = "all";
  var COLS = 17;
  function isAI(j) { return j.tier === "ai" || j.tier === "ai2"; }

  // Ticks live in this browser's storage; the page still works if storage is blocked.
  var state = {};
  try { state = JSON.parse(localStorage.getItem(KEY) || "{}") || {}; } catch (e) { state = {}; }
  function persist() {
    try { localStorage.setItem(KEY, JSON.stringify(state)); } catch (e) { /* storage blocked */ }
  }
  function rec(id) { return state[id] || (state[id] = {}); }

  function esc(s) {
    var d = document.createElement("div");
    d.textContent = s == null ? "" : String(s);
    return d.innerHTML;
  }
  function li(words) {
    return "https://www.linkedin.com/search/results/people/?keywords=" + encodeURIComponent(words) + "&origin=GLOBAL_SEARCH_HEADER";
  }

  function visible(j) {
    if (track === "ai" && !isAI(j)) return false;
    if (track === "analyst" && isAI(j)) return false;
    if (!q) return true;
    return (j.role + " " + j.company + " " + j.location + " " + j.jd + " " + j.job_id).toLowerCase().indexOf(q) !== -1;
  }

  function rowHtml(j, n) {
    var r = state[j.id] || {};
    var done = STEPS.filter(function (s) { return r[s[0]]; }).length;
    var h = '<tr data-id="' + esc(j.id) + '" class="t' + j.tier + (done === STEPS.length ? " complete" : "") + '">' +
      '<td class="c-num sticky1">' + n + '</td>' +
      '<td class="c-role sticky2"><a href="' + esc(j.url) + '" target="_blank" rel="noopener">' + esc(j.role) + '</a>' +
        (j.deadline ? '<span class="due">Closes ' + esc(j.deadline) + '</span>' : '') +
        (j.type && j.type !== "Full-time" ? '<span class="type">' + esc(j.type) + '</span>' : '') + '</td>' +
      '<td class="c-co">' + esc(j.company) + '</td>' +
      '<td class="c-loc">' + esc(j.location) + '</td>' +
      '<td class="c-res' + (isAI(j) ? " ai" : "") + '">' + esc(j.resume || "") + '</td>' +
      '<td class="c-id">' + esc(j.job_id) + '</td>' +
      '<td class="c-exp">' + esc(j.exp) + '</td>' +
      '<td class="c-pay">' + esc(j.pay) + '</td>' +
      '<td class="c-jd">' + (j.jd ? esc(j.jd) : '<span class="pending">Summary still being written. Open the posting for now.</span>') + '</td>' +
      '<td class="c-ref">' +
        '<a href="' + esc(li(j.company + " Dwarkadas J. Sanghvi")) + '" target="_blank" rel="noopener">DJSCE alumni</a>' +
        '<a href="' + esc(li(j.li || j.company)) + '" target="_blank" rel="noopener">People in this team</a>' +
        '<a href="' + esc(li(j.company + " campus recruiter India")) + '" target="_blank" rel="noopener">Recruiters</a>' +
      '</td>';
    STEPS.forEach(function (s) {
      h += '<td class="c-ck"><input type="checkbox" data-step="' + s[0] + '" aria-label="' + esc(s[1] + " — " + j.role + ", " + j.company) + '"' +
        (r[s[0]] ? " checked" : "") + '></td>';
    });
    h += '<td class="c-note"><textarea rows="2" data-note aria-label="' + esc("Notes — " + j.role + ", " + j.company) + '">' +
      esc(r.note || "") + '</textarea></td></tr>';
    return h;
  }

  function render() {
    var html = "", lastTier = null, n = 0;
    T.jobs.forEach(function (j) {
      if (!visible(j)) return;
      if (j.tier !== lastTier) {
        html += '<tr class="grp"><td colspan="' + COLS + '"><span>' + esc(T.tiers[j.tier] || "") + '</span></td></tr>';
        lastTier = j.tier;
      }
      html += rowHtml(j, ++n);
    });
    document.getElementById("rows").innerHTML = html ||
      '<tr><td colspan="' + COLS + '" class="empty">Nothing matches. Clear the search or switch the track back to All.</td></tr>';
    renderProgress();
  }

  function renderProgress() {
    var total = T.jobs.length;
    var html = STEPS.map(function (s) {
      var c = T.jobs.filter(function (j) { return (state[j.id] || {})[s[0]]; }).length;
      return '<div class="pstep"><span class="pnum">' + c + '<small>/' + total + '</small></span>' +
        '<span class="plabel">' + esc(s[1]) + '</span>' +
        '<span class="pbar"><span style="width:' + (total ? Math.round(c / total * 100) : 0) + '%"></span></span></div>';
    }).join("");
    document.getElementById("progress").innerHTML = html;
  }

  document.getElementById("edition").textContent = "— " + (T.title || "");
  var nAI = T.jobs.filter(isAI).length;
  document.getElementById("meta").textContent = T.meta ? T.meta : T.jobs.length + " live openings (" + (T.jobs.length - nAI) + " analyst & PM, " + nAI +
    " data science & AI) · every link rechecked " + T.checked;
  document.getElementById("leftout").textContent = T.left_out || "";

  var rows = document.getElementById("rows");
  rows.addEventListener("change", function (e) {
    var tr = e.target.closest("tr[data-id]");
    if (!tr || !e.target.dataset.step) return;
    rec(tr.dataset.id)[e.target.dataset.step] = e.target.checked;
    persist();
    var r = state[tr.dataset.id];
    tr.classList.toggle("complete", STEPS.every(function (s) { return r[s[0]]; }));
    renderProgress();
  });
  rows.addEventListener("input", function (e) {
    var tr = e.target.closest("tr[data-id]");
    if (!tr || !e.target.hasAttribute("data-note")) return;
    rec(tr.dataset.id).note = e.target.value;
    persist();
  });

  var qi = document.getElementById("q");
  qi.addEventListener("input", function () { q = qi.value.trim().toLowerCase(); render(); });
  document.querySelector(".seg").addEventListener("click", function (e) {
    var b = e.target.closest("[data-track]");
    if (!b) return;
    track = b.dataset.track;
    document.querySelectorAll("[data-track]").forEach(function (x) { x.setAttribute("aria-pressed", String(x === b)); });
    render();
  });

  function download(name, text, type) {
    var a = document.createElement("a");
    a.href = URL.createObjectURL(new Blob([text], { type: type }));
    a.download = name;
    document.body.appendChild(a); a.click(); a.remove();
    setTimeout(function () { URL.revokeObjectURL(a.href); }, 1000);
  }
  document.getElementById("save").addEventListener("click", function () {
    download("applications-" + T.edition + "-backup.json", JSON.stringify({ edition: T.edition, state: state }, null, 1), "application/json");
  });
  document.getElementById("restore").addEventListener("change", function (e) {
    var f = e.target.files[0];
    if (!f) return;
    f.text().then(function (txt) {
      var d = JSON.parse(txt);
      if (d.edition !== T.edition && !confirm("This backup is from " + d.edition + ", not " + T.edition + ". Load it anyway?")) return;
      state = d.state || {};
      persist(); render();
    }).catch(function () { alert("That file is not a tracker backup."); });
    e.target.value = "";
  });
  document.getElementById("csv").addEventListener("click", function () {
    function cell(v) { v = v == null ? "" : String(v); return /[",\n]/.test(v) ? '"' + v.replace(/"/g, '""') + '"' : v; }
    var head = ["#", "Job role", "Link", "Company", "Location", "Resume to send", "Job ID", T.exp_label || "Experience asked", T.pay_label || "Est. pay (LPA)", "Summarized JD"]
      .concat(STEPS.map(function (s) { return s[1]; })).concat(["Notes"]);
    var lines = [head.map(cell).join(",")];
    T.jobs.forEach(function (j, i) {
      var r = state[j.id] || {};
      lines.push([i + 1, j.role, j.url, j.company, j.location, j.resume, j.job_id, j.exp, j.pay, j.jd]
        .concat(STEPS.map(function (s) { return r[s[0]] ? "Yes" : ""; })).concat([r.note || ""]).map(cell).join(","));
    });
    download("applications-" + T.edition + ".csv", "﻿" + lines.join("\r\n"), "text/csv");
  });

  render();
})();
