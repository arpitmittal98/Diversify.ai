// Content script that runs on job sites
function tryQuerySelectors(selectors) {
    for (const selector of selectors) {
        const element = document.querySelector(selector);
        if (element && element.textContent.trim()) {
            return element.textContent.trim();
        }
    }
    return null;
}

function extractJobDetails() {
    if (window.location.hostname.includes('linkedin.com')) {
        // LinkedIn specific selectors with fallbacks
        const descriptionSelectors = [
            '.jobs-description-content__text',
            '.jobs-box__html-content',
            '[data-job-description]',
            '#job-details',
            '.description__text',
            // Broader fallback selectors
            '[class*="job-details"]',
            '[class*="description"]'
        ];

        const companySelectors = [
            '.jobs-unified-top-card__company-name',
            '.jobs-company__name',
            '[data-tracking-control-name*="company"]',
            // Broader fallback selectors
            'a[href*="/company/"]',
            '[class*="company"]'
        ];

        const titleSelectors = [
            '.jobs-unified-top-card__job-title',
            '.job-details-jobs-unified-top-card__job-title',
            '[class*="job-title"]',
            'h1'
        ];

        const jobDescription = tryQuerySelectors(descriptionSelectors);
        const companyName = tryQuerySelectors(companySelectors);
        const jobTitle = tryQuerySelectors(titleSelectors);

        // Additional check for description in nested elements
        if (!jobDescription) {
            const container = document.querySelector('.jobs-description');
            if (container) {
                const paragraphs = Array.from(container.querySelectorAll('p, li, div')).map(el => el.textContent.trim()).filter(Boolean);
                if (paragraphs.length > 0) {
                    return {
                        description: paragraphs.join('\n'),
                        company: companyName || 'Unknown Company',
                        title: jobTitle || 'Job Position'
                    };
                }
            }
        }

        if (jobDescription && companyName) {
            console.log('Successfully extracted job details');
            return {
                description: jobDescription,
                company: companyName,
                title: jobTitle || 'Job Position'
            };
        }
    }
    
    console.log('Failed to extract job details');
    return null;
}

// Listen for messages from popup
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === "analyze") {
        console.log('Content script received "analyze" action');
        const jobDetails = extractJobDetails();
        if (!jobDetails) {
            sendResponse({
                error: "Could not find job details. Please make sure you're on a LinkedIn job posting page."
            });
            return false; // No async response needed
        }

        console.log('Job details found:', jobDetails);

        // Send job details to the background script for analysis.
        // The background script will fetch user skills from storage.
        console.log('Sending job details to background script for analysis');
        chrome.runtime.sendMessage({
            type: 'analyzeJob',
            data: jobDetails
        }, response => {
            // This callback handles the final response from the background script
            if (chrome.runtime.lastError) {
                console.error('Error in message response:', chrome.runtime.lastError.message);
                sendResponse({ error: `Extension communication error: ${chrome.runtime.lastError.message}` });
                return;
            }
            
            if (!response) {
                console.error('No response from background script. It might have been invalidated.');
                sendResponse({ error: "Extension error: No response from background service." });
                return;
            }

            if (response.error) {
                console.error('Analysis failed:', response.error);
                sendResponse({ error: response.error });
            } else {
                console.log('Forwarding analysis response to popup:', response);
                sendResponse(response);
            }
        });

        return true; // IMPORTANT: Indicates you will send a response asynchronously
    }
});