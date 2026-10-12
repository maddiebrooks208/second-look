// Port of second_look/rules.py scan() + verdict(). Runs entirely in the browser.
(function (root) {
  const D = typeof module !== 'undefined' ? require('./data.js') : { RULES }; // const globals aren't window props
  function scan(text) {
    const hits = [];
    for (const rule of D.RULES) {
      const found = [];
      for (const pat of rule.patterns) {
        const re = new RegExp(pat, 'gi');
        let m;
        while ((m = re.exec(text)) !== null) {
          found.push(m[0].trim());
          if (m[0].length === 0) re.lastIndex++;
        }
      }
      if (found.length) hits.push({ rule, evidence: [...new Set(found)] });
    }
    return hits;
  }
  function verdict(hits) {
    const high = hits.filter(h => h.rule.severity === 'high').length;
    const medium = hits.filter(h => h.rule.severity === 'medium').length;
    if (high || medium >= 2) return high ? 'Stop' : 'Be careful';
    return medium ? 'Be careful' : 'Looks OK';
  }
  const api = { scan, verdict };
  if (typeof module !== 'undefined') module.exports = api; else root.SecondLook = api;
})(this);
