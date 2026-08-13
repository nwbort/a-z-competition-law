/* A–Z Competition Law Dictionary — tiny progressive enhancement layer.
   Everything here is optional: the site is fully browsable with JS disabled.
   No network requests, no cookies, no local storage, no analytics. */
(function () {
  'use strict';

  var terms = window.AZ_TERMS || [];
  var root = document.documentElement;
  var base = root.getAttribute('data-root') || '';

  /* ---- Surprise me ---------------------------------------------------- */
  /* Letting an anchor resolve the link gives the absolute path the browser
     would actually navigate to, so a term can be compared against the current
     page whatever prefix data-root carries and however deep the page sits.
     Directory URLs and their index.html spelling are the same page. */
  var pathOf = function (href) {
    var a = document.createElement('a');
    a.href = href;
    return a.pathname.replace(/index\.html$/, '');
  };

  var dice = document.querySelector('[data-random]');
  if (dice && terms.length) {
    dice.hidden = false;
    dice.addEventListener('click', function (ev) {
      ev.preventDefault();
      /* Never pick the page being read. If that leaves nothing — one word in
         the dictionary, and you are on it — staying put is the only move. */
      var here = pathOf(location.href);
      var pool = terms.filter(function (t) { return pathOf(base + t.url) !== here; });
      if (!pool.length) pool = terms;
      var pick = pool[Math.floor(Math.random() * pool.length)];
      window.location.href = base + pick.url;
    });
  }

  /* ---- Search --------------------------------------------------------- */
  var form = document.querySelector('[data-search]');
  if (!form || !terms.length) return;

  var input = form.querySelector('input');
  var list = document.querySelector('[data-results]');
  var browse = document.querySelector('[data-browse]');
  var status = document.querySelector('[data-search-status]');
  if (!input || !list) return;

  form.hidden = false;
  form.addEventListener('submit', function (ev) { ev.preventDefault(); });

  var norm = function (s) {
    return String(s).toLowerCase().replace(/[^a-z0-9 ]+/g, ' ').replace(/\s+/g, ' ').trim();
  };

  var haystacks = terms.map(function (t) {
    return norm([t.term, t.aka, t.blurb, (t.tags || []).join(' ')].join(' '));
  });

  var score = function (t, hay, q) {
    var name = norm(t.term);
    var aka = norm(t.aka || '');
    if (name === q) return 0;
    if (name.indexOf(q) === 0) return 1;
    if (aka.indexOf(q) === 0) return 2;
    if (name.indexOf(q) > -1) return 3;
    if (hay.indexOf(q) > -1) return 4;
    return -1;
  };

  var render = function () {
    var q = norm(input.value);
    list.textContent = '';

    if (!q) {
      if (browse) browse.hidden = false;
      if (status) status.textContent = '';
      return;
    }
    if (browse) browse.hidden = true;

    var hits = [];
    for (var i = 0; i < terms.length; i++) {
      var s = score(terms[i], haystacks[i], q);
      if (s > -1) hits.push({ t: terms[i], s: s });
    }
    hits.sort(function (a, b) {
      return a.s - b.s || a.t.term.localeCompare(b.t.term);
    });

    if (!hits.length) {
      var none = document.createElement('p');
      none.className = 'no-results';
      none.textContent = '🫥 No match for “' + input.value.trim() + '” — it may be a letter we have not reached yet!';
      list.appendChild(none);
      if (status) status.textContent = 'No matches.';
      return;
    }

    hits.slice(0, 30).forEach(function (h) {
      var a = document.createElement('a');
      a.className = 'result';
      a.href = base + h.t.url;
      var b = document.createElement('b');
      b.textContent = h.t.term;
      a.appendChild(b);
      if (h.t.aka) {
        var sp = document.createElement('span');
        sp.textContent = h.t.aka;
        a.appendChild(sp);
      }
      list.appendChild(a);
    });

    if (status) {
      status.textContent = hits.length + (hits.length === 1 ? ' match' : ' matches') + '.';
    }
  };

  input.addEventListener('input', render);

  /* Press "/" anywhere to jump to the search box. */
  document.addEventListener('keydown', function (ev) {
    if (ev.key !== '/' || ev.metaKey || ev.ctrlKey || ev.altKey) return;
    var el = document.activeElement;
    var tag = el && el.tagName;
    if (tag === 'INPUT' || tag === 'TEXTAREA' || (el && el.isContentEditable)) return;
    ev.preventDefault();
    input.focus();
    input.select();
  });

  render();
})();
