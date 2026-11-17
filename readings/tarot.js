/* Free tarot draw for emc.coach
   Cards are shown as text tiles (no artwork). Meanings are short keyword prompts for reflection.
   Shuffling uses the browser's secure random number generator. */
(function () {
  var MAJOR = [
    ['The Fool', 'a fresh start, trust, a leap with open eyes', 'recklessness, hesitation, ignoring the risk'],
    ['The Magician', 'skill, focus, using what you already have', 'scattered effort, manipulation, untapped talent'],
    ['The High Priestess', 'intuition, quiet knowing, what is not yet said', 'ignoring your gut, secrets, a muddy signal'],
    ['The Empress', 'nurture, abundance, creativity, the body', 'smothering, creative block, neglecting yourself'],
    ['The Emperor', 'structure, authority, steady boundaries', 'rigidity, control, a shaky foundation'],
    ['The Hierophant', 'tradition, teachers, shared values', 'rebelling for its own sake, outgrown rules'],
    ['The Lovers', 'a meaningful choice, alignment, real connection', 'misalignment, avoiding a decision, disharmony'],
    ['The Chariot', 'drive, willpower, steering opposing pulls', 'no direction, forcing it, loss of momentum'],
    ['Strength', 'gentle courage, patience, mastering impulse', 'self-doubt, running on empty, harshness'],
    ['The Hermit', 'solitude, searching inward, a guiding light', 'isolation, withdrawing too far, refusing counsel'],
    ['Wheel of Fortune', 'cycles turning, timing, a change of luck', 'resisting change, a setback, feeling stuck in a loop'],
    ['Justice', 'fairness, truth, cause and effect', 'dishonesty, avoiding accountability, bias'],
    ['The Hanged Man', 'pause, surrender, a new angle', 'stalling, needless sacrifice, resisting the pause'],
    ['Death', 'an ending that clears the way, transformation', 'clinging, fear of change, a slow fade'],
    ['Temperance', 'balance, moderation, blending opposites', 'excess, imbalance, impatience'],
    ['The Devil', 'attachment, habits that bind, shadow material', 'loosening a hold, breaking free, facing the shadow'],
    ['The Tower', 'sudden upheaval, truth breaking through', 'avoiding the inevitable, aftershocks, slow collapse'],
    ['The Star', 'hope, renewal, quiet faith', 'discouragement, disconnection, dimmed hope'],
    ['The Moon', 'dreams, uncertainty, what hides below the surface', 'confusion lifting, fear, clearing illusions'],
    ['The Sun', 'joy, vitality, clarity, success', 'temporary clouds, dimmed joy, overexposure'],
    ['Judgement', 'a reckoning, a call to rise, forgiveness', 'self-criticism, ignoring the call, regret'],
    ['The World', 'completion, wholeness, a cycle fulfilled', 'loose ends, almost there, stalled closure']
  ];

  var SUITS = {
    Wands: { glyph: '❂', theme: 'action, drive, creative fire', cards: [
      ['Ace', 'a spark, a new venture, raw energy', 'a false start, low spark, delay'],
      ['Two', 'planning, choosing a direction, looking ahead', 'fear of the unknown, playing it small'],
      ['Three', 'expansion, early results, waiting for returns', 'delays, narrow view, plans stalling'],
      ['Four', 'celebration, a stable base, homecoming', 'tension at home, a shaky base, a delayed party'],
      ['Five', 'competition, friction, many voices', 'avoiding conflict, petty fights, resolution near'],
      ['Six', 'recognition, victory, public acknowledgment', 'ego, a fall from favor, going unrecognized'],
      ['Seven', 'defending your position, standing firm', 'overwhelm, giving ground, burnout'],
      ['Eight', 'speed, news, things moving fast', 'slowdowns, scattered messages, rushing'],
      ['Nine', 'resilience, one more push, guarded stamina', 'exhaustion, defensiveness, old battle fatigue'],
      ['Ten', 'heavy responsibility, carrying too much', 'putting a burden down, delegating, collapse under load'],
      ['Page', 'curiosity, a bold idea, eager beginnings', 'half-finished ideas, restlessness, hesitation'],
      ['Knight', 'passion, bold pursuit, big energy', 'impulsiveness, burnout, scattered drive'],
      ['Queen', 'warmth, confidence, magnetic leadership', 'jealousy, insecurity, burning out the room'],
      ['King', 'vision, leadership, turning ideas into reality', 'domineering, impatience, big talk without follow-through']
    ]},
    Cups: { glyph: '❀', theme: 'emotion, relationship, imagination', cards: [
      ['Ace', 'an open heart, new feeling, emotional beginnings', 'blocked feeling, emotional drought, holding back'],
      ['Two', 'partnership, mutual attraction, reconciliation', 'imbalance, a strained bond, miscommunication'],
      ['Three', 'friendship, celebration, community', 'gossip, overindulgence, feeling left out'],
      ['Four', 'apathy, contemplation, missing what is offered', 'renewed interest, noticing the offer, ending the slump'],
      ['Five', 'grief, regret, focusing on what was lost', 'acceptance, moving on, seeing what remains'],
      ['Six', 'nostalgia, kindness, memories, innocence', 'stuck in the past, unrealistic memory, moving forward'],
      ['Seven', 'many options, wishful thinking, fantasy', 'clarity, choosing, sobering up from illusion'],
      ['Eight', 'walking away, seeking something deeper', 'drifting, fear of leaving, going back'],
      ['Nine', 'contentment, a wish granted, satisfaction', 'smugness, hollow wins, wanting more'],
      ['Ten', 'emotional fulfillment, harmony at home', 'family friction, a picture-perfect surface, misalignment'],
      ['Page', 'a tender message, creative inspiration, openness', 'emotional immaturity, mixed messages, moodiness'],
      ['Knight', 'romance, an offer, following the heart', 'unrealistic promises, moodiness, charm over substance'],
      ['Queen', 'compassion, emotional depth, intuitive care', 'emotional overwhelm, martyrdom, boundary drift'],
      ['King', 'emotional balance, calm counsel, diplomacy', 'suppressed feeling, moodiness, emotional manipulation']
    ]},
    Swords: { glyph: '✠', theme: 'thought, truth, communication', cards: [
      ['Ace', 'a clear idea, a breakthrough, honest truth', 'confusion, cloudy thinking, harsh words'],
      ['Two', 'a stalemate, a hard choice, holding both sides', 'indecision ending, information surfacing, overthinking'],
      ['Three', 'heartbreak, hard truth, a necessary hurt', 'healing, releasing pain, grief that lingers'],
      ['Four', 'rest, recovery, a needed pause', 'restlessness, burnout, getting back too soon'],
      ['Five', 'a hollow win, conflict, a cost to winning', 'reconciliation, letting a fight go, lingering resentment'],
      ['Six', 'moving toward calmer waters, a transition', 'carrying baggage, a slow passage, resistance to leaving'],
      ['Seven', 'strategy, stealth, doing it alone', 'coming clean, getting caught, conscience'],
      ['Eight', 'feeling trapped, a self-made limit', 'seeing the way out, freeing yourself, new perspective'],
      ['Nine', 'anxiety, sleepless worry, dread', 'worry easing, reaching out, facing fears'],
      ['Ten', 'a painful ending, hitting bottom, finality', 'recovery, the worst is past, a slow rise'],
      ['Page', 'curiosity, new ideas, a watchful mind', 'gossip, all talk, scattered thoughts'],
      ['Knight', 'quick thinking, direct action, charging in', 'impulsiveness, harsh speech, no plan'],
      ['Queen', 'clear perception, honesty, firm boundaries', 'coldness, bitterness, a sharp tongue'],
      ['King', 'intellect, fair judgment, clear authority', 'cold logic, misuse of power, rigid views']
    ]},
    Pentacles: { glyph: '✦', theme: 'work, money, the body, the practical world', cards: [
      ['Ace', 'a real opportunity, a seed of prosperity', 'a missed chance, shaky footing, poor planning'],
      ['Two', 'juggling priorities, adapting, flexibility', 'overcommitting, dropping a ball, disorganization'],
      ['Three', 'teamwork, craft, building something together', 'misaligned team, shoddy work, working alone'],
      ['Four', 'security, holding tight, protecting resources', 'loosening your grip, generosity, or greed'],
      ['Five', 'hardship, feeling left out in the cold', 'recovery, asking for help, the worst passing'],
      ['Six', 'generosity, fair exchange, giving and receiving', 'strings attached, imbalance, debt'],
      ['Seven', 'patience, assessing growth, the long game', 'impatience, poor returns, rethinking effort'],
      ['Eight', 'practice, mastery, steady diligent work', 'perfectionism, repetition, a lack of focus'],
      ['Nine', 'self-reliance, comfort, enjoying what you built', 'overspending, dependence, a gap in security'],
      ['Ten', 'legacy, lasting stability, family wealth', 'instability, family conflict, short-term thinking'],
      ['Page', 'a practical plan, study, a grounded start', 'procrastination, lack of follow-through, distraction'],
      ['Knight', 'reliability, steady progress, thoroughness', 'stagnation, stubbornness, going too slowly'],
      ['Queen', 'practical nurture, resourcefulness, comfort', 'overwork, neglecting yourself, material worry'],
      ['King', 'stability, security, provision, steady success', 'greed, stubbornness, rigid with resources']
    ]}
  };

  var DECK = [];
  MAJOR.forEach(function (c, i) {
    DECK.push({ name: c[0], up: c[1], rev: c[2], tag: 'Major Arcana ' + (i), glyph: '✶' });
  });
  Object.keys(SUITS).forEach(function (s) {
    SUITS[s].cards.forEach(function (c) {
      var nm = c[0] + ' of ' + s;
      DECK.push({ name: nm, up: c[1], rev: c[2], tag: s + ' · ' + SUITS[s].theme, glyph: SUITS[s].glyph });
    });
  });

  var SPREADS = {
    celtic:   { label: 'Celtic Cross',   positions: ['The heart of the matter', 'What crosses you', 'The root beneath it', 'The recent past', 'What you are reaching for', 'What is coming next', 'How you see yourself in this', 'Outside influences', 'Hopes and fears', 'Where it is heading'] },
    day:      { label: 'Your day',       positions: ['The day ahead'] },
    week:     { label: 'Your week',      positions: ['Start of the week', 'Middle of the week', 'End of the week'] },
    month:    { label: 'Your month',     positions: ['Week one', 'Week two', 'Week three', 'Week four'] },
    year:     { label: 'Your year',      positions: ['The theme of the year', 'Jan–Mar', 'Apr–Jun', 'Jul–Sep', 'Oct–Dec'] },
    question: { label: 'A question',     positions: ['Where things stand', 'What is in the way', 'What helps'] }
  };

  function shuffle(a) {
    var arr = a.slice(), i, j, t, buf = new Uint32Array(1);
    for (i = arr.length - 1; i > 0; i--) {
      var max = 0x100000000 - (0x100000000 % (i + 1)), r;
      do { crypto.getRandomValues(buf); r = buf[0]; } while (r >= max);
      j = r % (i + 1);
      t = arr[i]; arr[i] = arr[j]; arr[j] = t;
    }
    return arr;
  }
  function coin() { var b = new Uint8Array(1); crypto.getRandomValues(b); return b[0] < 128; }

  var form = document.getElementById('draw-form');
  var out = document.getElementById('spread');
  var again = document.getElementById('draw-again');
  var note = document.getElementById('draw-note');
  if (!form || !out) return;

  function esc(s) { return s.replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); }

  function draw() {
    var kind = form.elements['spread'].value;
    var useRev = form.elements['reversals'].checked;
    var sp = SPREADS[kind];
    var cards = shuffle(DECK).slice(0, sp.positions.length);
    out.innerHTML = '';
    out.classList.toggle('celtic', kind === 'celtic');
    out.setAttribute('aria-live', 'polite');
    note.textContent = 'Tap each card to turn it over. Read them in order.';
    var remaining = cards.length;
    cards.forEach(function (card, i) {
      var reversed = useRev && coin();
      var el = document.createElement('button');
      el.type = 'button';
      el.className = 'tcard';
      el.setAttribute('aria-pressed', 'false');
      el.innerHTML =
        '<span class="tpos">' + (kind === 'celtic' ? (i + 1) + '. ' : '') + esc(sp.positions[i]) + '</span>' +
        '<span class="tback" aria-hidden="true"><span class="tback-glyph">✦</span></span>' +
        '<span class="tface" hidden>' +
          '<span class="tglyph" aria-hidden="true">' + card.glyph + '</span>' +
          '<span class="tname">' + esc(card.name) + (reversed ? ' <em>(reversed)</em>' : '') + '</span>' +
          '<span class="ttag">' + esc(card.tag) + '</span>' +
          '<span class="tmean">' + esc(reversed ? card.rev : card.up) + '</span>' +
        '</span>';
      el.addEventListener('click', function () {
        if (el.getAttribute('aria-pressed') === 'true') return;
        el.setAttribute('aria-pressed', 'true');
        el.classList.add('open');
        el.querySelector('.tback').hidden = true;
        el.querySelector('.tface').hidden = false;
        remaining--;
        if (remaining === 0) note.textContent = 'All turned. Take what resonates and leave the rest. What do you notice?';
      });
      out.appendChild(el);
    });
    again.hidden = false;
    out.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }

  form.addEventListener('submit', function (e) { e.preventDefault(); draw(); });
  again.addEventListener('click', draw);
})();
