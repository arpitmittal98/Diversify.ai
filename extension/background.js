// Background service worker
chrome.runtime.onInstalled.addListener(() => {
    console.log('Inclusive Job Search Assistant installed');
});

// Handle communication between content script and backend
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.type === 'analyzeJob') {
        // Get user skills from storage before making the request
        chrome.storage.local.get(['userSkills'], (result) => {
            console.log('Retrieved user skills from storage:', result.userSkills);
            const requestData = {
                ...request.data,
                skills: result.userSkills || []
            };
            // Log the full request data
            console.log('Full request data:', requestData);
            
            // Log the request for debugging
            console.log('Sending analysis request with skills:', requestData);

            fetch('http://localhost:5000/analyze', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(requestData)
            })
            .then(response => response.json())
            .then(data => {
                console.log('Received analysis response:', data);
                sendResponse({ success: true, data });
            })
            .catch(error => {
                console.error('Analysis request failed:', error);
                sendResponse({ success: false, error: error.message });
            });
        });
        
        return true; // Will respond asynchronously
    }
});
