function getSettingsDiv() {
  let settingsDiv = document.getElementById('chat-settings-storage');
  if (!settingsDiv) {
    settingsDiv = document.createElement('div');
    settingsDiv.id = 'chat-settings-storage';
    settingsDiv.style.display = 'none'; // hidden element
    document.body.appendChild(settingsDiv);
  }
  return settingsDiv;
}

function getThreadId() {
  const path = window.location.pathname;
  const threadId = path.split('/').filter(Boolean)[1].trim(); // Get second non-empty segment
  return threadId;
}

function getSessionId() {
  const sessionId = '123456790';
  return sessionId;
}

function sendAction(action_name, payload) {
  return fetch('/project/action', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      sessionId: getSessionId(),
      action: {
        name: action_name,
        payload: payload,
      },
    }),
  })
    .then((response) => {
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return response.json();
    })
    .catch((error) => {
      console.error('Error sending action:', error);
      throw error;
    });
}

// Sets data variables in the chat settings storage div
// And also dispatches a custom event
window.addEventListener('message', (event) => {
  if (event.data.message === 'chat_settings_update') {
    const updated_settings = event.data.data;

    // Save settings as JSON string in a data attribute
    let settingsDiv = getSettingsDiv();
    settingsDiv.setAttribute('data-chat-settings', JSON.stringify(updated_settings));
    // ✅ Dispatch custom event with bubbling enabled
    const customEvent = new CustomEvent('chatSettingsUpdated', {
      detail: event.data.data,
      bubbles: true, // <-- this is key!
    });
    settingsDiv.dispatchEvent(customEvent);
  } else if (event.data.message === 'datastores_list_update') {
    const updated_datastores = event.data.data;
    // Save settings as JSON string in a data attribute
    let settingsDiv = getSettingsDiv();
    settingsDiv.setAttribute('data-datastores-list', JSON.stringify(updated_datastores));
    const customEvent = new CustomEvent('datastoresListUpdated', {
      detail: event.data.data,
      bubbles: true, // <-- this is key!
    });
    settingsDiv.dispatchEvent(customEvent);
  }
});

function updateChatModelUI() {
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
  const chatSettingsStorage = getSettingsDiv();
  const settingsJSON = chatSettingsStorage?.getAttribute('data-chat-settings');
  if (settingsJSON) {
    const settings = JSON.parse(settingsJSON);
    modelPill.textContent = settings.Model;
    console.log(settings);
  }
}

function updateDatastoresListUI() {
  // Find the header container
  let header = document.getElementById('header');
  if (!header) {
    console.warn('Header container not found');
    return;
  }

  // Check if the datastore select already exists
  let datastoreSelect = document.getElementById('datastore-select');
  if (!datastoreSelect) {
    datastoreSelect = document.createElement('select');
    datastoreSelect.id = 'datastore-select';
    datastoreSelect.style.marginLeft = '10px';
    datastoreSelect.style.width = '200px';
    datastoreSelect.style.appearance = 'none';
    datastoreSelect.style.border = 'none';
    datastoreSelect.style.outline = 'none';
    datastoreSelect.style.cursor = 'pointer';
    datastoreSelect.style.backgroundColor = '#6e78f7'; // Tailwind's blue-600
    datastoreSelect.style.borderRadius = '9999px'; // pill shape
    datastoreSelect.style.padding = '6px 16px';
    datastoreSelect.style.color = '#fff';
    datastoreSelect.style.fontWeight = 'bold';
    datastoreSelect.style.fontSize = '14px';
    datastoreSelect.style.boxShadow = '0 2px 6px rgba(0, 0, 0, 0.2)';

    datastoreSelect.addEventListener('mouseover', () => {
      datastoreSelect.style.backgroundColor = '#1d4ed8'; // darker blue
    });

    datastoreSelect.addEventListener('mouseout', () => {
      datastoreSelect.style.backgroundColor = '#6e78f7';
    });

    datastoreSelect.addEventListener('change', (e) => {
      console.log('Selected datastore:', e.target.value);
      window.postMessage(
        {
          sender: 'UI server',
          message: 'selected_datastore',
          data: e.target.value,
        },
        '*'
      );
    });

    // Find the top flex container inside header
    const topFlex = header.querySelector('.flex');
    if (topFlex) {
      topFlex.appendChild(datastoreSelect);
    } else {
      // Fallback to header if flex container not found
      header.appendChild(datastoreSelect);
    }
  }

  // Fetch selected datastore from chat settings (only if available)
  const chatSettingsStorage = getSettingsDiv();
  const settingsDatastoresJSON = chatSettingsStorage?.getAttribute('data-datastores-list');
  if (settingsDatastoresJSON) {
    const settings = JSON.parse(settingsDatastoresJSON);
    // datastoreSelect.textContent = 'Select Datastore';
    datastoreSelect.innerHTML = settings
      .map((datastore) => `<option value="${datastore}">${datastore}</option>`)
      .join('');
    console.log(settings);
  }
}

// Reactive response to the chatSettingsUpdated event
document.addEventListener('chatSettingsUpdated', (e) => {
  console.log('Custom Event Fired! New settings:', e.detail);
  updateChatModelUI();
});

// Reactive response to the datastoresListUpdated event
document.addEventListener('datastoresListUpdated', (e) => {
  console.log('Custom Event Fired! New datastores:', e.detail);
  updateDatastoresListUI();
});

// document.addEventListener('DOMContentLoaded', () => {
//   // Set up mutation observer to watch for header element
//   const observer = new MutationObserver((mutations) => {
//     mutations.forEach((mutation) => {
//       if (mutation.addedNodes.length) {
//         const header = document.getElementById('header');
//         if (header) {
//           manageDatastoreButton();
//         }
//       }
//     });
//   });

//   // Start observing document for header element
//   observer.observe(document.body, {
//     childList: true,
//     subtree: true,
//   });

//   // Initial check in case header already exists
//   createAndAppendButton();
// });
