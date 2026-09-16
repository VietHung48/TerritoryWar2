const CFG = window.GAME_CONFIG;
let STATE = null;
let currentQuestionId = null;
let timerInterval = null;
let pendingCell = null; // {r, c} đang chờ chọn màu

/**
 * Chuyển giữa tab "Câu hỏi" / "Lãnh địa"
 */
function showTab(name) {
  
  document.getElementById('tab-questions').classList.toggle('active', name === 'questions');
  document.getElementById('tab-territory').classList.toggle('active', name === 'territory');
  document.getElementById('tabQuestionsBtn').classList.toggle('active', name === 'questions');
  document.getElementById('tabTerritoryBtn').classList.toggle('active', name === 'territory');
  if (name === 'territory') renderBoard();
}

/**
 * Load trạng thái từ server
 */
async function loadState() {
  const res = await fetch('/api/state');
  STATE = await res.json();
  renderQuestionGrid();
  renderBoard();
  renderRanking();
}

/**
*Render danh sách 30 câu hỏi
*/
function renderQuestionGrid() {
  const wrap = document.getElementById('questionGrid');
  wrap.innerHTML = '';
  STATE.questions.forEach((q, i) => {
    const div = document.createElement('div');
    div.className = 'q-card' + (q.used ? ' used' : '');
    div.textContent = i + 1;
    if (!q.used) {
      div.addEventListener('click', () => openQuestion(q.id));
    }
    wrap.appendChild(div);
  });
}
/**
 * Mở câu hỏi
 */
async function openQuestion(qid) {
  const res = await fetch(`/api/question/${qid}/open`, { method: 'POST' });
  const data = await res.json();
  if (data.error) { alert(data.error); return; }

  
  
  currentQuestionId = qid;
  document.getElementById('questionText').textContent = data.question.text;
  
  const optionsWrap = document.getElementById('questionOptions');
  optionsWrap.innerHTML = '';

  Object.entries(data.question.options || {}).forEach(([key, value]) => {
  const option = document.createElement('div');

  option.className = 'question-option';
  option.dataset.option = key;

  option.innerHTML = `<b>${key}.</b> ${value}`;

  optionsWrap.appendChild(option);
  });

  const banner = document.getElementById('perkBanner');
  if (data.perk) {
    banner.style.display = 'block';
    banner.className = 'perk-banner ' + data.perk.type;
    banner.innerHTML = `<div>${data.perk.title}</div><div style="font-weight:400;font-size:15px;margin-top:4px;">${data.perk.desc}</div>`;
  } else {
    banner.style.display = 'none';
  }

  document.getElementById('answerRow').style.display = 'none';
  resetTimerUI();

  document.getElementById('overlay').style.display = 'block';
  document.getElementById('questionBox').style.display = 'block';

  // đánh dấu đã dùng ngay trên UI
  STATE.questions.forEach(q => { if (q.id === qid) q.used = true; });
  renderQuestionGrid();
}
/**
 * Đóng modal, dừng timer
 */
function closeQuestion() {
  document.getElementById('overlay').style.display = 'none';
  document.getElementById('questionBox').style.display = 'none';
  stopTimer();
  currentQuestionId = null;
}
/**
 * 	Gọi API lấy đáp án đúng, hiện ra + tô sáng đáp án đúng
 */
async function revealAnswer() {
  if (currentQuestionId == null) return;
  const res = await fetch(`/api/question/${currentQuestionId}/answer`);
  const data = await res.json();


  // document.getElementById('answerText').textContent = data.answer;
  // document.getElementById('answerRow').style.display = 'block';

  //  // Tìm đáp án đúng và bôi đỏ
  // const correctOption = document.querySelector(
  //   `.question-option[data-option="${data.answer}"]`
  // );

  // if (correctOption) {
  //   correctOption.classList.add('correct');
  // }

  const correct = String(data.answer).trim().toUpperCase();

  document.querySelectorAll('.question-option').forEach(option => {
    if (option.dataset.option === correct) {
      option.classList.add('correct');
    }
  }); 
  //delay then switch to domain 
  setTimeout(() => {
    goToTerritory();
  }, 5000);
}
/**
 * 	Đóng modal + chuyển sang tab Lãnh địa
 */
function goToTerritory() {
  closeQuestion();
  showTab('territory');
}
/**
 * Reset đồng hồ về 10, admin tự bật lại nút bấm
 */

function resetTimerUI() {
  stopTimer();
  const disp = document.getElementById('timerDisplay');
  disp.textContent = '10';
  disp.classList.remove('urgent');
  document.getElementById('timerBtn').disabled = false;
  document.getElementById('timerBtn').textContent = '⏱️ Bắt đầu đếm giờ (10s)';
  
}
/**
 * 	Admin bấm để bắt đầu đếm ngược 10s
 */

function startTimer() {
  let t = 10;
  const disp = document.getElementById('timerDisplay');
  const btn = document.getElementById('timerBtn');
  btn.disabled = true;
  btn.textContent = 'Đang đếm giờ...';
  disp.textContent = t;

  stopTimer();
  timerInterval = setInterval(() => {
    t -= 1;
    disp.textContent = t;
    if (t <= 3) disp.classList.add('urgent');
    if (t <= 0) {
      stopTimer();
      btn.textContent = '⏰ Hết giờ!';
    }
  }, 1000);
}
/**
 * 	Dừng interval đang chạy
 */
function stopTimer() {
  if (timerInterval) { clearInterval(timerInterval); timerInterval = null; }
}

// ---------------------------------------------------------------------
// Bàn cờ lãnh địa
// ---------------------------------------------------------------------
/**
 * Vẽ lại toàn bộ 60 ô theo màu đội trong STATE.grid
 */
function renderBoard() {
  if (!STATE) return;
  const board = document.getElementById('board');
  board.innerHTML = '';
  for (let r = 0; r < CFG.rows; r++) {
    for (let c = 0; c < CFG.cols; c++) {
      const team = STATE.grid[r][c];
      const div = document.createElement('div');
      div.className = 'cell';
      div.textContent = String.fromCharCode(65 + r) + (c + 1);
      if (team && CFG.teams[team]) {
        div.style.background = CFG.teams[team].color;
        div.style.color = '#fff';
      }
      div.addEventListener('click', (ev) => openColorPopup(ev, r, c));
      board.appendChild(div);
    }
  }
}

/**
 *Hiện popup 5 màu ngay cạnh ô vừa bấm
 */
function openColorPopup(ev, r, c) {
  pendingCell = { r, c };
  const popup = document.getElementById('colorPopup');
  popup.style.display = 'block';

  const rect = ev.target.getBoundingClientRect();
  const margin = 10;
  const gap = 8;
  const availableWidth = Math.max(0, window.innerWidth - margin * 2);
  const availableHeight = Math.max(0, window.innerHeight - margin * 2);

  // Thu nhỏ/giãn chiều rộng theo phần màn hình còn lại để popup không bị cắt.
  popup.style.boxSizing = 'border-box';
  popup.style.width = Math.min(240, availableWidth) + 'px';
  popup.style.maxWidth = availableWidth + 'px';
  popup.style.maxHeight = availableHeight + 'px';
  popup.style.overflowY = 'auto';

  const popupWidth = popup.offsetWidth;
  const popupHeight = Math.min(popup.offsetHeight, availableHeight);
  let left = rect.left + window.scrollX;
  let top = rect.bottom + window.scrollY + gap;

  if (left + popupWidth > window.innerWidth - margin + window.scrollX) {
    left = window.innerWidth - popupWidth - margin + window.scrollX;
  }
  left = Math.max(window.scrollX + margin, left);

  // Nếu không đủ chỗ phía dưới, đặt popup lên phía trên ô.
  if (rect.bottom + popupHeight + gap > window.innerHeight - margin) {
    top = rect.top + window.scrollY - popupHeight - gap;
  }
  top = Math.max(window.scrollY + margin, top);

  popup.style.left = left + 'px';
  popup.style.top = top + 'px';
}

document.addEventListener('click', (ev) => {
  const popup = document.getElementById('colorPopup');
  if (popup.style.display === 'block' &&
      !popup.contains(ev.target) &&
      !ev.target.classList.contains('cell')) {
    popup.style.display = 'none';
  }
});
/**
 *	Gọi API /api/claim, cập nhật bảng + xếp hạng ngay sau đó
 */
async function pickColor(team) {
  document.getElementById('colorPopup').style.display = 'none';
  if (!pendingCell) return;
  const res = await fetch('/api/claim', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ row: pendingCell.r, col: pendingCell.c, team })
  });
  const data = await res.json();
  STATE.grid = data.grid;
  renderBoard();
  renderRankingFromPayload(data);
  pendingCell = null;
}

// ---------------------------------------------------------------------
// Bảng xếp hạng
// ---------------------------------------------------------------------
/**
 *		Vẽ xếp hạng dùng dữ liệu có sẵn trong STATE
 */
function renderRanking() {
  if (!STATE) return;
  renderRankingFromPayload(STATE);
}
/**
 *		Vẽ xếp hạng từ 1 response API bất kỳ (dùng chung cho nhiều chỗ)
 */
function renderRankingFromPayload(payload) {
  const box = document.getElementById('ranking');
  let html = '<h3>🏆 Bảng xếp hạng</h3>';
  payload.ranking.forEach((r, i) => {
    html += `<div class="rank-row">
      <span><b>#${i + 1}</b> <span class="swatch-dot" style="background:${r.color}"></span>${r.name}</span>
      <span>${r.count} ô</span>
    </div>`;
  });
  html += `<div class="rank-row"><span>⬜ Chưa chiếm</span><span>${payload.neutral} ô</span></div>`;
  if (payload.leader) {
    html += `<div class="leader-line">👑 Dẫn đầu: <b style="color:${payload.leader.color}">${payload.leader.name}</b></div>`;
  }
  box.innerHTML = html;
}

// ---------------------------------------------------------------------
// Reset ván chơi
// ---------------------------------------------------------------------
/**
 *		Xác nhận rồi gọi /api/reset, tải lại toàn bộ trạng thái
 */
async function resetGame() {
  if (!confirm('Chơi lại từ đầu? Toàn bộ lãnh địa và câu hỏi đã dùng sẽ được làm mới.')) return;
  await fetch('/api/reset', { method: 'POST' });
  await loadState();
  closeQuestion();
  showTab('questions');
}


loadState();
