const API_BASE = '/api/v1';
const ROLE_PERMISSIONS = {
  admin: ['dashboard','patients','patients_manage','etl','etl_execute','etl_delete','analytics','ml','reports','reports_export','settings','users_manage'],
  doctor: ['dashboard','patients','analytics','ml','reports'],
  analyst: ['dashboard','patients','etl','etl_execute','analytics','reports','reports_export'],
  viewer: ['dashboard','patients','reports'],
};
let currentUserRole = null;

function getToken() {
  return localStorage.getItem('access_token');
}

async function apiRequest(endpoint, options = {}) {
  const token = getToken();
  const url = endpoint.startsWith('http') ? endpoint : API_BASE + endpoint;
  const headers = { 'Content-Type': 'application/json', ...(options.headers || {}) };
  if (token) headers['Authorization'] = 'Bearer ' + token;
  let res = await fetch(url, { ...options, headers });
  if (res.status === 401) {
    const refresh = localStorage.getItem('refresh_token');
    if (refresh) {
      const r = await fetch(API_BASE + '/auth/token/refresh/', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ refresh }) });
      if (r.ok) {
        const d = await r.json();
        localStorage.setItem('access_token', d.access);
        if (d.refresh) localStorage.setItem('refresh_token', d.refresh);
        headers['Authorization'] = 'Bearer ' + d.access;
        res = await fetch(url, { ...options, headers });
      } else {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        window.location.href = '/';
        return;
      }
    } else {
      localStorage.removeItem('access_token');
      window.location.href = '/';
      return;
    }
  }
  const ct = res.headers.get('content-type') || '';
  if (!res.ok) {
    try { const e = await res.json(); throw new Error(e.error || e.detail || 'Error ' + res.status); }
    catch (x) { if (x instanceof TypeError) throw new Error('Error ' + res.status); throw x; }
  }
  if (ct.includes('application/json')) return res.json();
  return res.text();
}

function showToast(message, type) {
  const c = document.getElementById('toast-container');
  if (!c) return;
  const t = document.createElement('div');
  t.className = 'toast toast-' + (type || 'info');
  t.innerHTML = '<span>' + message + '</span><button onclick="this.parentElement.remove()">&times;</button>';
  c.appendChild(t);
  setTimeout(() => t.remove(), 4000);
}

async function checkAuth() {
  try {
    const data = await apiRequest('/auth/profile/');
    if (data?.data) {
      currentUserRole = data.data.role;
      const sidebar = document.querySelector('.sidebar');
      if (sidebar) {
        sidebar.querySelectorAll('[data-perm]').forEach(function(el) {
          const perm = el.getAttribute('data-perm');
          if (perm && !hasPermission(perm)) el.style.display = 'none';
        });
      }
      document.querySelectorAll('[data-perm]').forEach(function(el) {
        const perm = el.getAttribute('data-perm');
        if (perm && !hasPermission(perm)) el.style.display = 'none';
      });
      if (data.data.full_name) {
        const userNameEl = document.getElementById('user-name');
        if (userNameEl) userNameEl.textContent = data.data.full_name;
      }
    }
  } catch (e) {
    window.location.href = '/';
  }
}

function hasPermission(perm) {
  const perms = ROLE_PERMISSIONS[currentUserRole] || [];
  return perms.includes(perm);
}

function setupSidebar() {
  const toggle = document.getElementById('sidebar-toggle');
  const sidebar = document.querySelector('.sidebar');
  const overlay = document.getElementById('sidebar-overlay');
  if (toggle && sidebar) {
    toggle.addEventListener('click', function() {
      sidebar.classList.toggle('collapsed');
      overlay.classList.toggle('show');
    });
    document.querySelectorAll('.sidebar .nav-link').forEach(function(el) {
      el.addEventListener('click', function() {
        if (window.innerWidth < 768) {
          sidebar.classList.add('collapsed');
          overlay.classList.remove('show');
        }
      });
    });
  }
  overlay.addEventListener('click', function() {
    sidebar.classList.add('collapsed');
    overlay.classList.remove('show');
  });
  document.getElementById('btn-logout').addEventListener('click', function() {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    document.cookie = 'access_token=; path=/; max-age=0';
    window.location.href = '/';
  });
}

function setupSearch() {
  const input = document.getElementById('patient-search');
  if (!input) return;
  let timer = null;
  input.addEventListener('input', function() {
    clearTimeout(timer);
    timer = setTimeout(function() { loadPatientsTable(); }, 300);
  });
}

function setupTabs() {
  document.querySelectorAll('[data-tab]').forEach(function(el) {
    el.addEventListener('click', function() {
      document.querySelectorAll('[data-tab]').forEach(function(t) { t.classList.remove('active'); });
      document.querySelectorAll('.tab-pane').forEach(function(p) { p.classList.remove('active'); });
      el.classList.add('active');
      var target = document.getElementById('tab-' + el.getAttribute('data-tab'));
      if (target) target.classList.add('active');
    });
  });
}

function setupFileUpload() {
  var dropZone = document.getElementById('drop-zone');
  var fileInput = document.getElementById('file-input');
  if (!dropZone || !fileInput) return;
  dropZone.addEventListener('click', function() { fileInput.click(); });
  dropZone.addEventListener('dragover', function(e) { e.preventDefault(); dropZone.classList.add('drag-over'); });
  dropZone.addEventListener('dragleave', function() { dropZone.classList.remove('drag-over'); });
  dropZone.addEventListener('drop', function(e) { e.preventDefault(); dropZone.classList.remove('drag-over'); if (e.dataTransfer.files.length) { fileInput.files = e.dataTransfer.files; uploadFile(e.dataTransfer.files[0]); } });
  fileInput.addEventListener('change', function() { if (this.files.length) uploadFile(this.files[0]); });
}

async function uploadFile(file) {
  var formData = new FormData();
  formData.append('file', file);
  formData.append('name', file.name);
  formData.append('source_type', file.name.endsWith('.csv') ? 'csv' : 'excel');
  try {
    var res = await fetch(API_BASE + '/etl/sources/upload/', { method: 'POST', headers: { 'Authorization': 'Bearer ' + getToken() }, body: formData });
    var data = await res.json();
    if (data.success) {
      showToast('Archivo subido exitosamente', 'success');
      if (typeof loadETLHistory === 'function') loadETLHistory();
    } else {
      showToast(data.error || 'Error al subir archivo', 'error');
    }
  } catch (e) {
    showToast('Error de conexión', 'error');
  }
}

async function loadPatientsTable() {
  var tbody = document.getElementById('patients-table-body');
  if (!tbody) return;
  tbody.innerHTML = '<tr><td colspan="11" class="text-center text-muted py-4"><span class="loading-spinner"></span> Cargando...</td></tr>';
  try {
    var search = document.getElementById('patient-search')?.value || '';
    var risk = document.getElementById('filter-risk')?.value || '';
    var params = new URLSearchParams();
    if (search) params.set('search', search);
    if (risk) params.set('risk_category', risk);
    params.set('page', '1');
    params.set('page_size', '20');
    var data = await apiRequest('/patients/?' + params.toString());
    var patients = data?.results || [];
    tbody.innerHTML = '';
    if (patients.length === 0) {
      tbody.innerHTML = '<tr><td colspan="11" class="text-center text-muted py-4">No se encontraron pacientes</td></tr>';
      return;
    }
    patients.forEach(function(p) {
      var riskLabel = { critical: 'Crítico', high: 'Alto', medium: 'Medio', low: 'Bajo' }[p.risk_category] || p.risk_category;
      var riskClass = { critical: 'risk-critical', high: 'risk-high', medium: 'risk-medium', low: 'risk-low' }[p.risk_category] || '';
      var tr = document.createElement('tr');
      tr.innerHTML = '<td class="font-mono">' + (p.patient_id || '—') + '</td><td><a href="/patients/' + p.id + '/">' + escapeHtml(p.first_name || '') + ' ' + escapeHtml(p.last_name || '') + '</a></td><td>' + (p.age || '—') + '</td><td>' + (p.gender || '—') + '</td><td>' + (p.bmi || '—') + '</td><td><span class="risk-badge ' + riskClass + '">' + riskLabel + '</span></td><td>' + escapeHtml(p.diagnosis || '—') + '</td><td>' + (p.systolic_bp || '—') + '</td><td>' + (p.glucose || '—') + '</td><td>' + (p.smoking ? 'Sí' : 'No') + '</td><td class="text-muted text-xs">' + (p.created_at ? new Date(p.created_at).toLocaleDateString() : '—') + '</td>';
      tbody.appendChild(tr);
    });
  } catch (e) {
    tbody.innerHTML = '<tr><td colspan="11" class="text-center text-danger py-4">Error al cargar pacientes</td></tr>';
  }
}

async function loadETLHistory() {
  var tbody = document.getElementById('etl-table-body');
  if (!tbody) return;
  try {
    var data = await apiRequest('/etl/executions/history/');
    var execs = data?.results || [];
    tbody.innerHTML = '';
    if (execs.length === 0) {
      tbody.innerHTML = '<tr><td colspan="9" class="text-center text-muted py-4">Sin ejecuciones</td></tr>';
      return;
    }
    var statusLabels = { completed: 'Completado', failed: 'Fallido', running: 'Ejecutando', pending: 'Pendiente' };
    var statusClass = { completed: 'badge-success', failed: 'badge-danger', running: 'badge-info', pending: 'badge-warning' };
    execs.forEach(function(e) {
      var tr = document.createElement('tr');
      tr.innerHTML = '<td class="font-mono">#' + (e.id || '—') + '</td><td>' + escapeHtml(e.source_name || '—') + '</td><td><span class="badge ' + (statusClass[e.status] || 'badge-secondary') + '">' + (statusLabels[e.status] || e.status) + '</span></td><td>' + (e.records_read || '0') + '</td><td>' + (e.records_loaded || '0') + '</td><td>' + (e.quality_score != null ? e.quality_score + '%' : '—') + '</td><td>' + (e.duration_seconds != null ? e.duration_seconds.toFixed(1) + 's' : '—') + '</td><td>' + escapeHtml(e.executed_by_name || '—') + '</td><td class="text-xs text-muted">' + (e.created_at ? new Date(e.created_at).toLocaleString() : '—') + '</td>';
      tbody.appendChild(tr);
    });
  } catch (e) {
    tbody.innerHTML = '<tr><td colspan="9" class="text-center text-danger py-4">Error al cargar historial</td></tr>';
  }
}

function escapeHtml(str) {
  var div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}

function setupPredictionForm() {
  var form = document.getElementById('predict-form');
  if (!form) return;
  form.addEventListener('submit', async function(e) {
    e.preventDefault();
    var resultEl = document.getElementById('prediction-result');
    if (!resultEl) return;
    resultEl.innerHTML = '<span class="loading-spinner"></span> Prediciendo...';
    var data = {};
    new FormData(form).forEach(function(v, k) { data[k] = v; });
    data.smoking = data.smoking === 'true';
    data.family_history = data.family_history === 'true';
    data.physical_activity = data.physical_activity === 'true';
    data.alcohol_consumption = data.alcohol_consumption === 'true';
    try {
      var res = await apiRequest('/ml/models/predict/', { method: 'POST', body: JSON.stringify(data) });
      if (res?.success && res?.data) {
        var d = res.data;
        var riskClass = { critical: 'risk-critical', high: 'risk-high', medium: 'risk-medium', low: 'risk-low' }[d.risk_category] || '';
        var riskLabel = { critical: 'Crítico', high: 'Alto', medium: 'Medio', low: 'Bajo' }[d.risk_category] || d.risk_category;
        resultEl.innerHTML = '<div class="mt-3 p-3 rounded" style="background:var(--light);border:1px solid var(--border);">' +
          '<strong>Resultado de Predicción:</strong><br>' +
          'Riesgo: <span class="risk-badge ' + riskClass + '">' + riskLabel + '</span><br>' +
          'Probabilidad: ' + (d.probability != null ? (d.probability * 100).toFixed(1) + '%' : '—') +
          '</div>';
      } else {
        resultEl.innerHTML = '<div class="mt-3 text-danger">' + (res?.error || 'Error en predicción') + '</div>';
      }
    } catch (e) {
      resultEl.innerHTML = '<div class="mt-3 text-danger">Error de conexión</div>';
    }
  });
}

async function loadMLComparison() {
  var el = document.getElementById('ml-comparison');
  if (!el) return;
  try {
    var data = await apiRequest('/ml/models/comparison/');
    var models = data?.data?.models || data?.models || [];
    if (models.length === 0) {
      el.innerHTML = '<p class="text-muted text-center py-4">Sin modelos entrenados. Haz clic en "Entrenar Modelos" para comenzar.</p>';
      return;
    }
    var html = '<div class="table-container"><table class="table-custom"><thead><tr><th>Modelo</th><th>Precisión</th><th>F1-Score</th><th>Recall</th><th>Precisión</th><th>AUC-ROC</th></tr></thead><tbody>';
    models.forEach(function(m) {
      html += '<tr><td class="fw-600">' + escapeHtml(m.model_name || m.name || '—') + '</td>' +
        '<td>' + (m.accuracy != null ? (m.accuracy * 100).toFixed(1) + '%' : '—') + '</td>' +
        '<td>' + (m.f1_score != null ? m.f1_score.toFixed(4) : '—') + '</td>' +
        '<td>' + (m.recall != null ? m.recall.toFixed(4) : '—') + '</td>' +
        '<td>' + (m.precision != null ? m.precision.toFixed(4) : '—') + '</td>' +
        '<td>' + (m.auc_roc != null ? m.auc_roc.toFixed(4) : '—') + '</td></tr>';
    });
    html += '</tbody></table></div>';
    el.innerHTML = html;
  } catch (e) {
    el.innerHTML = '<p class="text-danger">Error al cargar modelos</p>';
  }
}

async function loadAlerts() {
  var el = document.getElementById('alerts-list');
  if (!el) return;
  try {
    var data = await apiRequest('/dashboard/alerts/');
    var alerts = data?.data;
    if (!alerts) { el.innerHTML = '<p class="text-muted">Sin datos</p>'; return; }
    var countEl = document.getElementById('alert-count');
    if (countEl) countEl.textContent = alerts.total || 0;
    var html = '<div class="mb-2"><span class="badge bg-danger">Críticas: ' + (alerts.critical || 0) + '</span> <span class="badge bg-warning">Advertencias: ' + (alerts.warnings || 0) + '</span> <span class="badge bg-info">Info: ' + (alerts.info || 0) + '</span></div>';
    (alerts.recent || []).forEach(function(a) {
      html += '<div class="alert-item alert-' + a.severity + '"><div class="alert-text"><strong>' + escapeHtml(a.patient || '') + '</strong><br><small>' + escapeHtml(a.description || '') + '</small></div><div class="alert-time">' + (a.created_at ? new Date(a.created_at).toLocaleDateString() : '') + '</div></div>';
    });
    el.innerHTML = html;
  } catch (e) {
    el.innerHTML = '<p class="text-danger">Error al cargar alertas</p>';
  }
}
