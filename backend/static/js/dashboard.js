const API_BASE = '/api/v1';

function getToken() {
    return localStorage.getItem('access_token') || sessionStorage.getItem('access_token');
}

async function apiRequest(endpoint, options = {}) {
    const token = getToken();
    const headers = {
        'Content-Type': 'application/json',
        ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
        ...options.headers,
    };
    try {
        const response = await fetch(`${API_BASE}${endpoint}`, { ...options, headers });
        if (response.status === 401) {
            const refresh = localStorage.getItem('refresh_token');
            if (refresh) {
                const refreshRes = await fetch(`${API_BASE}/auth/token/refresh/`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ refresh }),
                });
                if (refreshRes.ok) {
                    const data = await refreshRes.json();
                    localStorage.setItem('access_token', data.access);
                    headers['Authorization'] = `Bearer ${data.access}`;
                    const retryRes = await fetch(`${API_BASE}${endpoint}`, { ...options, headers });
                    return retryRes.json();
                }
            }
            window.location.href = '/login.html';
            return null;
        }
        return response.json();
    } catch (error) {
        console.error('API Error:', error);
        showToast('Error de conexión', 'error');
        return null;
    }
}

function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    if (!container) return;
    const icons = { success: 'bi-check-circle-fill', error: 'bi-x-circle-fill', warning: 'bi-exclamation-triangle-fill', info: 'bi-info-circle-fill' };
    const toast = document.createElement('div');
    toast.className = `toast-item ${type}`;
    toast.innerHTML = `<i class="bi ${icons[type] || 'bi-info-circle-fill'}"></i><span>${message}</span>`;
    container.appendChild(toast);
    setTimeout(() => { toast.style.opacity = '0'; setTimeout(() => toast.remove(), 300); }, 3500);
}

function formatNumber(num) { return num?.toLocaleString() || '0'; }
function formatDecimal(num, d = 2) { return num ? parseFloat(num).toFixed(d) : '0'; }

function getRiskBadge(risk) {
    const labels = { low: 'Bajo', medium: 'Medio', high: 'Alto', critical: 'Crítico' };
    return `<span class="risk-badge risk-${risk}">${labels[risk] || risk}</span>`;
}

function getStatusDot(status) {
    const labels = { completed: 'Completado', failed: 'Fallido', processing: 'Procesando', pending: 'Pendiente' };
    return `<span class="status-dot ${status}"></span>${labels[status] || status}`;
}

var currentUserRole = null;

var ROLE_PERMISSIONS = {
    admin: [
        'dashboard', 'patients', 'patients_manage', 'patients_delete',
        'etl', 'etl_execute', 'etl_delete',
        'analytics', 'analytics_export',
        'ml', 'ml_train', 'ml_predict',
        'reports', 'reports_export',
        'users_manage', 'users_delete',
        'settings', 'settings_global',
        'audit_view',
    ],
    analyst: [
        'dashboard',
        'patients',
        'etl', 'etl_execute',
        'analytics', 'analytics_export',
        'ml', 'ml_train', 'ml_predict',
        'reports', 'reports_export',
    ],
    doctor: [
        'dashboard',
        'patients',
        'analytics',
        'reports',
        'settings',
    ],
};

async function checkAuth() {
    const token = getToken();
    if (!token) {
        window.location.href = '/login.html';
        return;
    }
    try {
        const user = await apiRequest('/auth/profile/');
        if (user && user.success !== false) {
            const data = user.data || user;
            currentUserRole = data.role;
            document.getElementById('user-name').textContent = data.full_name || data.email;
            const roleLabels = { admin: 'Administrador', doctor: 'Médico', analyst: 'Analista' };
            document.getElementById('user-role').textContent = roleLabels[data.role] || data.role;
            document.getElementById('user-avatar').textContent = (data.full_name || data.email)[0].toUpperCase();
            applyRoleBasedUI(data.role);
        }
    } catch (e) {
        console.error('Auth check failed:', e);
    }
}

function applyRoleBasedUI(role) {
    const perms = ROLE_PERMISSIONS[role] || [];
    document.querySelectorAll('[data-perm]').forEach(el => {
        const required = el.dataset.perm.split(' ');
        const hasAny = required.some(p => perms.includes(p));
        el.style.display = hasAny ? '' : 'none';
    });
}

function hasRole(allowedRoles) {
    return allowedRoles.includes(currentUserRole);
}

function logout() {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    sessionStorage.removeItem('access_token');
    window.location.href = '/login.html';
}

async function loadKPIs() {
    const data = await apiRequest('/dashboard/kpi/');
    if (!data?.data) return;
    const k = data.data;
    const elements = {
        'kpi-total-patients': k.total_patients,
        'kpi-critical': k.critical_patients,
        'kpi-hypertensive': k.hypertensive,
        'kpi-diabetic': k.diabetic,
        'kpi-smokers': k.smokers,
        'kpi-avg-risk': formatDecimal(k.avg_risk),
        'kpi-etl-executions': k.etl_executions != null ? k.etl_executions : '—',
        'kpi-etl-records': k.etl_records_processed != null ? formatNumber(k.etl_records_processed) : '—',
        'kpi-model-accuracy': k.model_accuracy != null ? `${formatDecimal(k.model_accuracy * 100)}%` : '—',
    };
    Object.entries(elements).forEach(([id, val]) => {
        const el = document.getElementById(id);
        if (el) el.textContent = val;
    });
}

async function loadCharts() {
    const data = await apiRequest('/dashboard/charts/');
    if (!data?.data) return;
    const d = data.data;

    const riskCtx = document.getElementById('chart-risk');
    if (riskCtx && d.risk_distribution?.length) {
        const colors = { low: '#10b981', medium: '#f59e0b', high: '#f97316', critical: '#ef4444' };
        const labels = { low: 'Bajo', medium: 'Medio', high: 'Alto', critical: 'Crítico' };
        new Chart(riskCtx, {
            type: 'doughnut',
            data: {
                labels: d.risk_distribution.map(r => labels[r.risk_category] || r.risk_category),
                datasets: [{
                    data: d.risk_distribution.map(r => r.count),
                    backgroundColor: d.risk_distribution.map(r => colors[r.risk_category] || '#94a3b8'),
                    borderWidth: 0,
                }]
            },
            options: { responsive: true, plugins: { legend: { position: 'bottom', labels: { padding: 15, usePointStyle: true } } } }
        });
    }

    const genderCtx = document.getElementById('chart-gender');
    if (genderCtx && d.gender_distribution?.length) {
        const genderLabels = { M: 'Masculino', F: 'Femenino', O: 'Otro' };
        new Chart(genderCtx, {
            type: 'pie',
            data: {
                labels: d.gender_distribution.map(g => genderLabels[g.gender] || g.gender),
                datasets: [{
                    data: d.gender_distribution.map(g => g.count),
                    backgroundColor: ['#3b82f6', '#ec4899', '#94a3b8'],
                    borderWidth: 0,
                }]
            },
            options: { responsive: true, plugins: { legend: { position: 'bottom' } } }
        });
    }

    const ageCtx = document.getElementById('chart-age');
    if (ageCtx && d.age_distribution?.length) {
        new Chart(ageCtx, {
            type: 'bar',
            data: {
                labels: d.age_distribution.map(a => a.group),
                datasets: [{
                    label: 'Pacientes',
                    data: d.age_distribution.map(a => a.count),
                    backgroundColor: '#3b82f6',
                    borderRadius: 4,
                }]
            },
            options: {
                responsive: true,
                scales: { y: { beginAtZero: true, grid: { display: false } }, x: { grid: { display: false } } },
                plugins: { legend: { display: false } }
            }
        });
    }

    const bmiCtx = document.getElementById('chart-bmi');
    if (bmiCtx && d.bmi_distribution?.length) {
        const bmiLabels = { underweight: 'Bajo peso', normal: 'Normal', overweight: 'Sobrepeso', obese_i: 'Obesidad I', obese_ii: 'Obesidad II', obese_iii: 'Obesidad III' };
        const bmiColors = ['#93c5fd', '#3b82f6', '#f59e0b', '#f97316', '#ef4444', '#7c3aed'];
        new Chart(bmiCtx, {
            type: 'bar',
            data: {
                labels: d.bmi_distribution.map(b => bmiLabels[b.bmi_category] || b.bmi_category),
                datasets: [{
                    label: 'Pacientes',
                    data: d.bmi_distribution.map(b => b.count),
                    backgroundColor: bmiColors,
                    borderRadius: 4,
                }]
            },
            options: {
                responsive: true,
                indexAxis: 'y',
                scales: { x: { beginAtZero: true, grid: { display: false } }, y: { grid: { display: false } } },
                plugins: { legend: { display: false } }
            }
        });
    }

    const diagCtx = document.getElementById('chart-diagnosis');
    if (diagCtx && d.diagnosis_distribution?.length) {
        const colors = ['#3b82f6', '#10b981', '#f59e0b', '#f97316', '#ef4444', '#8b5cf6', '#06b6d4', '#ec4899', '#84cc16', '#6366f1'];
        new Chart(diagCtx, {
            type: 'doughnut',
            data: {
                labels: d.diagnosis_distribution.map(dd => dd.diagnosis),
                datasets: [{
                    data: d.diagnosis_distribution.map(dd => dd.count),
                    backgroundColor: colors.slice(0, d.diagnosis_distribution.length),
                    borderWidth: 0,
                }]
            },
            options: {
                responsive: true,
                plugins: { legend: { position: 'bottom', labels: { padding: 12, font: { size: 10 } } } }
            }
        });
    }
}

async function loadPatientsTable(page = 1) {
    const tbody = document.getElementById('patients-table-body');
    if (!tbody) return;
    const search = document.getElementById('patient-search')?.value || '';
    const riskFilter = document.getElementById('filter-risk')?.value || '';
    const genderFilter = document.getElementById('filter-gender')?.value || '';
    const pageSize = 25;

    let url = `/patients/?page=${page}&page_size=${pageSize}`;
    if (search) url += `&search=${encodeURIComponent(search)}`;
    if (riskFilter) url += `&risk_category=${riskFilter}`;
    if (genderFilter) url += `&gender=${genderFilter}`;

    const data = await apiRequest(url);
    if (!data?.results) return;

    tbody.innerHTML = data.results.map(p => `
        <tr>
            <td>${p.patient_id}</td>
            <td>${p.full_name}</td>
            <td>${p.age}</td>
            <td>${{M:'M',F:'F',O:'O'}[p.gender] || '-'}</td>
            <td>${formatDecimal(p.bmi)}</td>
            <td>${getRiskBadge(p.risk_category)}</td>
            <td>${p.diagnosis_code || '-'}</td>
            <td>${p.glucose ? formatDecimal(p.glucose) : '-'}</td>
            <td>${p.systolic_bp || '-'}</td>
            <td>${p.smoking ? 'Sí' : 'No'}</td>
            <td>${new Date(p.created_at).toLocaleDateString()}</td>
        </tr>
    `).join('');

    const pagination = document.getElementById('patients-pagination');
    if (pagination) {
        const totalPages = Math.ceil(data.count / pageSize) || 1;
        const current = page;
        const start = (current - 1) * pageSize + 1;
        const end = Math.min(current * pageSize, data.count);
        let html = `<div class="info">Mostrando ${start}–${end} de ${data.count}</div><div class="pages">`;
        for (let i = Math.max(1, current - 2); i <= Math.min(totalPages, current + 2); i++) {
            html += `<button class="${i === current ? 'active' : ''}" onclick="loadPatientsTable(${i})">${i}</button>`;
        }
        html += '</div>';
        pagination.innerHTML = html;
    }
}

async function loadETLHistory() {
    const tbody = document.getElementById('etl-table-body');
    if (!tbody) return;
    const data = await apiRequest('/etl/executions/');
    if (!data?.results) return;

    tbody.innerHTML = data.results.map(e => `
        <tr>
            <td>#${e.id}</td>
            <td>${e.source_name}</td>
            <td>${getStatusDot(e.status)}</td>
            <td>${formatNumber(e.records_loaded)}</td>
            <td>${e.quality_score ? formatDecimal(e.quality_score) : '-'}</td>
            <td>${e.duration_formatted}</td>
            <td>${e.executed_by_name}</td>
            <td>${new Date(e.created_at).toLocaleString()}</td>
        </tr>
    `).join('');
}

async function loadMLComparison() {
    const container = document.getElementById('ml-comparison');
    if (!container) return;
    const data = await apiRequest('/ml/models/comparison/');
    if (!data?.results) return;

    container.innerHTML = data.results.map(m => `
        <div class="card mb-3 ml-card">
            <div class="card-body">
                <div class="d-flex align-center justify-between">
                    <div>
                        <h6 class="mb-1">${m.model}</h6>
                        <small class="text-muted">v${m.version} ${m.is_active ? '<span class="risk-badge risk-low">Activo</span>' : ''}</small>
                    </div>
                    <span class="risk-badge ${m.is_active ? 'risk-low' : 'risk-medium'}">${formatDecimal(m.accuracy * 100)}%</span>
                </div>
                <div class="row mt-3 g-2">
                    <div class="col-6 col-md-3"><small class="text-muted">Precisión</small><br><strong>${formatDecimal(m.precision * 100)}%</strong></div>
                    <div class="col-6 col-md-3"><small class="text-muted">Recall</small><br><strong>${formatDecimal(m.recall * 100)}%</strong></div>
                    <div class="col-6 col-md-3"><small class="text-muted">F1-Score</small><br><strong>${formatDecimal(m.f1_score * 100)}%</strong></div>
                    <div class="col-6 col-md-3"><small class="text-muted">ROC-AUC</small><br><strong>${m.roc_auc ? formatDecimal(m.roc_auc * 100) + '%' : 'N/A'}</strong></div>
                </div>
            </div>
        </div>
    `).join('');
}

async function loadAlerts() {
    const container = document.getElementById('alerts-list');
    if (!container) return;
    const data = await apiRequest('/dashboard/alerts/');
    if (!data?.data) return;

    document.getElementById('alert-count').textContent = data.data.total;

    const severityIcons = { critical: 'bi-exclamation-triangle-fill', warning: 'bi-exclamation-circle-fill', info: 'bi-info-circle-fill' };
    const severityColors = { critical: 'var(--danger)', warning: 'var(--warning)', info: 'var(--info)' };
    container.innerHTML = data.data.recent.map(a => `
        <div class="alert-item alert-${a.severity}">
            <div class="alert-icon"><i class="bi ${severityIcons[a.severity] || 'bi-info-circle-fill'}" style="color:${severityColors[a.severity] || 'var(--text-secondary)'}"></i></div>
            <div class="alert-content">
                <div class="alert-title">${a.alert_type} — ${a.patient}</div>
                <div class="alert-desc">${a.description}</div>
                <div class="alert-time">${new Date(a.created_at).toLocaleString()}</div>
            </div>
        </div>
    `).join('');
}

async function executeETL(sourceId) {
    const btn = document.querySelector(`[data-source-id="${sourceId}"]`);
    if (btn) { btn.disabled = true; btn.innerHTML = '<span class="loading-spinner"></span>'; }
    const result = await apiRequest('/etl/executions/execute/', {
        method: 'POST',
        body: JSON.stringify({ source_id: sourceId, run_async: true }),
    });
    if (result?.success) {
        showToast('ETL iniciado exitosamente', 'success');
        setTimeout(() => { loadETLHistory(); }, 2000);
    } else {
        showToast(result?.error || 'Error al ejecutar ETL', 'error');
    }
    if (btn) { btn.disabled = false; btn.innerHTML = '<i class="bi bi-play-fill"></i> Ejecutar'; }
}

function setupPredictionForm() {
    const form = document.getElementById('predict-form');
    if (!form) return;

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const data = Object.fromEntries(new FormData(form));
        for (const [key, val] of Object.entries(data)) {
            if (['smoking', 'family_history', 'physical_activity', 'alcohol_consumption'].includes(key)) {
                data[key] = val === 'on' || val === 'true';
            }
        }

        const btn = form.querySelector('button[type="submit"]');
        btn.disabled = true;
        btn.innerHTML = '<span class="loading-spinner"></span>';

        const result = await apiRequest('/ml/models/predict/', {
            method: 'POST',
            body: JSON.stringify(data),
        });

        btn.disabled = false;
        btn.innerHTML = '<i class="bi bi-magic"></i> Predecir Riesgo';

        const resultDiv = document.getElementById('prediction-result');
        if (result?.success) {
            const riskLabels = { low: 'Bajo', medium: 'Medio', high: 'Alto', critical: 'Crítico' };
            resultDiv.innerHTML = `
                <div class="card mt-3 prediction-result">
                    <div class="card-body text-center">
                        <h5 style="font-weight:600;letter-spacing:-.3px;">Resultado de Predicción</h5>
                        <div class="my-3">${getRiskBadge(result.predicted_risk)}</div>
                        <h2 style="font-weight:800;letter-spacing:-.5px;" class="risk-${result.predicted_risk}">${riskLabels[result.predicted_risk]}</h2>
                        <div class="mt-3">
                            <small class="text-muted">Probabilidades:</small>
                            ${Object.entries(result.probabilities || {}).map(([k, v]) =>
                                `<div class="d-flex align-center justify-between mt-1">
                                    <small>${riskLabels[k] || k}</small>
                                    <div class="flex-1 mx-2" style="height:6px;background:#e2e8f0;border-radius:3px;">
                                        <div style="width:${(v*100).toFixed(1)}%;height:100%;background:var(--risk-${k});border-radius:3px;"></div>
                                    </div>
                                    <small>${(v*100).toFixed(1)}%</small>
                                </div>`
                            ).join('')}
                        </div>
                    </div>
                </div>
            `;
        } else {
            resultDiv.innerHTML = `<div class="alert alert-danger mt-3">${result?.error || 'Error en la predicción'}</div>`;
        }
    });
}

function setupFileUpload() {
    const dropZone = document.getElementById('drop-zone');
    const fileInput = document.getElementById('file-input');
    if (!dropZone || !fileInput) return;

    dropZone.addEventListener('click', () => fileInput.click());

    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.classList.add('dragover');
    });

    dropZone.addEventListener('dragleave', () => {
        dropZone.classList.remove('dragover');
    });

    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.classList.remove('dragover');
        if (e.dataTransfer.files.length) {
            fileInput.files = e.dataTransfer.files;
            uploadFile(e.dataTransfer.files[0]);
        }
    });

    fileInput.addEventListener('change', () => {
        if (fileInput.files.length) uploadFile(fileInput.files[0]);
    });
}

async function uploadFile(file) {
    const validTypes = ['.xlsx', '.xls', '.csv'];
    const ext = '.' + file.name.split('.').pop().toLowerCase();
    if (!validTypes.includes(ext)) {
        showToast('Formato no válido. Use .xlsx o .csv', 'error');
        return;
    }

    const formData = new FormData();
    formData.append('name', file.name);
    formData.append('source_type', ext === '.csv' ? 'csv' : 'excel');
    formData.append('file', file);

    const token = getToken();
    let result, data;
    try {
        result = await fetch(`${API_BASE}/etl/sources/`, {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${token}` },
            body: formData,
        });
        data = await result.json();
    } catch (e) {
        let msg = 'Error de conexión al cargar archivo';
        if (result && !result.ok) {
            msg = `Error del servidor (${result.status})`;
        }
        showToast(msg, 'error');
        return;
    }

    if (!result.ok) {
        showToast(data?.error || data?.detail || `Error del servidor (${result.status})`, 'error');
        return;
    }

    if (data?.id || data?.success) {
        showToast('Archivo cargado exitosamente. Iniciando ETL...', 'success');
        const execResult = await apiRequest('/etl/executions/execute/', {
            method: 'POST',
            body: JSON.stringify({ source_id: data.id || data.data?.id, run_async: true }),
        });
        if (execResult?.success) {
            showToast('ETL iniciado', 'info');
            setTimeout(() => loadETLHistory(), 2000);
        } else {
            showToast(execResult?.error || 'Error al iniciar ETL', 'error');
        }
    } else {
        showToast(data?.error || 'Error al cargar archivo', 'error');
    }
}

function setupSidebar() {
    const toggleBtn = document.getElementById('sidebar-toggle');
    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('sidebar-overlay');
    if (!toggleBtn || !sidebar) return;

    toggleBtn.addEventListener('click', () => {
        if (window.innerWidth <= 991) {
            sidebar.classList.toggle('show');
            if (overlay) overlay.classList.toggle('show');
        } else {
            sidebar.classList.toggle('collapsed');
        }
    });

    if (overlay) {
        overlay.addEventListener('click', () => {
            sidebar.classList.remove('show');
            overlay.classList.remove('show');
        });
    }

    const path = window.location.pathname;
    document.querySelectorAll('.nav-item').forEach(item => {
        const href = item.getAttribute('href');
        if (href && (path === href || path.startsWith(href))) {
            item.classList.add('active');
        }
    });

    const logoutBtn = document.getElementById('btn-logout');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', logout);
    }
}

function setupTabs() {
    document.querySelectorAll('.tab-item[data-tab]').forEach(tab => {
        tab.addEventListener('click', () => {
            const parent = tab.parentElement;
            parent.querySelectorAll('.tab-item').forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            const target = document.getElementById(tab.dataset.tab);
            if (target) {
                parent.parentElement.querySelectorAll('.tab-content').forEach(c => c.style.display = 'none');
                target.style.display = 'block';
            }
        });
    });
}

function setupSearch() {
    const searchInput = document.getElementById('patient-search');
    if (searchInput) {
        let debounce;
        searchInput.addEventListener('input', () => {
            clearTimeout(debounce);
            debounce = setTimeout(() => loadPatientsTable(), 300);
        });
    }
}

document.addEventListener('DOMContentLoaded', async () => {
    setupSidebar();
    setupTabs();
    setupSearch();
    setupFileUpload();
    setupPredictionForm();

    await checkAuth();

    const path = window.location.pathname;

    if (path === '/' || path === '') {
        const tasks = [loadKPIs(), loadCharts(), loadPatientsTable(), loadAlerts()];
        if (ROLE_PERMISSIONS[currentUserRole]?.includes('etl')) tasks.push(loadETLHistory());
        if (ROLE_PERMISSIONS[currentUserRole]?.includes('ml')) tasks.push(loadMLComparison());
        await Promise.all(tasks);
    }
});

window.loadPatientsTable = loadPatientsTable;
window.executeETL = executeETL;
