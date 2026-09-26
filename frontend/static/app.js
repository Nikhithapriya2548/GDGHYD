let currentCampaignId = null;

// Utility to show panels
function showPanel(id) {
    document.getElementById(id).style.display = 'block';
}

// 1. Create Campaign
document.getElementById('campaign-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const btn = e.target.querySelector('button');
    btn.textContent = 'Generating...';
    btn.disabled = true;

    try {
        const res = await fetch('/api/campaign/create', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                product_name: document.getElementById('product-name').value,
                product_desc: document.getElementById('product-desc').value
            })
        });
        const data = await res.json();
        currentCampaignId = data.campaign_id;
        
        // Populate Creative Director Panel
        document.getElementById('creative-plan-content').textContent = JSON.stringify(data.creative_plan, null, 2);
        showPanel('panel-creative-director');
        showPanel('panel-theme');
    } catch (err) {
        console.error(err);
        alert('Error creating campaign');
    } finally {
        btn.textContent = 'Generate Creative Plan';
        btn.disabled = false;
    }
});

// 2. Set Theme
document.getElementById('btn-set-theme').addEventListener('click', async (e) => {
    if (!currentCampaignId) return;
    const btn = e.target;
    btn.disabled = true;
    
    try {
        const res = await fetch(`/api/campaign/${currentCampaignId}/theme`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ theme: document.getElementById('theme-select').value })
        });
        const data = await res.json();
        document.getElementById('theme-status').textContent = `Theme set: ${data.theme}`;
        showPanel('panel-upload');
    } catch (err) {
        console.error(err);
    } finally {
        btn.disabled = false;
    }
});

// 3. Upload Asset
document.getElementById('btn-upload').addEventListener('click', async (e) => {
    if (!currentCampaignId) return;
    const fileInput = document.getElementById('asset-upload');
    if (!fileInput.files[0]) {
        document.getElementById('upload-status').textContent = 'Skipped upload.';
        showPanel('panel-storyboard');
        return;
    }
    
    const btn = e.target;
    btn.disabled = true;
    
    const formData = new FormData();
    formData.append('file', fileInput.files[0]);

    try {
        const res = await fetch(`/api/campaign/${currentCampaignId}/upload`, {
            method: 'POST',
            body: formData
        });
        const data = await res.json();
        document.getElementById('upload-status').textContent = `Uploaded: ${data.asset_path}`;
        showPanel('panel-storyboard');
    } catch (err) {
        console.error(err);
    } finally {
        btn.disabled = false;
    }
});

document.getElementById('btn-skip-upload').addEventListener('click', () => {
    if (!currentCampaignId) return;
    document.getElementById('upload-status').textContent = 'Skipped upload.';
    showPanel('panel-storyboard');
});

// 4. Generate Storyboard
document.getElementById('btn-generate-storyboard').addEventListener('click', async (e) => {
    if (!currentCampaignId) return;
    const btn = e.target;
    btn.disabled = true;
    btn.textContent = 'Generating...';

    try {
        const res = await fetch(`/api/campaign/${currentCampaignId}/storyboard`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({})
        });
        const data = await res.json();
        
        const gallery = document.getElementById('storyboard-gallery');
        gallery.innerHTML = '';
        data.scenes.forEach(scene => {
            const el = document.createElement('div');
            el.className = 'scene-card';
            el.innerHTML = `
                <img src="${scene.image_url}" alt="Scene ${scene.scene_id}">
                <p>Scene ${scene.scene_id}: ${scene.prompt}</p>
            `;
            gallery.appendChild(el);
        });
        showPanel('panel-video');
    } catch (err) {
        console.error(err);
    } finally {
        btn.disabled = false;
        btn.textContent = 'Generate Storyboard';
    }
});

// 5. Video Pipeline
document.getElementById('btn-start-video').addEventListener('click', async (e) => {
    if (!currentCampaignId) return;
    const btn = e.target;
    btn.disabled = true;
    
    try {
        const res = await fetch(`/api/campaign/${currentCampaignId}/video/start`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ prompt: 'A cool video scene' })
        });
        const data = await res.json();
        pollVideoStatus(data.job_id);
    } catch (err) {
        console.error(err);
        btn.disabled = false;
    }
});

async function pollVideoStatus(jobId) {
    const textEl = document.getElementById('video-status-text');
    const barEl = document.getElementById('video-progress-bar');
    
    const interval = setInterval(async () => {
        try {
            const res = await fetch(`/api/campaign/${currentCampaignId}/video/status/${jobId}`);
            const data = await res.json();
            
            textEl.textContent = `Status: ${data.status}`;
            if (data.status === 'processing') {
                barEl.style.width = '50%';
            } else if (data.status === 'completed') {
                barEl.style.width = '100%';
                clearInterval(interval);
                showPanel('panel-music');
            } else if (data.status === 'failed') {
                clearInterval(interval);
                document.getElementById('btn-start-video').disabled = false;
            }
        } catch (err) {
            console.error(err);
        }
    }, 2000);
}

// 6. Music Generation
document.getElementById('btn-generate-music').addEventListener('click', async (e) => {
    if (!currentCampaignId) return;
    const btn = e.target;
    btn.disabled = true;
    
    try {
        const res = await fetch(`/api/campaign/${currentCampaignId}/music`, {
            method: 'POST'
        });
        const data = await res.json();
        document.getElementById('music-status').textContent = `Music generated! Mood: ${data.mood}`;
        
        const player = document.createElement('audio');
        player.controls = true;
        player.src = data.audio_url;
        const container = document.getElementById('music-player-container');
        container.innerHTML = '';
        container.appendChild(player);
        
        showPanel('panel-final');
    } catch (err) {
        console.error(err);
    } finally {
        btn.disabled = false;
    }
});

// 7. Final Preview
document.getElementById('btn-get-final').addEventListener('click', async (e) => {
    if (!currentCampaignId) return;
    const btn = e.target;
    btn.disabled = true;
    
    try {
        const res = await fetch(`/api/campaign/${currentCampaignId}/final`);
        const data = await res.json();
        
        let htmlContent = `<div style="text-align: center;">
            <p><strong>Theme:</strong> ${data.theme || 'N/A'}</p>
            <p><strong>Mood:</strong> ${data.mood || 'N/A'}</p>`;
            
        if (data.video_url) {
            htmlContent += `
            <video controls style="max-width: 100%; border-radius: 8px; border: 1px solid var(--border); margin-top: 1rem;">
                <source src="${data.video_url}" type="video/mp4">
                Your browser does not support the video tag.
            </video>`;
        } else {
            htmlContent += `<p style="color: red;">No video URL returned.</p>`;
        }
        
        htmlContent += `</div>`;
        document.getElementById('final-preview-content').innerHTML = htmlContent;
        
    } catch (err) {
        console.error(err);
        document.getElementById('final-preview-content').innerHTML = `<p style="color: red;">Error loading preview.</p>`;
    } finally {
        btn.disabled = false;
    }
});

// Static Shells Wiring
function displayPrebakedVideo(src, text) {
    const display = document.getElementById('variation-display');
    display.innerHTML = `
        <p><strong>${text}</strong></p>
        <video controls autoplay style="max-width: 100%; border-radius: 8px; border: 1px solid var(--border);">
            <source src="${src}" type="video/mp4">
            Your browser does not support the video tag.
        </video>
    `;
}

document.getElementById('card-1x1').addEventListener('click', () => {
    displayPrebakedVideo('/static/prebaked/variation_1x1.mp4', 'Showing 1:1 Variation (Instagram)');
});

document.getElementById('card-9x16').addEventListener('click', () => {
    displayPrebakedVideo('/static/prebaked/variation_9x16.mp4', 'Showing 9:16 Variation (TikTok)');
});

document.getElementById('btn-chat-send').addEventListener('click', () => {
    const input = document.getElementById('chat-input');
    if (!input.value.trim()) return;
    displayPrebakedVideo('/static/prebaked/conversational_edit.mp4', `Showing result for: "${input.value}"`);
    input.value = '';
});

