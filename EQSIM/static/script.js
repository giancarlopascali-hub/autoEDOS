async function fetchStatus() {
    try {
        const response = await fetch('/api/status');
        const data = await response.json();
        
        updateUI(data);
    } catch (error) {
        console.error('Error fetching status:', error);
    }
}

async function fetchConfig() {
    try {
        const response = await fetch('/api/config');
        const data = await response.json();
        
        document.getElementById('folder_a').value = data.folder_a || '';
        document.getElementById('folder_b').value = data.folder_b || '';
        document.getElementById('folder_c').value = data.folder_c || '';
        document.getElementById('folder_d').value = data.folder_d || '';
        document.getElementById('tag').value = data.tag || 'USED_';
        document.getElementById('delay').value = data.delay || 1.0;
        
        updateStatusDisplay(data.active);
    } catch (error) {
        console.error('Error fetching config:', error);
    }
}

function updateUI(data) {
    const logsContainer = document.getElementById('logs');
    const wasAtBottom = logsContainer.scrollHeight - logsContainer.scrollTop <= logsContainer.clientHeight + 10;
    
    logsContainer.innerHTML = data.logs.map(log => {
        const parts = log.split('] ');
        const time = parts[0].replace('[', '');
        const msg = parts[1];
        return `<div class="log-entry"><span>${time}</span> ${msg}</div>`;
    }).join('');

    if (wasAtBottom) {
        logsContainer.scrollTop = logsContainer.scrollHeight;
    }

    updateStatusDisplay(data.active);
    document.getElementById('last-updated').textContent = 'Last update: ' + new Date().toLocaleTimeString();
}

function updateStatusDisplay(isActive) {
    const dot = document.getElementById('status-dot');
    const text = document.getElementById('status-text');
    const btn = document.getElementById('toggle-btn');

    if (isActive) {
        dot.classList.add('active');
        text.textContent = 'ACTIVATED';
        text.style.color = 'var(--success-color)';
        btn.textContent = 'Deactivate';
        btn.className = 'btn-toggle active';
    } else {
        dot.classList.remove('active');
        text.textContent = 'DEACTIVATED';
        text.style.color = 'var(--text-secondary)';
        btn.textContent = 'Activate';
        btn.className = 'btn-toggle inactive';
    }
}

async function toggleApp() {
    try {
        const dot = document.getElementById('status-dot');
        const isActive = dot.classList.contains('active');
        
        const response = await fetch('/api/toggle', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ active: !isActive })
        });
        const data = await response.json();
        updateStatusDisplay(data.active);
    } catch (error) {
        console.error('Error toggling app:', error);
    }
}

async function saveConfig() {
    const config = {
        folder_a: document.getElementById('folder_a').value,
        folder_b: document.getElementById('folder_b').value,
        folder_c: document.getElementById('folder_c').value,
        folder_d: document.getElementById('folder_d').value,
        tag: document.getElementById('tag').value,
        delay: parseFloat(document.getElementById('delay').value)
    };

    try {
        const response = await fetch('/api/config', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(config)
        });
        const data = await response.json();
        if (data.status === 'success') {
            alert('Configuration saved successfully!');
        }
    } catch (error) {
        console.error('Error saving config:', error);
        alert('Failed to save configuration.');
    }
}

async function browseFolder(inputId) {
    try {
        const response = await fetch('/api/browse', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        const data = await response.json();
        if (data.path) {
            document.getElementById(inputId).value = data.path;
        }
    } catch (error) {
        console.error('Error browsing folder:', error);
    }
}

// Initial load
fetchConfig();
// Poll for updates
setInterval(fetchStatus, 1000);
