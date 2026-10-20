/* Disclaimer for every book, test, and hypnosis page.
   To use on any page, add this one line just before </body>:
     <script src="/disclaimer.js"></script>
   It appears in the spot marked <div data-disclaimer></div>, or at the very top of the page if there is no spot. */
(function () {
  var html =
    '<p><b>Please read before you begin.</b> I am a certified coach, not a therapist. The thoughts and opinions in my books, assessments, and hypnosis recordings are for reflection and personal growth. They are not therapy, diagnosis, or treatment, and they are not a substitute for professional mental health care. The assessments are not clinical or diagnostic tools.</p>' +
    (document.querySelector('audio') ? '<p>Do not listen to hypnosis recordings while driving, operating machinery, or doing anything that needs your full attention. If you have a history of seizures or a serious mental health condition, talk with your doctor before using hypnosis.</p>' : '') +
    '<p>Please take what resonates and leave the rest.</p>' +
    '<p>If you are in crisis, in the U.S. call or text 988, or call 911.</p>';
  var slot = document.querySelector('[data-disclaimer]');
  var box = document.createElement('aside');
  box.className = 'elc-disclaimer';
  box.setAttribute('role', 'note');
  box.setAttribute('aria-label', 'Disclaimer');
  box.innerHTML = html;
  // Page without the site styles (e.g. a standalone book or test file): style it inline
  if (!document.querySelector('link[href*="styles.css"]')) {
    box.style.cssText = 'font:15px/1.6 system-ui,-apple-system,Segoe UI,sans-serif;color:#2b1a2e;background:#F4E7E1;border-left:4px solid #A34054;padding:14px 18px;margin:0;';
    var ps = box.querySelectorAll('p'); for (var i = 0; i < ps.length; i++) ps[i].style.margin = '0 0 6px';
  }
  if (slot) { slot.replaceWith(box); return; }
  document.body.insertBefore(box, document.body.firstChild);
})();
