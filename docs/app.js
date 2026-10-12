(function () {
  const $ = id => document.getElementById(id);
  const esc = s => s.replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const pretty = n => n.replace(/^\d+-/, '').replace(/-/g, ' ');
  for (const ex of EXAMPLES) {
    const b = document.createElement('button');
    b.textContent = pretty(ex.name);
    b.onclick = () => { $('msg').value = ex.text; run(); };
    $('samples').appendChild(b);
  }
  function highlight(text, hits) {
    // mark the union of all matched ranges (matches can overlap)
    const marks = new Array(text.length).fill(false);
    for (const h of hits) for (const pat of h.rule.patterns) {
      const re = new RegExp(pat, 'gi'); let m;
      while ((m = re.exec(text)) !== null) { for (let i = m.index; i < m.index + m[0].length; i++) marks[i] = true; if (!m[0].length) re.lastIndex++; }
    }
    let out = '', on = false;
    for (let i = 0; i < text.length; i++) {
      if (marks[i] !== on) { out += marks[i] ? '<mark>' : '</mark>'; on = marks[i]; }
      out += esc(text[i]);
    }
    return out + (on ? '</mark>' : '');
  }
  function run() {
    const text = $('msg').value.trim();
    if (!text) { $('out').innerHTML = ''; return; }
    const hits = SecondLook.scan(text), v = SecondLook.verdict(hits);
    const cls = v.split(' ')[0];
    let h = `<div class="card"><p class="verdict ${cls}">${v === 'Stop' ? 'STOP' : v === 'Be careful' ? 'BE CAREFUL' : 'LOOKS OK'}</p>`;
    h += hits.length ? hits.map(x => `<div class="hit ${x.rule.severity}"><span class="tag">${x.rule.severity}</span> <b>${esc(x.rule.title)}</b><br>${esc(x.rule.why)}<br><small>matched: ${x.evidence.map(e => '“' + esc(e) + '”').join(', ')}</small></div>`).join('')
                    : '<p>No known payment-trap patterns found.</p>';
    h += `<p class="tag">Suggested reply (fixed safe reply)</p><div class="reply">${esc(FALLBACK_REPLY[v])}</div>`;
    h += `<p class="tag" style="margin-top:14px">The message, with matches highlighted</p><div style="white-space:pre-wrap">${highlight(text, hits)}</div></div>`;
    $('out').innerHTML = h;
  }
  const pre = EXAMPLES.find(e => location.hash === '#' + e.name);
  if (pre) { $('msg').value = pre.text; run(); }
  $('go').onclick = run;
  $('clear').onclick = () => { $('msg').value = ''; $('out').innerHTML = ''; };
})();
