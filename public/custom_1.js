window.addEventListener('message', (event) => {
  console.log(event.data);
  if (event.data.message === 'chat_settings_update') {
    const updated_settings = event.data.data;
    // Check if custom DOM element exists
    let settingsDiv = document.getElementById('chat-settings-storage');
    if (!settingsDiv) {
      settingsDiv = document.createElement('div');
      settingsDiv.id = 'chat-settings-storage';
      settingsDiv.style.display = 'none'; // hidden element
      document.body.appendChild(settingsDiv);
    }
    // Save settings as JSON string in a data attribute
    settingsDiv.setAttribute('data-chat-settings', JSON.stringify(updated_settings));
    // ✅ Dispatch custom event with bubbling enabled
    const customEvent = new CustomEvent('chatSettingsUpdated', {
      detail: event.data.data,
      bubbles: true, // <-- this is key!
    });
    settingsDiv.dispatchEvent(customEvent);
  }
});

function modifyUI() {
  // Find the header container
  let header = document.getElementById('header');
  if (!header) {
    console.warn('Header container not found');
    return;
  }

  // Check if the model pill already exists
  let modelPill = document.getElementById('model-pill');
  if (!modelPill) {
    // Create pill if it doesn’t exist
    modelPill = document.createElement('span');
    modelPill.id = 'model-pill';
    modelPill.style.padding = '6px 12px';
    modelPill.style.marginLeft = '10px';
    modelPill.style.backgroundColor = '#007bff';
    modelPill.style.color = '#fff';
    modelPill.style.borderRadius = '12px';
    modelPill.style.fontSize = '14px';
    modelPill.style.fontWeight = 'bold';

    // Find the top flex container inside header
    const topFlex = header.querySelector('.flex');
    if (topFlex) {
      topFlex.appendChild(modelPill);
    } else {
      // Fallback to header if flex container not found
      header.appendChild(modelPill);
    }
  }

  // Fetch selected model from chat settings (only if available)
  const chatSettingsStorage = document.getElementById('chat-settings-storage');
  const settingsJSON = chatSettingsStorage?.getAttribute('data-chat-settings');
  if (settingsJSON) {
    const settings = JSON.parse(settingsJSON);
    modelPill.textContent = settings.Model;
    console.log(settings);
  }
}

// Anywhere else in your app
document.addEventListener('chatSettingsUpdated', (e) => {
  console.log('Custom Event Fired! New settings:', e.detail);
  modifyUI();
});

// document.addEventListener('DOMContentLoaded', function () {
//   console.log('Custom Chainlit UI Loaded');

//   // Get full URL including query parameters if needed
//   const fullUrl = window.location.href;
//   console.log('Full URL:', fullUrl);

//   // Parse out thread ID if present
//   const threadId = fullUrl.split('/').pop();
//   console.log('Thread ID:', threadId);

//   // Run modification after UI loads
//   setTimeout(modifyUI, 1000);

//   // Observer for dynamic updates
//   const settingsDiv = document.getElementById('chat-settings-storage');
//   if (settingsDiv) {
//     observer.observe(settingsDiv, { attributes: true });
//   }
//   let observer = new MutationObserver(modifyUI);
//   observer.observe(document.body, { childList: true, subtree: true });
// });
