/**
 * VoteWise — Premium Frontend with Particle System & Animated Counters
 */

const API = '';
let chatSessionId = '';
let currentQuiz = null;
let currentQuestionIndex = 0;

// ═══ Particle System ═══
(function initParticles() {
  const canvas = document.getElementById('particle-canvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  let particles = [];
  const resize = () => { canvas.width = window.innerWidth; canvas.height = window.innerHeight; };
  resize(); window.addEventListener('resize', resize);

  class Particle {
    constructor() { this.reset(); }
    reset() {
      this.x = Math.random() * canvas.width;
      this.y = Math.random() * canvas.height;
      this.vx = (Math.random() - 0.5) * 0.3;
      this.vy = (Math.random() - 0.5) * 0.3;
      this.radius = Math.random() * 1.5 + 0.5;
      this.opacity = Math.random() * 0.4 + 0.1;
      this.hue = Math.random() > 0.5 ? 220 : 260;
    }
    update() {
      this.x += this.vx; this.y += this.vy;
      if (this.x < 0 || this.x > canvas.width || this.y < 0 || this.y > canvas.height) this.reset();
    }
    draw() {
      ctx.beginPath();
      ctx.arc(this.x, this.y, this.radius, 0, Math.PI * 2);
      ctx.fillStyle = `hsla(${this.hue},80%,70%,${this.opacity})`;
      ctx.fill();
    }
  }

  for (let i = 0; i < 60; i++) particles.push(new Particle());

  function drawLines() {
    for (let i = 0; i < particles.length; i++) {
      for (let j = i + 1; j < particles.length; j++) {
        const dx = particles[i].x - particles[j].x;
        const dy = particles[i].y - particles[j].y;
        const dist = Math.sqrt(dx * dx + dy * dy);
        if (dist < 120) {
          ctx.beginPath();
          ctx.moveTo(particles[i].x, particles[i].y);
          ctx.lineTo(particles[j].x, particles[j].y);
          ctx.strokeStyle = `rgba(99,102,241,${0.06 * (1 - dist / 120)})`;
          ctx.lineWidth = 0.5;
          ctx.stroke();
        }
      }
    }
  }

  function animate() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    particles.forEach(p => { p.update(); p.draw(); });
    drawLines();
    requestAnimationFrame(animate);
  }
  animate();
})();

// ═══ Animated Counter ═══
function animateCounter(el, target, suffix = '') {
  if (!el) return;
  const duration = 1200;
  const start = performance.now();
  const initial = 0;

  function tick(now) {
    const progress = Math.min((now - start) / duration, 1);
    const eased = 1 - Math.pow(1 - progress, 3);
    const current = Math.round(initial + (target - initial) * eased);
    el.textContent = current.toLocaleString() + suffix;
    if (progress < 1) requestAnimationFrame(tick);
  }
  requestAnimationFrame(tick);
}

// ═══ Navigation ═══
document.querySelectorAll('.nav-tab').forEach(tab => {
  tab.addEventListener('click', () => switchTab(tab.dataset.section));
  tab.addEventListener('keydown', e => { if (e.key === 'Enter') switchTab(tab.dataset.section); });
});

function switchTab(section) {
  document.querySelectorAll('.nav-tab').forEach(t => { t.classList.remove('active'); t.setAttribute('aria-selected', 'false'); });
  document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
  const tab = document.querySelector(`[data-section="${section}"]`);
  if (tab) { tab.classList.add('active'); tab.setAttribute('aria-selected', 'true'); }
  const sec = document.getElementById(section);
  if (sec) sec.classList.add('active');
  if (section === 'dashboard') loadDashboard();
  if (section === 'timeline') loadTimeline();
}

// ═══ Dashboard ═══
async function loadDashboard() {
  try {
    const [analytics, leaderboard] = await Promise.all([
      fetch(`${API}/api/analytics/summary`).then(r => r.json()),
      fetch(`${API}/api/analytics/leaderboard`).then(r => r.json()),
    ]);

    animateCounter(document.getElementById('stat-users'), analytics.total_users || 0);
    animateCounter(document.getElementById('stat-quizzes'), analytics.total_quizzes_completed || 0);
    animateCounter(document.getElementById('stat-xp'), analytics.total_xp_awarded || 0);
    animateCounter(document.getElementById('stat-pass-rate'), analytics.quiz_pass_rate || 0, '%');

    const tbody = document.getElementById('leaderboard-body');
    tbody.innerHTML = leaderboard.map((u, i) => `
      <tr style="animation:sectionIn 0.4s ease-out ${i * 0.08}s both">
        <td><span class="rank-badge rank-${i + 1}">${i + 1}</span></td>
        <td style="font-weight:600">${u.name}</td>
        <td style="color:#60a5fa;font-weight:700">${u.xp_points.toLocaleString()} XP</td>
        <td>${u.quizzes_completed}</td>
        <td><span class="badge">${u.level}</span></td>
      </tr>
    `).join('');
  } catch (e) { console.error('Dashboard load error:', e); }
}

// ═══ Chat ═══
const chatInput = document.getElementById('chat-input');
chatInput.addEventListener('keydown', e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); } });

function sendSuggestion(text) { chatInput.value = text; sendMessage(); }

async function sendMessage() {
  const message = chatInput.value.trim();
  if (!message) return;
  addChatMessage(message, 'user');
  chatInput.value = '';
  chatInput.disabled = true;
  document.getElementById('chat-send-btn').disabled = true;

  const loadingEl = document.createElement('div');
  loadingEl.className = 'chat-message assistant';
  loadingEl.innerHTML = '<div class="loading-dots"><span></span><span></span><span></span></div>';
  loadingEl.id = 'chat-loading';
  document.getElementById('chat-messages').appendChild(loadingEl);
  scrollChat();

  try {
    const res = await fetch(`${API}/api/chat`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message, session_id: chatSessionId, learning_level: 'beginner', topic: 'general' }),
    });
    const data = await res.json();
    document.getElementById('chat-loading')?.remove();
    chatSessionId = data.session_id || chatSessionId;
    addChatMessage(data.message, 'assistant');
    if (data.civic_tip) addChatMessage(`💡 ${data.civic_tip}`, 'system');

    if (data.suggested_questions?.length) {
      document.getElementById('suggestions-bar').innerHTML = data.suggested_questions.map(q =>
        `<button class="suggestion-chip" onclick="sendSuggestion('${q.replace(/'/g, "\\'")}')">${q}</button>`
      ).join('');
    }
  } catch (e) {
    document.getElementById('chat-loading')?.remove();
    addChatMessage('Sorry, I encountered an error. Please try again.', 'assistant');
  }
  chatInput.disabled = false;
  document.getElementById('chat-send-btn').disabled = false;
  chatInput.focus();
}

function addChatMessage(text, role) {
  const el = document.createElement('div');
  el.className = `chat-message ${role}`;
  el.innerHTML = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>').replace(/\n/g, '<br>');
  document.getElementById('chat-messages').appendChild(el);
  scrollChat();
}

function scrollChat() {
  const c = document.getElementById('chat-messages');
  c.scrollTop = c.scrollHeight;
}

// ═══ Timeline ═══
async function loadTimeline() {
  try {
    const data = await fetch(`${API}/api/timeline`).then(r => r.json());
    document.getElementById('timeline-grid').innerHTML = data.steps.map((step, i) => `
      <div class="timeline-step" data-step="${i + 1}" role="listitem"
           onclick="toggleStep(this)" tabindex="0" onkeydown="if(event.key==='Enter')toggleStep(this)"
           style="animation:sectionIn 0.4s ease-out ${i * 0.06}s both">
        <div class="step-header">
          <span class="step-icon">${step.icon}</span>
          <span class="step-title">${step.title}</span>
        </div>
        <p class="step-summary">${step.summary}</p>
        <div class="step-details" id="step-detail-${i}">
          ${step.detailed_description ? `<p style="color:var(--text-2);margin-bottom:0.85rem">${step.detailed_description}</p>` : ''}
          ${step.requirements.length ? `<div class="detail-section"><div class="detail-label">Requirements</div><ul class="detail-list">${step.requirements.map(r => `<li>${r}</li>`).join('')}</ul></div>` : ''}
          ${step.tips.length ? `<div class="detail-section"><div class="detail-label">Tips</div><ul class="detail-list">${step.tips.map(t => `<li>${t}</li>`).join('')}</ul></div>` : ''}
          ${step.key_dates.length ? `<div class="detail-section"><div class="detail-label">Key Dates</div><ul class="detail-list">${step.key_dates.map(d => `<li>${d}</li>`).join('')}</ul></div>` : ''}
        </div>
      </div>
    `).join('');
  } catch (e) { console.error('Timeline load error:', e); }
}

function toggleStep(el) {
  const d = el.querySelector('.step-details');
  if (d) d.classList.toggle('open');
}

// ═══ Quiz ═══
async function startQuiz() {
  const difficulty = document.getElementById('quiz-difficulty').value;
  const numQ = document.getElementById('quiz-count').value;
  try {
    const res = await fetch(`${API}/api/quiz/generate?difficulty=${difficulty}&num_questions=${numQ}`, { method: 'POST' });
    currentQuiz = await res.json(); currentQuestionIndex = 0;
    document.getElementById('quiz-setup').style.display = 'none';
    document.getElementById('quiz-results').style.display = 'none';
    document.getElementById('quiz-active').style.display = 'block';
    showQuestion();
  } catch (e) { console.error('Quiz start error:', e); }
}

function showQuestion() {
  if (!currentQuiz || currentQuestionIndex >= currentQuiz.questions.length) { finishQuiz(); return; }
  const q = currentQuiz.questions[currentQuestionIndex];
  const total = currentQuiz.questions.length;
  const progress = ((currentQuestionIndex) / total * 100).toFixed(0);
  const letters = ['A', 'B', 'C', 'D', 'E', 'F'];
  document.getElementById('quiz-question-card').innerHTML = `
    <div class="question-progress">
      <span>Question ${currentQuestionIndex + 1} of ${total}</span>
      <div class="progress-bar"><div class="progress-fill" style="width:${progress}%"></div></div>
      <span class="badge">${q.difficulty}</span>
    </div>
    <div class="question-text">${q.question}</div>
    <div class="options-grid" id="options-grid">
      ${q.options.map((opt, i) => `
        <button class="option-btn" data-index="${i}" onclick="submitAnswer(${i})" style="animation:sectionIn 0.3s ease-out ${i*0.06}s both">
          <span class="option-letter">${letters[i]}</span><span>${opt}</span>
        </button>
      `).join('')}
    </div>
    <div class="explanation-box" id="explanation-box"></div>
  `;
}

async function submitAnswer(selectedIndex) {
  const q = currentQuiz.questions[currentQuestionIndex];
  document.querySelectorAll('.option-btn').forEach(btn => btn.classList.add('disabled'));
  try {
    const res = await fetch(`${API}/api/quiz/answer?session_id=${currentQuiz.id}&question_id=${q.id}&selected_answer=${selectedIndex}`, { method: 'POST' });
    const result = await res.json();
    document.querySelectorAll('.option-btn').forEach(btn => {
      const idx = parseInt(btn.dataset.index);
      if (idx === result.correct_answer) btn.classList.add('correct');
      else if (idx === selectedIndex && !result.is_correct) btn.classList.add('incorrect');
    });
    const expBox = document.getElementById('explanation-box');
    expBox.innerHTML = `<strong>${result.is_correct ? '✅ Correct!' : '❌ Incorrect'}</strong> — ${result.explanation}<br><span style="color:#60a5fa">+${result.points_earned} points</span>`;
    expBox.classList.add('visible');
    setTimeout(() => { currentQuestionIndex++; showQuestion(); }, 2500);
  } catch (e) { console.error('Answer error:', e); }
}

async function finishQuiz() {
  try {
    const res = await fetch(`${API}/api/quiz/complete/${currentQuiz.id}`, { method: 'POST' });
    const result = await res.json();
    document.getElementById('quiz-active').style.display = 'none';
    document.getElementById('quiz-results').style.display = 'block';
    const passed = result.score_percent >= 70;
    document.getElementById('quiz-result-card').innerHTML = `
      <div style="font-size:3.5rem;margin-bottom:0.75rem">${passed ? '🎉' : '📚'}</div>
      <div class="result-score">${result.score_percent}%</div>
      <p style="color:var(--text-2);margin-bottom:0.5rem">${result.correct_count} of ${result.total_count} correct — ${result.xp_awarded} XP earned</p>
      <p style="font-size:1.1rem;margin-bottom:1.25rem">${passed ? 'Great job! You passed!' : "Keep learning — you'll get it next time!"}</p>
      ${result.badges_earned?.length ? `<div class="result-badges">${result.badges_earned.map(b => `<span class="badge">🏅 ${b}</span>`).join('')}</div>` : ''}
      <button class="btn btn-primary" style="margin-top:1.5rem" onclick="resetQuiz()">Take Another Quiz</button>
    `;
  } catch (e) { console.error('Quiz finish error:', e); }
}

function resetQuiz() {
  currentQuiz = null; currentQuestionIndex = 0;
  document.getElementById('quiz-setup').style.display = 'block';
  document.getElementById('quiz-active').style.display = 'none';
  document.getElementById('quiz-results').style.display = 'none';
}

// ═══ Readiness ═══
async function checkReadiness() {
  const payload = {
    age: parseInt(document.getElementById('readiness-age').value) || 18,
    state: document.getElementById('readiness-state').value,
    is_registered: document.getElementById('readiness-registered').checked,
    knows_polling_location: document.getElementById('readiness-polling').checked,
    has_valid_id: document.getElementById('readiness-id').checked,
    understands_ballot: document.getElementById('readiness-ballot').checked,
  };
  try {
    const res = await fetch(`${API}/api/timeline/readiness`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
    const result = await res.json();
    const scoreClass = result.score >= 80 ? 'high' : result.score >= 50 ? 'medium' : 'low';
    const el = document.getElementById('readiness-result');
    el.style.display = 'block';
    el.innerHTML = `
      <div class="readiness-score ${scoreClass}">${result.score}%</div>
      <p style="font-size:1.2rem;margin-bottom:1.25rem;font-weight:600">${result.status}</p>
      <div style="text-align:left;max-width:500px;margin:0 auto">
        <h3 style="margin-bottom:0.75rem">📋 Your Checklist</h3>
        ${Object.entries(result.checklist).map(([k, v]) => `
          <div style="display:flex;align-items:center;gap:0.5rem;padding:0.35rem 0;color:var(--text-2);font-size:0.92rem">
            <span style="font-size:1.1rem">${v ? '✅' : '❌'}</span><span>${k}</span>
          </div>
        `).join('')}
        ${result.recommendations.length ? `
          <h3 style="margin:1.25rem 0 0.5rem">💡 Recommendations</h3>
          ${result.recommendations.map(r => `<p style="color:var(--text-2);padding:0.2rem 0;font-size:0.88rem">→ ${r}</p>`).join('')}
        ` : ''}
      </div>
    `;
  } catch (e) { console.error('Readiness error:', e); }
}

// ═══ Init ═══
loadDashboard();
