/**
 * ==============================================================================
 * SNAPCLASS APPLICATION CONTROLLER (Frontend JavaScript)
 * Handles client state, camera/audio capture, modal dialogs, and Flask API integration.
 * ==============================================================================
 */

// Application State
const state = {
  currentUser: null,       // { role: 'student' | 'teacher', data: {...} }
  teacherTab: 'take_attendance',
  attendancePhotos: [],    // Array of base64 data URLs for classroom photos
  pendingAttendance: null, // { preview: [], logs: [] }
  cameraStream: null,
  mediaRecorder: null,
  audioChunks: [],
  recordedAudioBlob: null,
  recordingInterval: null,
  recordingSeconds: 0
};

// ==============================================================================
// INITIALIZATION & ROUTING
// ==============================================================================
document.addEventListener("DOMContentLoaded", () => {
  // Restore persisted session from localStorage
  const storedUser = localStorage.getItem("snapclass_user");
  if (storedUser) {
    try {
      state.currentUser = JSON.parse(storedUser);
    } catch (e) {
      localStorage.removeItem("snapclass_user");
    }
  }

  // Handle URL Join Code (e.g., /?join-code=CS101)
  const urlParams = new URLSearchParams(window.location.search);
  const joinCode = urlParams.get("join-code");

  if (joinCode) {
    handleUrlJoinCode(joinCode);
  } else if (state.currentUser) {
    if (state.currentUser.role === "student") {
      showView("student_dashboard");
    } else if (state.currentUser.role === "teacher") {
      showView("teacher_dashboard");
    }
  } else {
    showView("home");
  }

  setupEventListeners();
});

/**
 * Handles class joining via URL query parameter.
 */
async function handleUrlJoinCode(joinCode) {
  if (!state.currentUser || state.currentUser.role !== "student") {
    // Prompt student login first
    showToast("Please log in with FaceID to join this class.", "warning");
    sessionStorage.setItem("pending_join_code", joinCode);
    showView("student_login");
    return;
  }

  // Fetch subject info and prompt auto-enroll dialog
  try {
    const res = await fetch(`/api/subject/info/${encodeURIComponent(joinCode)}`);
    const data = await res.json();
    if (data.success) {
      document.getElementById("quickEnrollSubjectName").innerText = data.subject.name;
      document.getElementById("quickEnrollSubjectCode").innerText = data.subject.subject_code;
      document.getElementById("btnConfirmQuickEnroll").onclick = () => confirmQuickEnroll(joinCode);
      openModal("modalQuickEnroll");
    } else {
      showToast(data.error || "Subject not found.", "danger");
      showView("student_dashboard");
    }
  } catch (err) {
    showToast("Failed to verify subject code.", "danger");
    showView("student_dashboard");
  }
}

// ==============================================================================
// VIEW SWITCHER
// ==============================================================================
function showView(viewName) {
  // Stop any active camera streams when changing screens
  stopCamera();

  const views = [
    "viewHome",
    "viewStudentLogin",
    "viewStudentDashboard",
    "viewTeacherAuth",
    "viewTeacherDashboard"
  ];

  views.forEach(v => {
    const el = document.getElementById(v);
    if (el) el.style.display = "none";
  });

  const headerBadge = document.getElementById("headerUserBadge");
  if (headerBadge) {
    if (state.currentUser) {
      headerBadge.style.display = "flex";
      document.getElementById("headerUserName").innerText = state.currentUser.data.name;
      document.getElementById("headerUserRole").innerText = state.currentUser.role;
    } else {
      headerBadge.style.display = "none";
    }
  }

  switch (viewName) {
    case "home":
      document.getElementById("viewHome").style.display = "block";
      break;
    case "student_login":
      document.getElementById("viewStudentLogin").style.display = "block";
      document.getElementById("studentRegisterContainer").style.display = "none";
      startCamera("studentCameraVideo");
      break;
    case "student_dashboard":
      document.getElementById("viewStudentDashboard").style.display = "block";
      loadStudentDashboard();
      break;
    case "teacher_auth":
      document.getElementById("viewTeacherAuth").style.display = "block";
      switchTeacherAuthTab("login");
      break;
    case "teacher_dashboard":
      document.getElementById("viewTeacherDashboard").style.display = "block";
      switchTeacherTab(state.teacherTab || "take_attendance");
      break;
  }
}

// ==============================================================================
// CAMERA & WEBCAM STREAMING
// ==============================================================================
async function startCamera(videoElementId) {
  stopCamera();
  const video = document.getElementById(videoElementId);
  if (!video) return;

  try {
    const stream = await navigator.mediaDevices.getUserMedia({
      video: { width: { ideal: 1280 }, height: { ideal: 720 }, facingMode: "user" },
      audio: false
    });
    state.cameraStream = stream;
    video.srcObject = stream;
    video.play();
  } catch (err) {
    console.error("Camera access error:", err);
    showToast("Camera access was denied or not available. Please allow camera permissions.", "warning");
  }
}

function stopCamera() {
  if (state.cameraStream) {
    state.cameraStream.getTracks().forEach(track => track.stop());
    state.cameraStream = null;
  }
}

function captureSnapshot(videoElementId) {
  const video = document.getElementById(videoElementId);
  if (!video || !video.videoWidth) {
    showToast("Camera stream is not ready yet.", "warning");
    return null;
  }

  const canvas = document.createElement("canvas");
  canvas.width = video.videoWidth;
  canvas.height = video.videoHeight;
  const ctx = canvas.getContext("2d");
  ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
  return canvas.toDataURL("image/jpeg", 0.92);
}

// ==============================================================================
// MICROPHONE & AUDIO RECORDING
// ==============================================================================
async function startAudioRecording(indicatorBtnId, timerElementId) {
  state.audioChunks = [];
  state.recordedAudioBlob = null;
  state.recordingSeconds = 0;

  const btn = document.getElementById(indicatorBtnId);
  const timer = document.getElementById(timerElementId);

  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    state.mediaRecorder = new MediaRecorder(stream);

    state.mediaRecorder.ondataavailable = (e) => {
      if (e.data.size > 0) state.audioChunks.push(e.data);
    };

    state.mediaRecorder.onstop = () => {
      state.recordedAudioBlob = new Blob(state.audioChunks, { type: "audio/wav" });
      stream.getTracks().forEach(t => t.stop());
      clearInterval(state.recordingInterval);
      if (btn) btn.classList.remove("recording");
    };

    state.mediaRecorder.start();
    if (btn) btn.classList.add("recording");

    state.recordingInterval = setInterval(() => {
      state.recordingSeconds++;
      const mins = String(Math.floor(state.recordingSeconds / 60)).padStart(2, "0");
      const secs = String(state.recordingSeconds % 60).padStart(2, "0");
      if (timer) timer.innerText = `${mins}:${secs}`;
    }, 1000);

  } catch (err) {
    console.error("Microphone access error:", err);
    showToast("Microphone permission denied or not available.", "warning");
  }
}

function stopAudioRecording() {
  if (state.mediaRecorder && state.mediaRecorder.state !== "inactive") {
    state.mediaRecorder.stop();
  }
}

// ==============================================================================
// STUDENT PORTAL LOGIC
// ==============================================================================
async function handleStudentFaceLogin() {
  const snapshot = captureSnapshot("studentCameraVideo");
  if (!snapshot) return;

  const btn = document.getElementById("btnStudentScanFace");
  btn.disabled = true;
  btn.innerHTML = `<span class="spinner-border"></span> Scanning Face...`;

  try {
    const res = await fetch("/api/student/login-face", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ image: snapshot })
    });
    const data = await res.json();

    if (data.success) {
      state.currentUser = { role: "student", data: data.student };
      localStorage.setItem("snapclass_user", JSON.stringify(state.currentUser));
      showToast(`Welcome back, ${data.student.name}!`, "success");

      // Check if user clicked a join-code link previously
      const pendingCode = sessionStorage.getItem("pending_join_code");
      if (pendingCode) {
        sessionStorage.removeItem("pending_join_code");
        handleUrlJoinCode(pendingCode);
      } else {
        showView("student_dashboard");
      }
    } else {
      showToast(data.message || data.error, "warning");
      if (data.code === "NOT_RECOGNIZED") {
        // Show Registration Form and cache snapshot
        document.getElementById("studentRegisterContainer").style.display = "block";
        document.getElementById("studentRegisterContainer").scrollIntoView({ behavior: "smooth" });
        state.lastFaceSnapshot = snapshot;
      }
    }
  } catch (err) {
    showToast("Network error during FaceID scan.", "danger");
  } finally {
    btn.disabled = false;
    btn.innerHTML = `📸 Scan My Face`;
  }
}

async function handleStudentRegister() {
  const name = document.getElementById("studentRegName").value.trim();
  if (!name) {
    showToast("Please enter your name.", "warning");
    return;
  }

  const snapshot = state.lastFaceSnapshot || captureSnapshot("studentCameraVideo");
  if (!snapshot) {
    showToast("Face image is required for registration.", "warning");
    return;
  }

  const btn = document.getElementById("btnStudentCreateAccount");
  btn.disabled = true;
  btn.innerHTML = `Creating Profile...`;

  const formData = new FormData();
  formData.append("name", name);
  formData.append("image", snapshot);

  if (state.recordedAudioBlob) {
    formData.append("audio", state.recordedAudioBlob, "voice_sample.wav");
  }

  try {
    const res = await fetch("/api/student/register", {
      method: "POST",
      body: formData
    });
    const data = await res.json();

    if (data.success) {
      state.currentUser = { role: "student", data: data.student };
      localStorage.setItem("snapclass_user", JSON.stringify(state.currentUser));
      showToast(data.message, "success");

      const pendingCode = sessionStorage.getItem("pending_join_code");
      if (pendingCode) {
        sessionStorage.removeItem("pending_join_code");
        handleUrlJoinCode(pendingCode);
      } else {
        showView("student_dashboard");
      }
    } else {
      showToast(data.error || "Registration failed.", "danger");
    }
  } catch (err) {
    showToast("Network error during registration.", "danger");
  } finally {
    btn.disabled = false;
    btn.innerHTML = `Complete Registration`;
  }
}

async function loadStudentDashboard() {
  if (!state.currentUser || state.currentUser.role !== "student") return;

  const studentId = state.currentUser.data.student_id;
  document.getElementById("studentWelcomeName").innerText = state.currentUser.data.name;

  try {
    const res = await fetch(`/api/student/${studentId}/subjects`);
    const data = await res.json();

    if (data.success) {
      renderStudentSubjects(data.subjects);
      renderStudentMetrics(data.summary);
    } else {
      showToast("Failed to load enrolled subjects.", "danger");
    }
  } catch (err) {
    showToast("Network error loading dashboard.", "danger");
  }
}

function renderStudentMetrics(summary) {
  if (!summary) return;
  const container = document.getElementById("studentMetricsRow");
  if (!container) return;

  container.innerHTML = `
    <div class="metric-card">
      <div class="metric-value">${summary.total_enrolled}</div>
      <div class="metric-label">Enrolled Subjects</div>
    </div>
    <div class="metric-card">
      <div class="metric-value">${summary.total_classes}</div>
      <div class="metric-label">Total Sessions</div>
    </div>
    <div class="metric-card">
      <div class="metric-value" style="color: var(--success);">${summary.total_attended}</div>
      <div class="metric-label">Sessions Attended</div>
    </div>
    <div class="metric-card">
      <div class="metric-value" style="color: var(--accent);">${summary.overall_percentage}%</div>
      <div class="metric-label">Overall Attendance</div>
    </div>
  `;
}

function renderStudentSubjects(subjects) {
  const container = document.getElementById("studentSubjectsGrid");
  if (!container) return;

  if (!subjects || subjects.length === 0) {
    container.innerHTML = `
      <div style="grid-column: 1 / -1; text-align: center; padding: 3rem; background: #F8FAFC; border-radius: 16px; border: 1.5px dashed var(--border-subtle);">
        <h3 style="color: var(--text-main); margin-bottom: 8px;">No Enrolled Subjects Yet</h3>
        <p style="color: var(--text-muted); margin-bottom: 1.5rem;">Join a subject using a code from your teacher.</p>
        <button class="btn btn-primary" onclick="openModal('modalEnrollSubject')">➕ Enroll in Subject</button>
      </div>
    `;
    return;
  }

  container.innerHTML = subjects.map(sub => `
    <div class="subject-card">
      <div>
        <div class="subject-title">${escapeHtml(sub.name)}</div>
        <div class="subject-meta">
          <span class="subject-badge">${escapeHtml(sub.subject_code)}</span>
          <span>Section: ${escapeHtml(sub.section || 'All')}</span>
        </div>
        <div class="subject-stats-row">
          <div class="stat-pill">📅 Total: <b>${sub.total_classes}</b></div>
          <div class="stat-pill">✅ Attended: <b>${sub.attended_classes}</b></div>
          <div class="stat-pill">📊 Rate: <b>${sub.percentage}%</b></div>
        </div>
      </div>
      <div>
        <button class="btn btn-outline-danger btn-sm btn-block" onclick="handleUnenrollStudent(${sub.subject_id}, '${escapeHtml(sub.name)}')">
          🗑️ Unenroll
        </button>
      </div>
    </div>
  `).join("");
}

async function handleEnrollSubject() {
  const code = document.getElementById("inputEnrollSubjectCode").value.trim();
  if (!code) {
    showToast("Please enter a subject code.", "warning");
    return;
  }

  try {
    const res = await fetch("/api/student/enroll", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        student_id: state.currentUser.data.student_id,
        subject_code: code
      })
    });
    const data = await res.json();
    if (data.success) {
      showToast(data.message, "success");
      closeModal("modalEnrollSubject");
      document.getElementById("inputEnrollSubjectCode").value = "";
      loadStudentDashboard();
    } else {
      showToast(data.error || "Enrollment failed.", "danger");
    }
  } catch (err) {
    showToast("Network error while enrolling.", "danger");
  }
}

async function confirmQuickEnroll(subjectCode) {
  try {
    const res = await fetch("/api/student/enroll", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        student_id: state.currentUser.data.student_id,
        subject_code: subjectCode
      })
    });
    const data = await res.json();
    if (data.success) {
      showToast(data.message, "success");
      closeModal("modalQuickEnroll");
      window.history.replaceState({}, document.title, window.location.pathname);
      showView("student_dashboard");
    } else {
      showToast(data.error || "Enrollment failed.", "danger");
      closeModal("modalQuickEnroll");
      showView("student_dashboard");
    }
  } catch (err) {
    showToast("Network error during auto-enrollment.", "danger");
  }
}

async function handleUnenrollStudent(subjectId, subjectName) {
  if (!confirm(`Are you sure you want to unenroll from "${subjectName}"?`)) return;

  try {
    const res = await fetch("/api/student/unenroll", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        student_id: state.currentUser.data.student_id,
        subject_id: subjectId
      })
    });
    const data = await res.json();
    if (data.success) {
      showToast(data.message, "success");
      loadStudentDashboard();
    } else {
      showToast(data.error || "Failed to unenroll.", "danger");
    }
  } catch (err) {
    showToast("Network error while unenrolling.", "danger");
  }
}

// ==============================================================================
// TEACHER PORTAL LOGIC
// ==============================================================================
function switchTeacherAuthTab(tabName) {
  const loginTab = document.getElementById("tabTeacherLogin");
  const registerTab = document.getElementById("tabTeacherRegister");
  const loginForm = document.getElementById("formTeacherLogin");
  const registerForm = document.getElementById("formTeacherRegister");

  if (tabName === "login") {
    loginTab.classList.add("active");
    registerTab.classList.remove("active");
    loginForm.style.display = "block";
    registerForm.style.display = "none";
  } else {
    registerTab.classList.add("active");
    loginTab.classList.remove("active");
    registerForm.style.display = "block";
    loginForm.style.display = "none";
  }
}

async function handleTeacherLogin(e) {
  e.preventDefault();
  const username = document.getElementById("teacherLoginUsername").value.trim();
  const password = document.getElementById("teacherLoginPassword").value.trim();

  if (!username || !password) {
    showToast("Please enter both username and password.", "warning");
    return;
  }

  const btn = document.getElementById("btnTeacherLoginSubmit");
  btn.disabled = true;

  try {
    const res = await fetch("/api/teacher/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password })
    });
    const data = await res.json();

    if (data.success) {
      state.currentUser = { role: "teacher", data: data.teacher };
      localStorage.setItem("snapclass_user", JSON.stringify(state.currentUser));
      showToast(`Welcome back, ${data.teacher.name}!`, "success");
      showView("teacher_dashboard");
    } else {
      showToast(data.error || "Invalid username or password.", "danger");
    }
  } catch (err) {
    showToast("Network error during login.", "danger");
  } finally {
    btn.disabled = false;
  }
}

async function handleTeacherRegister(e) {
  e.preventDefault();
  const username = document.getElementById("teacherRegUsername").value.trim();
  const name = document.getElementById("teacherRegName").value.trim();
  const password = document.getElementById("teacherRegPassword").value.trim();
  const confirm = document.getElementById("teacherRegConfirm").value.trim();

  if (!username || !name || !password || !confirm) {
    showToast("All fields are required.", "warning");
    return;
  }

  if (password !== confirm) {
    showToast("Passwords do not match.", "warning");
    return;
  }

  const btn = document.getElementById("btnTeacherRegisterSubmit");
  btn.disabled = true;

  try {
    const res = await fetch("/api/teacher/register", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        username,
        name,
        password,
        confirm_password: confirm
      })
    });
    const data = await res.json();

    if (data.success) {
      showToast(data.message, "success");
      switchTeacherAuthTab("login");
      document.getElementById("teacherLoginUsername").value = username;
    } else {
      showToast(data.error || "Registration failed.", "danger");
    }
  } catch (err) {
    showToast("Network error during registration.", "danger");
  } finally {
    btn.disabled = false;
  }
}

function switchTeacherTab(tabName) {
  state.teacherTab = tabName;
  document.querySelectorAll(".nav-tab-btn").forEach(btn => btn.classList.remove("active"));
  
  const activeBtn = document.getElementById(`tabBtn_${tabName}`);
  if (activeBtn) activeBtn.classList.add("active");

  document.getElementById("teacherPaneTakeAttendance").style.display = tabName === "take_attendance" ? "block" : "none";
  document.getElementById("teacherPaneManageSubjects").style.display = tabName === "manage_subjects" ? "block" : "none";
  document.getElementById("teacherPaneRecords").style.display = tabName === "attendance_records" ? "block" : "none";

  if (tabName === "take_attendance") {
    loadTeacherSubjectsForAttendance();
  } else if (tabName === "manage_subjects") {
    loadTeacherSubjectsList();
  } else if (tabName === "attendance_records") {
    loadTeacherRecordsAndAnalytics();
  }
}

async function loadTeacherSubjectsForAttendance() {
  if (!state.currentUser || state.currentUser.role !== "teacher") return;
  const teacherId = state.currentUser.data.teacher_id;
  const select = document.getElementById("selectAttendanceSubject");

  try {
    const res = await fetch(`/api/teacher/${teacherId}/subjects`);
    const data = await res.json();

    if (data.success && data.subjects.length > 0) {
      select.innerHTML = data.subjects.map(s => `
        <option value="${s.subject_id}">${escapeHtml(s.name)} (${escapeHtml(s.subject_code)})</option>
      `).join("");
      renderAttendancePhotosGallery();
    } else {
      select.innerHTML = `<option value="">No subjects created yet</option>`;
      renderAttendancePhotosGallery();
    }
  } catch (err) {
    showToast("Failed to load subjects for attendance.", "danger");
  }
}

function renderAttendancePhotosGallery() {
  const container = document.getElementById("attendancePhotosGallery");
  const clearBtn = document.getElementById("btnClearAttendancePhotos");
  const runBtn = document.getElementById("btnRunFaceScan");

  const hasPhotos = state.attendancePhotos.length > 0;
  if (clearBtn) clearBtn.disabled = !hasPhotos;
  if (runBtn) runBtn.disabled = !hasPhotos;

  if (!container) return;

  if (!hasPhotos) {
    container.innerHTML = `
      <div style="grid-column: 1 / -1; text-align: center; padding: 2rem; color: var(--text-muted); background: #F8FAFC; border-radius: 12px; border: 1.5px dashed var(--border-subtle);">
        No classroom photos added yet. Click <b>"➕ Add Photos"</b> above to snap or upload classroom images.
      </div>
    `;
    return;
  }

  container.innerHTML = state.attendancePhotos.map((photo, idx) => `
    <div class="photo-thumb-card">
      <img src="${photo}" alt="Classroom photo ${idx + 1}" />
      <button class="remove-btn" onclick="removeAttendancePhoto(${idx})" title="Remove photo">✕</button>
      <div class="photo-caption">Photo ${idx + 1}</div>
    </div>
  `).join("");
}

function removeAttendancePhoto(index) {
  state.attendancePhotos.splice(index, 1);
  renderAttendancePhotosGallery();
}

function clearAllAttendancePhotos() {
  state.attendancePhotos = [];
  renderAttendancePhotosGallery();
  showToast("Cleared all classroom photos.", "info");
}

// Dialog: Add Photos (Camera vs File Upload)
function openAddPhotosModal() {
  openModal("modalAddPhotos");
  switchAddPhotoSource("camera");
}

function switchAddPhotoSource(source) {
  const camBtn = document.getElementById("btnPhotoSourceCamera");
  const fileBtn = document.getElementById("btnPhotoSourceUpload");
  const camPane = document.getElementById("panePhotoSourceCamera");
  const filePane = document.getElementById("panePhotoSourceUpload");

  if (source === "camera") {
    camBtn.classList.add("btn-primary");
    camBtn.classList.remove("btn-tertiary");
    fileBtn.classList.add("btn-tertiary");
    fileBtn.classList.remove("btn-primary");
    camPane.style.display = "block";
    filePane.style.display = "none";
    startCamera("teacherCameraVideo");
  } else {
    stopCamera();
    fileBtn.classList.add("btn-primary");
    fileBtn.classList.remove("btn-tertiary");
    camBtn.classList.add("btn-tertiary");
    camBtn.classList.remove("btn-primary");
    filePane.style.display = "block";
    camPane.style.display = "none";
  }
}

function handleSnapClassroomPhoto() {
  const snapshot = captureSnapshot("teacherCameraVideo");
  if (snapshot) {
    state.attendancePhotos.push(snapshot);
    renderAttendancePhotosGallery();
    showToast(`Captured Photo #${state.attendancePhotos.length}`, "success");
  }
}

function handleUploadClassroomPhotos(e) {
  const files = e.target.files;
  if (!files || files.length === 0) return;

  Array.from(files).forEach(file => {
    const reader = new FileReader();
    reader.onload = (evt) => {
      state.attendancePhotos.push(evt.target.result);
      renderAttendancePhotosGallery();
    };
    reader.readAsDataURL(file);
  });

  showToast(`Added ${files.length} photo(s).`, "success");
}

// Run Face Analysis
async function handleRunFaceAnalysis() {
  const select = document.getElementById("selectAttendanceSubject");
  const subjectId = select.value;
  if (!subjectId) {
    showToast("Please create and select a subject first.", "warning");
    return;
  }

  if (state.attendancePhotos.length === 0) {
    showToast("Please add classroom photos before running face analysis.", "warning");
    return;
  }

  const btn = document.getElementById("btnRunFaceScan");
  btn.disabled = true;
  btn.innerHTML = `<span class="spinner-border"></span> Deep scanning photos...`;

  try {
    const res = await fetch("/api/attendance/face-scan", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        subject_id: subjectId,
        images: state.attendancePhotos
      })
    });
    const data = await res.json();

    if (data.success) {
      state.pendingAttendance = data;
      renderAttendancePreviewModal(data);
      openModal("modalAttendanceResults");
    } else {
      showToast(data.error || "Face analysis scan failed.", "danger");
    }
  } catch (err) {
    showToast("Network error during face analysis.", "danger");
  } finally {
    btn.disabled = false;
    btn.innerHTML = `🔍 Run Face Analysis`;
  }
}

// Voice Attendance Modal & Run
function openVoiceAttendanceModal() {
  const select = document.getElementById("selectAttendanceSubject");
  if (!select.value) {
    showToast("Please select a subject first.", "warning");
    return;
  }
  state.recordedAudioBlob = null;
  document.getElementById("voiceRecordTimer").innerText = "00:00";
  openModal("modalVoiceAttendance");
}

async function handleRunVoiceAnalysis() {
  const select = document.getElementById("selectAttendanceSubject");
  const subjectId = select.value;

  if (!state.recordedAudioBlob) {
    showToast("Please record or select an audio sample first.", "warning");
    return;
  }

  const btn = document.getElementById("btnRunVoiceScan");
  btn.disabled = true;
  btn.innerHTML = `<span class="spinner-border"></span> Analyzing classroom voices...`;

  const formData = new FormData();
  formData.append("subject_id", subjectId);
  formData.append("audio", state.recordedAudioBlob, "classroom_audio.wav");

  try {
    const res = await fetch("/api/attendance/voice-scan", {
      method: "POST",
      body: formData
    });
    const data = await res.json();

    if (data.success) {
      closeModal("modalVoiceAttendance");
      state.pendingAttendance = data;
      renderAttendancePreviewModal(data);
      openModal("modalAttendanceResults");
    } else {
      showToast(data.error || "Voice analysis failed.", "danger");
    }
  } catch (err) {
    showToast("Network error during voice analysis.", "danger");
  } finally {
    btn.disabled = false;
    btn.innerHTML = `Analyze Audio`;
  }
}

function renderAttendancePreviewModal(data) {
  const tbody = document.getElementById("tableAttendancePreviewBody");
  if (!tbody) return;

  tbody.innerHTML = data.results.map(r => `
    <tr>
      <td><b>${escapeHtml(r.name)}</b></td>
      <td>#${r.student_id}</td>
      <td>${escapeHtml(String(r.source))}</td>
      <td>
        <span class="status-badge ${r.is_present ? 'present' : 'absent'}">
          ${r.is_present ? '✅ Present' : '❌ Absent'}
        </span>
      </td>
    </tr>
  `).join("");
}

async function handleConfirmAttendance() {
  if (!state.pendingAttendance || !state.pendingAttendance.logs) return;

  const btn = document.getElementById("btnConfirmAttendanceLogs");
  btn.disabled = true;

  try {
    const res = await fetch("/api/attendance/confirm", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ logs: state.pendingAttendance.logs })
    });
    const data = await res.json();

    if (data.success) {
      showToast("Attendance successfully saved to Supabase!", "success");
      closeModal("modalAttendanceResults");
      state.pendingAttendance = null;
      state.attendancePhotos = [];
      renderAttendancePhotosGallery();
    } else {
      showToast(data.error || "Failed to save attendance logs.", "danger");
    }
  } catch (err) {
    showToast("Network error saving attendance.", "danger");
  } finally {
    btn.disabled = false;
  }
}

// Teacher Tab 2: Manage Subjects
async function loadTeacherSubjectsList() {
  if (!state.currentUser || state.currentUser.role !== "teacher") return;
  const teacherId = state.currentUser.data.teacher_id;
  const container = document.getElementById("teacherSubjectsGrid");

  try {
    const res = await fetch(`/api/teacher/${teacherId}/subjects`);
    const data = await res.json();

    if (data.success) {
      if (data.subjects.length === 0) {
        container.innerHTML = `
          <div style="grid-column: 1 / -1; text-align: center; padding: 3rem; background: #F8FAFC; border-radius: 16px; border: 1.5px dashed var(--border-subtle);">
            <h3>No Subjects Created Yet</h3>
            <p style="color: var(--text-muted); margin-bottom: 1.5rem;">Create a course for students to enroll and scan attendance.</p>
            <button class="btn btn-primary" onclick="openModal('modalCreateSubject')">➕ Create First Subject</button>
          </div>
        `;
        return;
      }

      container.innerHTML = data.subjects.map(sub => `
        <div class="subject-card">
          <div>
            <div class="subject-title">${escapeHtml(sub.name)}</div>
            <div class="subject-meta">
              <span class="subject-badge">${escapeHtml(sub.subject_code)}</span>
              <span>Section: ${escapeHtml(sub.section)}</span>
            </div>
            <div class="subject-stats-row">
              <div class="stat-pill">🫂 Students: <b>${sub.total_students}</b></div>
              <div class="stat-pill">🕰️ Classes Held: <b>${sub.total_classes}</b></div>
            </div>
          </div>
          <div>
            <button class="btn btn-tertiary btn-sm btn-block" onclick="openShareSubjectModal('${escapeHtml(sub.name)}', '${escapeHtml(sub.subject_code)}')">
              🔗 Share Join Code
            </button>
          </div>
        </div>
      `).join("");
    }
  } catch (err) {
    showToast("Failed to load subjects.", "danger");
  }
}

async function handleCreateSubject() {
  const code = document.getElementById("inputNewSubCode").value.trim();
  const name = document.getElementById("inputNewSubName").value.trim();
  const section = document.getElementById("inputNewSubSection").value.trim();

  if (!code || !name || !section) {
    showToast("Please fill in all subject fields.", "warning");
    return;
  }

  try {
    const res = await fetch("/api/teacher/subjects", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        teacher_id: state.currentUser.data.teacher_id,
        subject_code: code,
        name: name,
        section: section
      })
    });
    const data = await res.json();

    if (data.success) {
      showToast("Subject created successfully!", "success");
      closeModal("modalCreateSubject");
      document.getElementById("inputNewSubCode").value = "";
      document.getElementById("inputNewSubName").value = "";
      document.getElementById("inputNewSubSection").value = "";
      loadTeacherSubjectsList();
    } else {
      showToast(data.error || "Failed to create subject.", "danger");
    }
  } catch (err) {
    showToast("Network error creating subject.", "danger");
  }
}

function openShareSubjectModal(name, code) {
  const host = window.location.origin;
  const joinUrl = `${host}/?join-code=${encodeURIComponent(code)}`;

  document.getElementById("shareSubTitle").innerText = name;
  document.getElementById("shareSubLink").innerText = joinUrl;
  document.getElementById("shareSubCode").innerText = code;
  document.getElementById("shareQrImage").src = `/api/subject/${encodeURIComponent(code)}/qr`;

  openModal("modalShareSubject");
}

function copyShareLink() {
  const linkText = document.getElementById("shareSubLink").innerText;
  navigator.clipboard.writeText(linkText).then(() => {
    showToast("Class link copied to clipboard!", "success");
  });
}

function copyShareCode() {
  const codeText = document.getElementById("shareSubCode").innerText;
  navigator.clipboard.writeText(codeText).then(() => {
    showToast("Subject code copied to clipboard!", "success");
  });
}

// Teacher Tab 3: Records & Analytics
async function loadTeacherRecordsAndAnalytics() {
  if (!state.currentUser || state.currentUser.role !== "teacher") return;
  const teacherId = state.currentUser.data.teacher_id;

  // 1. Load Summary Sessions
  try {
    const res = await fetch(`/api/teacher/${teacherId}/attendance-records`);
    const data = await res.json();
    if (data.success) {
      const tbody = document.getElementById("tableTeacherRecordsBody");
      if (data.sessions.length === 0) {
        tbody.innerHTML = `<tr><td colspan="4" style="text-align: center; color: var(--text-muted);">No attendance records found yet.</td></tr>`;
      } else {
        tbody.innerHTML = data.sessions.map(s => `
          <tr>
            <td>${escapeHtml(s.formatted_time)}</td>
            <td><b>${escapeHtml(s.subject_name)}</b></td>
            <td><span class="subject-badge">${escapeHtml(s.subject_code)}</span></td>
            <td>
              <span class="status-badge present">
                ✅ ${s.present_count} / ${s.total_count} Students
              </span>
            </td>
          </tr>
        `).join("");
      }
    }
  } catch (err) {
    console.error("Error loading records:", err);
  }

  // 2. Load Chart.js Analytics
  try {
    const res = await fetch(`/api/teacher/${teacherId}/analytics`);
    const data = await res.json();
    if (data.success) {
      // Metric cards
      document.getElementById("teacherTotalStudentsMetric").innerText = data.totals.total_students_enrolled;
      document.getElementById("teacherTotalSubjectsMetric").innerText = data.totals.total_subjects;
      document.getElementById("teacherAverageAttendanceMetric").innerText = `${data.totals.average_attendance}%`;

      // Render Chart.js
      if (window.renderAnalyticsCharts) {
        renderAnalyticsCharts(data);
      }
    }
  } catch (err) {
    console.error("Error loading analytics:", err);
  }
}

// ==============================================================================
// AUTHENTICATION LOGOUT & HELPERS
// ==============================================================================
function handleLogout() {
  state.currentUser = null;
  localStorage.removeItem("snapclass_user");
  showToast("Logged out successfully.", "info");
  showView("home");
}

function openModal(id) {
  const modal = document.getElementById(id);
  if (modal) modal.classList.add("active");
}

function closeModal(id) {
  const modal = document.getElementById(id);
  if (modal) {
    modal.classList.remove("active");
    stopCamera();
    stopAudioRecording();
  }
}

// Toast Notification Manager
function showToast(message, type = "info") {
  const container = document.getElementById("toastContainer");
  if (!container) return;

  const toast = document.createElement("div");
  toast.className = `toast toast-${type}`;
  toast.innerHTML = `<span>${escapeHtml(message)}</span>`;

  container.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = "0";
    toast.style.transform = "translateX(100%)";
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}

function escapeHtml(str) {
  return String(str || "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

// Setup Event Listeners
function setupEventListeners() {
  // Navigation / Modal backdrop click closing
  document.querySelectorAll(".modal-backdrop").forEach(backdrop => {
    backdrop.addEventListener("click", (e) => {
      if (e.target === backdrop) closeModal(backdrop.id);
    });
  });

  // Teacher Auth Form submissions
  const formLogin = document.getElementById("formTeacherLogin");
  if (formLogin) formLogin.addEventListener("submit", handleTeacherLogin);

  const formRegister = document.getElementById("formTeacherRegister");
  if (formRegister) formRegister.addEventListener("submit", handleTeacherRegister);

  // Audio recording buttons
  const recStudentVoiceBtn = document.getElementById("btnRecStudentVoice");
  if (recStudentVoiceBtn) {
    recStudentVoiceBtn.addEventListener("click", () => {
      if (state.mediaRecorder && state.mediaRecorder.state === "recording") {
        stopAudioRecording();
        showToast("Voice sample captured!", "success");
      } else {
        startAudioRecording("btnRecStudentVoice", "studentVoiceTimer");
        showToast("Recording started. Speak: 'I am present, my name is...'", "info");
      }
    });
  }

  const recTeacherVoiceBtn = document.getElementById("btnRecTeacherVoice");
  if (recTeacherVoiceBtn) {
    recTeacherVoiceBtn.addEventListener("click", () => {
      if (state.mediaRecorder && state.mediaRecorder.state === "recording") {
        stopAudioRecording();
        showToast("Classroom audio recording finished.", "success");
      } else {
        startAudioRecording("btnRecTeacherVoice", "voiceRecordTimer");
        showToast("Recording classroom audio...", "info");
      }
    });
  }
}
