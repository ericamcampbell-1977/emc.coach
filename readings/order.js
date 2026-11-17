/* Order forms for readings.
   SETUP (see README section "Readings"):
   1. FORM_ENDPOINT: paste your Formspree (or Cloudflare Worker) URL. Until then, the form opens a ready-to-send email instead.
   2. Each page's <form> has data-stripe="..." : paste the Stripe Payment Link there. Until then, you email a payment link yourself. */
(function () {
  var FORM_ENDPOINT = ''; // e.g. 'https://formspree.io/f/xxxxxxxx'
  var EMAIL = 'evolutionlabcollective@gmail.com';
  var form = document.getElementById('order-form');
  if (!form) return;
  var msg = document.getElementById('form-msg');
  function show(html) { msg.innerHTML = html; msg.hidden = false; msg.scrollIntoView({ behavior: 'smooth', block: 'center' }); }

  form.addEventListener('submit', function (e) {
    e.preventDefault();
    if (form.elements['company'] && form.elements['company'].value) return; // spam trap
    var fd = new FormData(form), lines = [], obj = {};
    fd.forEach(function (v, k) { if (k !== 'company' && v) { obj[k] = v; lines.push(k.replace(/_/g, ' ') + ': ' + v); } });
    var stripe = form.getAttribute('data-stripe');
    var subject = form.getAttribute('data-subject');

    // Birth-time sanity check: must be to the minute
    var t = form.elements['birth_time'];
    if (t && !/^\d{2}:\d{2}$/.test(t.value)) { show('Please enter your birth time to the minute (for example 14:07).'); return; }

    if (FORM_ENDPOINT) {
      obj._subject = subject;
      fetch(FORM_ENDPOINT, { method: 'POST', headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' }, body: JSON.stringify(obj) })
        .then(function (r) { if (!r.ok) throw new Error(r.status); done(); })
        .catch(function () { show('Something went wrong sending that. Please email <a class="text-link" href="mailto:' + EMAIL + '">' + EMAIL + '</a> instead.'); });
    } else {
      window.location.href = 'mailto:' + EMAIL + '?subject=' + encodeURIComponent(subject) + '&body=' + encodeURIComponent(lines.join('\n'));
      show('Your email app should open with your details filled in. Press send to complete your request.');
    }
    function done() {
      form.reset();
      if (stripe) {
        show('Thank you. Your details are in. <a class="btn" style="margin-top:.8rem" href="' + stripe + '" target="_blank" rel="noopener">Continue to payment</a>');
      } else {
        show('Thank you. Your details are in. I will email you a payment link, and your reading follows once payment is received.');
      }
    }
  });
})();
