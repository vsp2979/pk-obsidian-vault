// OmniView360 Frontend Application Controller

let currentStep = 1;
let selectedVideo = null;
let selectedMusic = null;
let videoProbeData = null;
let previewThreeScene = null;

const stepHeadings = [
  "Step 1: Import Video from Camera",
  "Step 2: Clean, Trim & Color Enhance",
  "Step 3: Add Music & Smart Voice Ducking",
  "Step 4: Interactive 360 Preview & Publish"
];

document.addEventListener('DOMContentLoaded', () => {
  initStatus();
  initWizardNav();
  initStep1Import();
  initStep2Clean();
  initStep3Audio();
  initStep4Publish();
  refreshFiles();
});

// 1. Initial Status & Connection
async function initStatus() {
  try {
    const res = await fetch('/api/status');
    const data = await res.json();
    if (data.share_url) {
      document.getElementById('lanShareUrl').textContent = data.share_url;
    }
  } catch (err) {
    console.error("Status check failed:", err);
  }
}

// 2. Wizard Navigation
function initWizardNav() {
  const navBtns = document.querySelectorAll('.nav-item');
  const btnPrev = document.getElementById('btnPrevStep');
  const btnNext = document.getElementById('btnNextStep');

  navBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      const step = parseInt(btn.dataset.step);
      goToStep(step);
    });
  });

  btnPrev.addEventListener('click', () => {
    if (currentStep > 1) goToStep(currentStep - 1);
  });

  btnNext.addEventListener('click', () => {
    if (currentStep < 4) goToStep(currentStep + 1);
  });
}

function goToStep(step) {
  if (step === 2 && !selectedVideo) {
    alert("Please select or upload a video first in Step 1.");
    return;
  }

  currentStep = step;
  document.querySelectorAll('.wizard-step').forEach(el => el.classList.remove('active'));
  document.getElementById(`step${step}`).classList.add('active');

  document.querySelectorAll('.nav-item').forEach(el => {
    el.classList.toggle('active', parseInt(el.dataset.step) === step);
  });

  document.getElementById('stepHeading').textContent = stepHeadings[step - 1];

  const btnPrev = document.getElementById('btnPrevStep');
  const btnNext = document.getElementById('btnNextStep');
  btnPrev.disabled = (step === 1);

  if (step === 4) {
    btnNext.style.display = 'none';
    initThreePreview();
  } else {
    btnNext.style.display = 'inline-flex';
    const nextTitles = ["Continue to Clean & Trim →", "Continue to Music & Ducking →", "Continue to 360 Preview & Share →"];
    btnNext.textContent = nextTitles[step - 1];
  }
}

// 3. Step 1: Import from Camera & Local
function initStep1Import() {
  const btnScan = document.getElementById('btnScanDevices');
  const dropZone = document.getElementById('videoDropZone');
  const fileInput = document.getElementById('videoFileInput');

  btnScan.addEventListener('click', scanDevices);

  // Drag and drop video
  dropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropZone.classList.add('dragover');
  });

  dropZone.addEventListener('dragleave', () => dropZone.classList.remove('dragover'));

  dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropZone.classList.remove('dragover');
    if (e.dataTransfer.files.length > 0) {
      uploadVideoFile(e.dataTransfer.files[0]);
    }
  });

  fileInput.addEventListener('change', () => {
    if (fileInput.files.length > 0) {
      uploadVideoFile(fileInput.files[0]);
    }
  });

  scanDevices();
}

async function scanDevices() {
  const listEl = document.getElementById('deviceList');
  listEl.innerHTML = '<div class="hint">Scanning for connected cameras...</div>';
  try {
    const res = await fetch('/api/devices');
    const data = await res.json();
    if (!data.devices || data.devices.length === 0) {
      listEl.innerHTML = `
        <div class="empty-state">
          No camera card detected under /Volumes.
          <br><small class="hint">Connect your Insta360 via USB mass-storage mode or browse local files below.</small>
        </div>`;
      return;
    }

    listEl.innerHTML = '';
    data.devices.forEach(dev => {
      const item = document.createElement('div');
      item.className = 'file-row';
      item.innerHTML = `
        <div>
          <strong>${dev.name}</strong>
          <span class="file-badge">Camera / SD</span>
          <br><small class="hint">${dev.path}</small>
        </div>
        <button class="btn btn-secondary btn-scan-card" data-path="${dev.path}">Scan Files</button>
      `;
      listEl.appendChild(item);
    });

    document.querySelectorAll('.btn-scan-card').forEach(btn => {
      btn.addEventListener('click', () => scanCardFiles(btn.dataset.path));
    });
  } catch (err) {
    listEl.innerHTML = `<div class="hint">Could not scan devices: ${err.message}</div>`;
  }
}

async function scanCardFiles(path) {
  try {
    const res = await fetch(`/api/scan?path=${encodeURIComponent(path)}`);
    const data = await res.json();
    if (data.files && data.files.length > 0) {
      alert(`Found ${data.files.length} Insta360 videos on ${path}! Importing first item...`);
      importCameraFile(data.files[0].path);
    } else {
      alert("No .insv or .mp4 files found on this device.");
    }
  } catch (err) {
    alert("Error scanning card: " + err.message);
  }
}

async function importCameraFile(filePath) {
  try {
    const res = await fetch('/api/import', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ file_path: filePath })
    });
    const data = await res.json();
    if (data.status === 'imported') {
      refreshFiles();
    }
  } catch (err) {
    alert("Import error: " + err.message);
  }
}

async function uploadVideoFile(file) {
  const dropZone = document.getElementById('videoDropZone');
  dropZone.innerHTML = `<div class="hint">Uploading ${file.name} (${(file.size / 1024 / 1024).toFixed(1)} MB)...</div>`;

  const formData = new FormData();
  formData.append('file', file, file.name);

  try {
    const res = await fetch('/api/upload_video', {
      method: 'POST',
      body: formData
    });
    const data = await res.json();
    if (data.status === 'uploaded') {
      refreshFiles();
      dropZone.innerHTML = `
        <svg viewBox="0 0 24 24" class="drop-icon"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>
        <p>Uploaded <strong>${file.name}</strong> successfully!</p>
        <label class="btn btn-primary file-label">Browse Another<input type="file" id="videoFileInput" accept=".insv,.mp4,.mov" hidden></label>
      `;
    }
  } catch (err) {
    alert("Upload failed: " + err.message);
  }
}

async function refreshFiles() {
  try {
    const res = await fetch('/api/files');
    const data = await res.json();
    renderRawList(data.raw_videos);
    renderMusicList(data.music_tracks);
  } catch (err) {
    console.error("Failed to refresh files:", err);
  }
}

function renderRawList(files) {
  const container = document.getElementById('rawFilesList');
  if (!files || files.length === 0) {
    container.innerHTML = '<p class="hint">No videos loaded yet. Drop a file above to begin.</p>';
    return;
  }

  container.innerHTML = '';
  files.forEach((f, idx) => {
    const row = document.createElement('div');
    row.className = 'file-row' + (selectedVideo && selectedVideo.path === f.path ? ' selected' : '');
    row.innerHTML = `
      <div>
        <strong>${f.name}</strong>
        <span class="file-badge">${f.ext.toUpperCase()}</span>
        <span class="file-badge">${f.size_mb} MB</span>
      </div>
      <button class="btn btn-secondary btn-select-vid" data-idx="${idx}">
        ${selectedVideo && selectedVideo.path === f.path ? '✓ Selected' : 'Select'}
      </button>
    `;
    container.appendChild(row);
  });

  document.querySelectorAll('.btn-select-vid').forEach(btn => {
    btn.addEventListener('click', (e) => {
      const idx = parseInt(e.target.dataset.idx);
      selectedVideo = files[idx];
      document.querySelectorAll('#rawFilesList .file-row').forEach((r, i) => {
        r.classList.toggle('selected', i === idx);
        r.querySelector('.btn-select-vid').textContent = (i === idx ? '✓ Selected' : 'Select');
      });
      loadVideoIntoStep2(selectedVideo);
    });
  });

  // Auto-select first video if none selected
  if (!selectedVideo && files.length > 0) {
    selectedVideo = files[0];
    loadVideoIntoStep2(selectedVideo);
  }
}

// 4. Step 2: Clean, Trim & Color
async function loadVideoIntoStep2(videoObj) {
  if (!videoObj) return;
  const player = document.getElementById('sourceVideoPlayer');
  const mediaUrl = `/media/uploads/raw/${encodeURIComponent(videoObj.name)}`;
  player.src = mediaUrl;

  try {
    const res = await fetch('/api/probe', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ file_path: videoObj.path })
    });
    videoProbeData = await res.json();
    if (videoProbeData.duration) {
      document.getElementById('trimEnd').value = videoProbeData.duration.toFixed(1);
    }
  } catch (err) {
    console.warn("Probe warning:", err);
  }
}

function initStep2Clean() {
  const bIn = document.getElementById('brightnessInput');
  const bVal = document.getElementById('brightnessVal');
  const cIn = document.getElementById('contrastInput');
  const cVal = document.getElementById('contrastVal');
  const sIn = document.getElementById('saturationInput');
  const sVal = document.getElementById('saturationVal');
  const player = document.getElementById('sourceVideoPlayer');

  function updateVideoFilter() {
    bVal.textContent = bIn.value;
    cVal.textContent = cIn.value;
    sVal.textContent = sIn.value;

    // Apply live CSS filter for instant visual preview
    const bCss = 1 + parseFloat(bIn.value);
    const cCss = parseFloat(cIn.value);
    const sCss = parseFloat(sIn.value);
    player.style.filter = `brightness(${bCss}) contrast(${cCss}) saturate(${sCss})`;
  }

  bIn.addEventListener('input', updateVideoFilter);
  cIn.addEventListener('input', updateVideoFilter);
  sIn.addEventListener('input', updateVideoFilter);
}

// 5. Step 3: Music & Ducking
function initStep3Audio() {
  const musicDrop = document.getElementById('musicDropZone');
  const musicInput = document.getElementById('musicFileInput');

  musicDrop.addEventListener('dragover', (e) => {
    e.preventDefault();
    musicDrop.classList.add('dragover');
  });

  musicDrop.addEventListener('dragleave', () => musicDrop.classList.remove('dragover'));

  musicDrop.addEventListener('drop', (e) => {
    e.preventDefault();
    musicDrop.classList.remove('dragover');
    if (e.dataTransfer.files.length > 0) {
      uploadMusicFile(e.dataTransfer.files[0]);
    }
  });

  musicInput.addEventListener('change', () => {
    if (musicInput.files.length > 0) {
      uploadMusicFile(musicInput.files[0]);
    }
  });

  const camVol = document.getElementById('cameraVolInput');
  const camVal = document.getElementById('cameraVolVal');
  const musVol = document.getElementById('musicVolInput');
  const musVal = document.getElementById('musicVolVal');

  camVol.addEventListener('input', () => camVal.textContent = `${Math.round(camVol.value * 100)}%`);
  musVol.addEventListener('input', () => musVal.textContent = `${Math.round(musVol.value * 100)}%`);
}

async function uploadMusicFile(file) {
  const musicDrop = document.getElementById('musicDropZone');
  musicDrop.innerHTML = `<div class="hint">Uploading music: ${file.name}...</div>`;

  const formData = new FormData();
  formData.append('file', file, file.name);

  try {
    const res = await fetch('/api/upload_music', { method: 'POST', body: formData });
    const data = await res.json();
    if (data.status === 'uploaded') {
      refreshFiles();
      musicDrop.innerHTML = `
        <svg viewBox="0 0 24 24" class="drop-icon"><path d="M9 18V5l12-2v13"/><circle cx="6" cy="18" r="3"/><circle cx="18" cy="16" r="3"/></svg>
        <p>Soundtrack <strong>${file.name}</strong> loaded!</p>
        <label class="btn btn-secondary file-label mt-10">Select Another<input type="file" id="musicFileInput" accept=".mp3,.wav,.m4a,.aac" hidden></label>
      `;
    }
  } catch (err) {
    alert("Music upload failed: " + err.message);
  }
}

function renderMusicList(tracks) {
  const container = document.getElementById('musicFileList');
  if (!tracks || tracks.length === 0) {
    container.innerHTML = '<small class="hint">No music chosen yet. The video\'s original ambient sound will be kept.</small>';
    return;
  }

  container.innerHTML = '';
  tracks.forEach((t, idx) => {
    const row = document.createElement('div');
    row.className = 'file-row' + (selectedMusic && selectedMusic.path === t.path ? ' selected' : '');
    row.innerHTML = `
      <div>
        <strong>🎵 ${t.name}</strong>
        <span class="file-badge">${t.size_mb} MB</span>
      </div>
      <button class="btn btn-secondary btn-select-music" data-idx="${idx}">
        ${selectedMusic && selectedMusic.path === t.path ? '✓ Selected' : 'Use This'}
      </button>
    `;
    container.appendChild(row);
  });

  document.querySelectorAll('.btn-select-music').forEach(btn => {
    btn.addEventListener('click', (e) => {
      const idx = parseInt(e.target.dataset.idx);
      selectedMusic = tracks[idx];
      document.querySelectorAll('#musicFileList .file-row').forEach((r, i) => {
        r.classList.toggle('selected', i === idx);
        r.querySelector('.btn-select-music').textContent = (i === idx ? '✓ Selected' : 'Use This');
      });
    });
  });

  if (!selectedMusic && tracks.length > 0) {
    selectedMusic = tracks[0];
  }
}

// 6. Step 4: Interactive 360 Preview & Publish
function initThreePreview() {
  const container = document.getElementById('preview360Container');
  if (previewThreeScene || !selectedVideo) return;

  const player = document.getElementById('sourceVideoPlayer');
  const width = container.clientWidth || 800;
  const height = container.clientHeight || 400;

  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(75, width / height, 0.1, 1000);
  camera.target = new THREE.Vector3(0, 0, 0);

  const renderer = new THREE.WebGLRenderer({ antialias: true });
  renderer.setSize(width, height);
  container.appendChild(renderer.domElement);

  const geometry = new THREE.SphereGeometry(500, 60, 40);
  geometry.scale(-1, 1, 1);

  const texture = new THREE.VideoTexture(player);
  const material = new THREE.MeshBasicMaterial({ map: texture });
  const mesh = new THREE.Mesh(geometry, material);
  scene.add(mesh);

  let isInteracting = false;
  let lon = 0, lat = 0, onPointerDownLon = 0, onPointerDownLat = 0, onPointerDownX = 0, onPointerDownY = 0;

  renderer.domElement.addEventListener('pointerdown', (e) => {
    isInteracting = true;
    onPointerDownX = e.clientX;
    onPointerDownY = e.clientY;
    onPointerDownLon = lon;
    onPointerDownLat = lat;
  });

  window.addEventListener('pointermove', (e) => {
    if (!isInteracting) return;
    lon = (onPointerDownX - e.clientX) * 0.15 + onPointerDownLon;
    lat = (e.clientY - onPointerDownY) * 0.15 + onPointerDownLat;
  });

  window.addEventListener('pointerup', () => isInteracting = false);

  function animate() {
    requestAnimationFrame(animate);
    lat = Math.max(-85, Math.min(85, lat));
    const phi = THREE.MathUtils.degToRad(90 - lat);
    const theta = THREE.MathUtils.degToRad(lon);

    camera.target.x = 500 * Math.sin(phi) * Math.cos(theta);
    camera.target.y = 500 * Math.cos(phi);
    camera.target.z = 500 * Math.sin(phi) * Math.sin(theta);
    camera.lookAt(camera.target);

    renderer.render(scene, camera);
  }

  animate();
  previewThreeScene = { scene, camera, renderer };
}

function initStep4Publish() {
  const btnProcess = document.getElementById('btnStartProcessing');
  btnProcess.addEventListener('click', startPublishPipeline);

  document.getElementById('btnOpenWeb').addEventListener('click', () => {
    const url = document.getElementById('shareWebUrl').value;
    if (url) window.open(url, '_blank');
  });

  document.getElementById('btnCopyWeb').addEventListener('click', () => {
    const url = document.getElementById('shareWebUrl').value;
    navigator.clipboard.writeText(url).then(() => alert("Copied 360 link to clipboard!"));
  });
}

async function startPublishPipeline() {
  if (!selectedVideo) {
    alert("Please select a video to process.");
    return;
  }

  const btnProcess = document.getElementById('btnStartProcessing');
  btnProcess.disabled = true;

  const progressCard = document.getElementById('progressCard');
  const resultCard = document.getElementById('resultCard');
  progressCard.style.display = 'block';
  resultCard.style.display = 'none';

  const params = {
    video_path: selectedVideo.path,
    music_path: selectedMusic ? selectedMusic.path : null,
    title: document.getElementById('projectTitleInput').value || "My 360 Experience",
    start_time: parseFloat(document.getElementById('trimStart').value || 0),
    end_time: parseFloat(document.getElementById('trimEnd').value || 0) || null,
    brightness: parseFloat(document.getElementById('brightnessInput').value),
    contrast: parseFloat(document.getElementById('contrastInput').value),
    saturation: parseFloat(document.getElementById('saturationInput').value),
    sharpness: document.getElementById('sharpnessToggle').checked,
    camera_volume: parseFloat(document.getElementById('cameraVolInput').value),
    music_volume: parseFloat(document.getElementById('musicVolInput').value),
    enable_ducking: document.getElementById('duckingToggle').checked,
    resolution: document.getElementById('resolutionSelect').value
  };

  try {
    const res = await fetch('/api/process', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(params)
    });
    const data = await res.json();
    if (data.job_id) {
      pollJob(data.job_id);
    }
  } catch (err) {
    alert("Pipeline error: " + err.message);
    btnProcess.disabled = false;
  }
}

function pollJob(jobId) {
  const fill = document.getElementById('progressFill');
  const stepText = document.getElementById('progressStepText');
  const pctText = document.getElementById('progressPctText');
  const btnProcess = document.getElementById('btnStartProcessing');

  const timer = setInterval(async () => {
    try {
      const res = await fetch(`/api/job_status?job_id=${jobId}`);
      const job = await res.json();

      fill.style.width = `${job.progress}%`;
      pctText.textContent = `${job.progress}%`;
      stepText.textContent = job.step || "Processing...";

      if (job.status === 'completed') {
        clearInterval(timer);
        btnProcess.disabled = false;
        document.getElementById('progressCard').style.display = 'none';
        showResults(job.result);
      } else if (job.status === 'failed') {
        clearInterval(timer);
        btnProcess.disabled = false;
        alert("Processing failed: " + job.error);
      }
    } catch (err) {
      console.warn("Polling error:", err);
    }
  }, 700);
}

function showResults(result) {
  const resultCard = document.getElementById('resultCard');
  resultCard.style.display = 'block';

  document.getElementById('shareWebUrl').value = result.web_view_url;
  document.getElementById('btnDownloadMp4').href = result.mp4_rel;
  document.getElementById('btnDownloadZip').href = result.zip_rel;

  resultCard.scrollIntoView({ behavior: 'smooth' });
}
