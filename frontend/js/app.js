/**
 * VoteWise frontend interactions.
 */

const API = "";
let chatSessionId = "";
let currentQuiz = null;
let currentQuestionIndex = 0;

const $ = (selector, root = document) => root.querySelector(selector);
const $$ = (selector, root = document) => Array.from(root.querySelectorAll(selector));

function createElement(tag, options = {}, children = []) {
  const node = document.createElement(tag);
  if (options.className) node.className = options.className;
  if (options.id) node.id = options.id;
  if (options.text !== undefined) node.textContent = String(options.text);
  if (options.htmlFor) node.htmlFor = options.htmlFor;
  if (options.type) node.type = options.type;
  if (options.value !== undefined) node.value = options.value;
  if (options.attributes) {
    Object.entries(options.attributes).forEach(([key, value]) => node.setAttribute(key, value));
  }
  if (options.dataset) {
    Object.entries(options.dataset).forEach(([key, value]) => {
      node.dataset[key] = value;
    });
  }
  if (options.style) Object.assign(node.style, options.style);
  if (options.on) {
    Object.entries(options.on).forEach(([eventName, handler]) => node.addEventListener(eventName, handler));
  }
  children.forEach(child => node.append(child));
  return node;
}

function replaceChildren(parent, children) {
  if (!parent) return;
  parent.replaceChildren(...children);
}

function appendMarkdownText(parent, text) {
  const parts = String(text).split(/(\*\*.*?\*\*|\n)/g).filter(Boolean);
  parts.forEach(part => {
    if (part === "\n") {
      parent.append(document.createElement("br"));
    } else if (part.startsWith("**") && part.endsWith("**")) {
      parent.append(createElement("strong", { text: part.slice(2, -2) }));
    } else {
      parent.append(document.createTextNode(part));
    }
  });
}

function apiJson(url, options = {}) {
  return fetch(url, options).then(response => {
    if (!response.ok) throw new Error(`Request failed: ${response.status}`);
    return response.json();
  });
}

// Particle system
(function initParticles() {
  const canvas = $("#particle-canvas");
  if (!canvas) return;
  const ctx = canvas.getContext("2d");
  const particles = [];
  const resize = () => {
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
  };

  class Particle {
    constructor() {
      this.reset();
    }

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
      this.x += this.vx;
      this.y += this.vy;
      if (this.x < 0 || this.x > canvas.width || this.y < 0 || this.y > canvas.height) this.reset();
    }

    draw() {
      ctx.beginPath();
      ctx.arc(this.x, this.y, this.radius, 0, Math.PI * 2);
      ctx.fillStyle = `hsla(${this.hue},80%,70%,${this.opacity})`;
      ctx.fill();
    }
  }

  resize();
  window.addEventListener("resize", resize);
  for (let i = 0; i < 60; i += 1) particles.push(new Particle());

  function drawLines() {
    for (let i = 0; i < particles.length; i += 1) {
      for (let j = i + 1; j < particles.length; j += 1) {
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
    particles.forEach(particle => {
      particle.update();
      particle.draw();
    });
    drawLines();
    requestAnimationFrame(animate);
  }

  animate();
})();

function animateCounter(el, target, suffix = "") {
  if (!el) return;
  const duration = 1200;
  const start = performance.now();

  function tick(now) {
    const progress = Math.min((now - start) / duration, 1);
    const eased = 1 - Math.pow(1 - progress, 3);
    const current = Math.round(target * eased);
    el.textContent = current.toLocaleString() + suffix;
    if (progress < 1) requestAnimationFrame(tick);
  }

  requestAnimationFrame(tick);
}

function switchTab(section) {
  $$(".nav-tab").forEach(tab => {
    tab.classList.remove("active");
    tab.setAttribute("aria-selected", "false");
  });
  $$(".section").forEach(sectionNode => sectionNode.classList.remove("active"));

  const tab = $(`[data-section="${section}"]`);
  if (tab) {
    tab.classList.add("active");
    tab.setAttribute("aria-selected", "true");
  }
  const sectionNode = document.getElementById(section);
  if (sectionNode) sectionNode.classList.add("active");

  if (section === "dashboard") loadDashboard();
  if (section === "timeline") loadTimeline();
}

function renderSuggestionButtons(questions) {
  const bar = $("#suggestions-bar");
  replaceChildren(
    bar,
    questions.map(question =>
      createElement("button", {
        className: "suggestion-chip",
        text: question,
        type: "button",
        on: { click: () => sendSuggestion(question) },
      }),
    ),
  );
}

async function loadDashboard() {
  try {
    const [analytics, leaderboard] = await Promise.all([
      apiJson(`${API}/api/analytics/summary`),
      apiJson(`${API}/api/analytics/leaderboard`),
    ]);

    animateCounter($("#stat-users"), analytics.total_users || 0);
    animateCounter($("#stat-quizzes"), analytics.total_quizzes_completed || 0);
    animateCounter($("#stat-xp"), analytics.total_xp_awarded || 0);
    animateCounter($("#stat-pass-rate"), analytics.quiz_pass_rate || 0, "%");

    const rows = leaderboard.map((user, index) => {
      const row = createElement("tr", {
        style: { animation: `sectionIn 0.4s ease-out ${index * 0.08}s both` },
      });
      row.append(
        createElement("td", {}, [createElement("span", { className: `rank-badge rank-${index + 1}`, text: index + 1 })]),
        createElement("td", { text: user.name, style: { fontWeight: "600" } }),
        createElement("td", {
          text: `${Number(user.xp_points || 0).toLocaleString()} XP`,
          style: { color: "#60a5fa", fontWeight: "700" },
        }),
        createElement("td", { text: user.quizzes_completed || 0 }),
        createElement("td", {}, [createElement("span", { className: "badge", text: user.level })]),
      );
      return row;
    });
    replaceChildren($("#leaderboard-body"), rows);
  } catch (error) {
    console.error("Dashboard load error:", error);
  }
}

const chatInput = $("#chat-input");
if (chatInput) {
  chatInput.addEventListener("keydown", event => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      sendMessage();
    }
  });
}

function sendSuggestion(text) {
  chatInput.value = text;
  sendMessage();
}

function showLoadingMessage() {
  const loadingDots = createElement("div", { className: "loading-dots" }, [
    createElement("span"),
    createElement("span"),
    createElement("span"),
  ]);
  const loadingEl = createElement("div", { className: "chat-message assistant", id: "chat-loading" }, [loadingDots]);
  $("#chat-messages").append(loadingEl);
  scrollChat();
}

async function sendMessage() {
  const message = chatInput.value.trim();
  if (!message) return;

  addChatMessage(message, "user");
  chatInput.value = "";
  chatInput.disabled = true;
  $("#chat-send-btn").disabled = true;
  showLoadingMessage();

  try {
    const data = await apiJson(`${API}/api/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message, session_id: chatSessionId, learning_level: "beginner", topic: "general" }),
    });
    $("#chat-loading")?.remove();
    chatSessionId = data.session_id || chatSessionId;
    addChatMessage(data.message, "assistant");
    if (data.civic_tip) addChatMessage(`Tip: ${data.civic_tip}`, "system");
    if (data.suggested_questions?.length) renderSuggestionButtons(data.suggested_questions);
  } catch (error) {
    $("#chat-loading")?.remove();
    addChatMessage("Sorry, I encountered an error. Please try again.", "assistant");
  } finally {
    chatInput.disabled = false;
    $("#chat-send-btn").disabled = false;
    chatInput.focus();
  }
}

function addChatMessage(text, role) {
  const message = createElement("div", { className: `chat-message ${role}` });
  appendMarkdownText(message, text);
  $("#chat-messages").append(message);
  scrollChat();
}

function scrollChat() {
  const container = $("#chat-messages");
  container.scrollTop = container.scrollHeight;
}

async function loadTimeline() {
  try {
    const data = await apiJson(`${API}/api/timeline`);
    const steps = data.steps.map((step, index) => {
      const details = createElement("div", { className: "step-details", id: `step-detail-${index}` });

      if (step.detailed_description) {
        details.append(createElement("p", { text: step.detailed_description, style: { color: "var(--text-2)", marginBottom: "0.85rem" } }));
      }
      appendDetailList(details, "Requirements", step.requirements);
      appendDetailList(details, "Tips", step.tips);
      appendDetailList(details, "Key Dates", step.key_dates);

      const node = createElement(
        "div",
        {
          className: "timeline-step",
          attributes: { role: "listitem", tabindex: "0", "aria-expanded": "false" },
          dataset: { step: index + 1 },
          style: { animation: `sectionIn 0.4s ease-out ${index * 0.06}s both` },
          on: {
            click: event => toggleStep(event.currentTarget),
            keydown: event => {
              if (event.key === "Enter" || event.key === " ") {
                event.preventDefault();
                toggleStep(event.currentTarget);
              }
            },
          },
        },
        [
          createElement("div", { className: "step-header" }, [
            createElement("span", { className: "step-icon", text: step.icon }),
            createElement("span", { className: "step-title", text: step.title }),
          ]),
          createElement("p", { className: "step-summary", text: step.summary }),
          details,
        ],
      );
      return node;
    });
    replaceChildren($("#timeline-grid"), steps);
  } catch (error) {
    console.error("Timeline load error:", error);
  }
}

function appendDetailList(parent, label, items = []) {
  if (!items.length) return;
  parent.append(
    createElement("div", { className: "detail-section" }, [
      createElement("div", { className: "detail-label", text: label }),
      createElement("ul", { className: "detail-list" }, items.map(item => createElement("li", { text: item }))),
    ]),
  );
}

function toggleStep(el) {
  const details = $(".step-details", el);
  if (!details) return;
  details.classList.toggle("open");
  el.setAttribute("aria-expanded", String(details.classList.contains("open")));
}

async function startQuiz() {
  const difficulty = $("#quiz-difficulty").value;
  const numQ = $("#quiz-count").value;
  try {
    currentQuiz = await apiJson(`${API}/api/quiz/generate?difficulty=${encodeURIComponent(difficulty)}&num_questions=${encodeURIComponent(numQ)}`, {
      method: "POST",
    });
    currentQuestionIndex = 0;
    $("#quiz-setup").style.display = "none";
    $("#quiz-results").style.display = "none";
    $("#quiz-active").style.display = "block";
    showQuestion();
  } catch (error) {
    console.error("Quiz start error:", error);
  }
}

function showQuestion() {
  if (!currentQuiz || currentQuestionIndex >= currentQuiz.questions.length) {
    finishQuiz();
    return;
  }

  const question = currentQuiz.questions[currentQuestionIndex];
  const total = currentQuiz.questions.length;
  const progress = ((currentQuestionIndex / total) * 100).toFixed(0);
  const letters = ["A", "B", "C", "D", "E", "F"];
  const options = question.options.map((option, index) =>
    createElement(
      "button",
      {
        className: "option-btn",
        type: "button",
        dataset: { index },
        style: { animation: `sectionIn 0.3s ease-out ${index * 0.06}s both` },
        on: { click: () => submitAnswer(index) },
      },
      [createElement("span", { className: "option-letter", text: letters[index] }), createElement("span", { text: option })],
    ),
  );

  replaceChildren($("#quiz-question-card"), [
    createElement("div", { className: "question-progress" }, [
      createElement("span", { text: `Question ${currentQuestionIndex + 1} of ${total}` }),
      createElement("div", { className: "progress-bar" }, [
        createElement("div", { className: "progress-fill", style: { width: `${progress}%` } }),
      ]),
      createElement("span", { className: "badge", text: question.difficulty }),
    ]),
    createElement("div", { className: "question-text", text: question.question }),
    createElement("div", { className: "options-grid", id: "options-grid" }, options),
    createElement("div", { className: "explanation-box", id: "explanation-box" }),
  ]);
}

async function submitAnswer(selectedIndex) {
  const question = currentQuiz.questions[currentQuestionIndex];
  $$(".option-btn").forEach(button => button.classList.add("disabled"));
  try {
    const result = await apiJson(
      `${API}/api/quiz/answer?session_id=${encodeURIComponent(currentQuiz.id)}&question_id=${encodeURIComponent(question.id)}&selected_answer=${selectedIndex}`,
      { method: "POST" },
    );
    $$(".option-btn").forEach(button => {
      const index = Number.parseInt(button.dataset.index, 10);
      if (index === result.correct_answer) button.classList.add("correct");
      else if (index === selectedIndex && !result.is_correct) button.classList.add("incorrect");
    });
    const expBox = $("#explanation-box");
    replaceChildren(expBox, [
      createElement("strong", { text: result.is_correct ? "Correct!" : "Incorrect" }),
      document.createTextNode(` - ${result.explanation}`),
      document.createElement("br"),
      createElement("span", { text: `+${result.points_earned} points`, style: { color: "#60a5fa" } }),
    ]);
    expBox.classList.add("visible");
    setTimeout(() => {
      currentQuestionIndex += 1;
      showQuestion();
    }, 2500);
  } catch (error) {
    console.error("Answer error:", error);
  }
}

async function finishQuiz() {
  try {
    const result = await apiJson(`${API}/api/quiz/complete/${encodeURIComponent(currentQuiz.id)}`, { method: "POST" });
    $("#quiz-active").style.display = "none";
    $("#quiz-results").style.display = "block";

    const passed = result.score_percent >= 70;
    const children = [
      createElement("div", { text: passed ? "Passed" : "Keep Learning", style: { fontSize: "2rem", marginBottom: "0.75rem", fontWeight: "800" } }),
      createElement("div", { className: "result-score", text: `${result.score_percent}%` }),
      createElement("p", {
        text: `${result.correct_count} of ${result.total_count} correct - ${result.xp_awarded} XP earned`,
        style: { color: "var(--text-2)", marginBottom: "0.5rem" },
      }),
      createElement("p", {
        text: passed ? "Great job! You passed." : "Keep learning. You will get it next time.",
        style: { fontSize: "1.1rem", marginBottom: "1.25rem" },
      }),
    ];

    if (result.badges_earned?.length) {
      children.push(
        createElement(
          "div",
          { className: "result-badges" },
          result.badges_earned.map(badge => createElement("span", { className: "badge", text: badge })),
        ),
      );
    }

    children.push(
      createElement("button", {
        className: "btn btn-primary",
        type: "button",
        text: "Take Another Quiz",
        style: { marginTop: "1.5rem" },
        on: { click: resetQuiz },
      }),
    );
    replaceChildren($("#quiz-result-card"), children);
  } catch (error) {
    console.error("Quiz finish error:", error);
  }
}

function resetQuiz() {
  currentQuiz = null;
  currentQuestionIndex = 0;
  $("#quiz-setup").style.display = "block";
  $("#quiz-active").style.display = "none";
  $("#quiz-results").style.display = "none";
}

async function checkReadiness() {
  const payload = {
    age: Number.parseInt($("#readiness-age").value, 10) || 18,
    state: $("#readiness-state").value,
    is_registered: $("#readiness-registered").checked,
    knows_polling_location: $("#readiness-polling").checked,
    has_valid_id: $("#readiness-id").checked,
    understands_ballot: $("#readiness-ballot").checked,
  };
  try {
    const result = await apiJson(`${API}/api/timeline/readiness`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const scoreClass = result.score >= 80 ? "high" : result.score >= 50 ? "medium" : "low";
    const checklist = Object.entries(result.checklist).map(([key, value]) =>
      createElement("div", { style: { display: "flex", alignItems: "center", gap: "0.5rem", padding: "0.35rem 0", color: "var(--text-2)", fontSize: "0.92rem" } }, [
        createElement("span", { text: value ? "Done" : "Needed", style: { fontWeight: "700", minWidth: "64px" } }),
        createElement("span", { text: key }),
      ]),
    );
    const children = [
      createElement("div", { className: `readiness-score ${scoreClass}`, text: `${result.score}%` }),
      createElement("p", { text: result.status, style: { fontSize: "1.2rem", marginBottom: "1.25rem", fontWeight: "600" } }),
      createElement("div", { style: { textAlign: "left", maxWidth: "500px", margin: "0 auto" } }, [
        createElement("h3", { text: "Your Checklist", style: { marginBottom: "0.75rem" } }),
        ...checklist,
      ]),
    ];

    if (result.recommendations.length) {
      children[2].append(
        createElement("h3", { text: "Recommendations", style: { margin: "1.25rem 0 0.5rem" } }),
        ...result.recommendations.map(recommendation =>
          createElement("p", {
            text: `- ${recommendation}`,
            style: { color: "var(--text-2)", padding: "0.2rem 0", fontSize: "0.88rem" },
          }),
        ),
      );
    }

    const el = $("#readiness-result");
    el.style.display = "block";
    replaceChildren(el, children);
  } catch (error) {
    console.error("Readiness error:", error);
  }
}

function attachEvents() {
  $$(".nav-tab").forEach(tab => {
    tab.addEventListener("click", () => switchTab(tab.dataset.section));
    tab.addEventListener("keydown", event => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        switchTab(tab.dataset.section);
      }
    });
  });

  $$("[data-action]").forEach(control => {
    control.addEventListener("click", () => {
      const action = control.dataset.action;
      if (action === "start-quiz") startQuiz();
      if (action === "check-readiness") checkReadiness();
      if (action === "send-message") sendMessage();
      if (action === "suggestion") sendSuggestion(control.dataset.suggestion || "");
      if (action?.startsWith("switch:")) switchTab(action.replace("switch:", ""));
    });
  });
}

attachEvents();
loadDashboard();
