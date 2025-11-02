// Initialize user data
let userSkills = [];

// Helper function to save skills
function saveUserSkills(skills) {
    return new Promise((resolve) => {
        chrome.storage.local.set({
            userSkills: skills,
            profileSetup: true
        }, () => {
            console.log('Saved user skills:', skills);
            resolve();
        });
    });
}

// Load saved skills on popup open
document.addEventListener('DOMContentLoaded', () => {
    console.log('Popup opened, loading saved skills...');
    chrome.storage.local.get(['userSkills', 'profileSetup'], (result) => {
        console.log('Storage data:', result);
        if (result.userSkills && Array.isArray(result.userSkills)) {
            userSkills = result.userSkills;
            console.log('Loaded user skills:', userSkills);
            displayUserSkills();  // Update display with loaded skills
        }
        
        // Show appropriate section
        if (!result.profileSetup) {
            showSection('profile-setup');
        } else {
            showSection('analysis-section');
            displayUserSkills();
        }
        
        // Add event listeners for adding skills
        document.getElementById('add-skill-btn').addEventListener('click', addSkills);
        document.getElementById('skill-input').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                addSkills();
            }
        });
    });
});

// Helper function to show/hide sections
function showSection(sectionId) {
    document.querySelectorAll('.section').forEach(section => {
        section.classList.remove('active');
    });
    document.getElementById(sectionId).classList.add('active');
}

// Skills management
// Function to add skills
async function addSkills() {
    const input = document.getElementById('skill-input');
    const skillsText = input.value.trim().toLowerCase();
    
    if (!skillsText) return;
    
    // Split by commas and clean up each skill
    const newSkills = skillsText.split(',')
        .map(skill => skill.trim())
        .filter(skill => skill.length > 0);
    
    // Add only unique skills
    let addedCount = 0;
    newSkills.forEach(skill => {
        if (!userSkills.includes(skill)) {
            userSkills.push(skill);
            addedCount++;
        }
    });
    
    // Save skills immediately
    await saveUserSkills(userSkills);
    
    displayUserSkills();
    input.value = '';
    
    // Show feedback
    const hint = document.querySelector('.skill-hint');
    if (addedCount > 0) {
        hint.textContent = `Added ${addedCount} new skill${addedCount === 1 ? '' : 's'}!`;
        setTimeout(() => {
            hint.textContent = 'Enter multiple skills at once, separated by commas';
        }, 2000);
    }
}

function displayUserSkills() {
    const container = document.getElementById('skills-list');
    container.innerHTML = userSkills.map(skill => `
        <div class="skill-tag">
            ${skill}
            <span class="remove" data-skill="${skill}">×</span>
        </div>
    `).join('');
    
    // Add remove event listeners
    container.querySelectorAll('.remove').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const skillToRemove = e.target.dataset.skill;
            userSkills = userSkills.filter(s => s !== skillToRemove);
            displayUserSkills();
        });
    });
}

// Save profile
document.getElementById('save-profile-btn').addEventListener('click', async () => {
    console.log('Saving user skills:', userSkills);
    await saveUserSkills(userSkills);
    showSection('analysis-section');
});

// Edit profile button
document.getElementById('edit-profile-btn').addEventListener('click', () => {
    showSection('profile-setup');
});

// Footer link
document.getElementById('website-link').addEventListener('click', (e) => {
    e.preventDefault();
    chrome.tabs.create({ url: 'about:blank' });
});

// Helper function to show error message
function showError(message) {
    const errorDiv = document.getElementById('error-message');
    errorDiv.innerHTML = `<div class="skill-status missing">!</div> <div class="skill-name">${message}</div>`;
    errorDiv.classList.add('visible');
    
    // Hide the error after 5 seconds
    setTimeout(() => {
        errorDiv.classList.remove('visible');
        errorDiv.innerHTML = ''; // Clear content
    }, 5000);
}

// Helper function to clear error message
function clearError() {
    const errorDiv = document.getElementById('error-message');
    errorDiv.classList.remove('visible');
    errorDiv.innerHTML = ''; // Clear content
}

// Analyze button
document.getElementById('analyze-btn').addEventListener('click', () => {
    clearError();
    chrome.tabs.query({active: true, currentWindow: true}, (tabs) => {
        if (!tabs[0]?.url?.includes('linkedin.com/jobs')) {
            showError('Please navigate to a LinkedIn job posting first.');
            return;
        }

        chrome.tabs.sendMessage(tabs[0].id, {action: "analyze"}, response => {
            if (chrome.runtime.lastError) {
                showError(`Error: ${chrome.runtime.lastError.message}`);
                return;
            }
            if (!response) {
                showError('No response from the page. Please refresh and try again.');
                return;
            }
            if (response.error) {
                showError(response.error);
                return;
            }

            // The actual analysis data is nested inside the 'data' property
            const analysisData = response.data;
            if (!analysisData) {
                showError('Invalid response structure from background script.');
                return;
            }
            
            try {
                if (!analysisData.skills || !Array.isArray(analysisData.skills)) {
                    throw new Error('Invalid skills format from server');
                }

                // Get match percentage from response
                const matchPercent = analysisData.matchPercentage || 0;
                
                // Calculate matching skills
                const jobSkills = analysisData.skills.map(s => s.toLowerCase());
                const matchingSkills = userSkills.filter(skill => 
                    jobSkills.some(jobSkill => jobSkill.includes(skill.toLowerCase()))
                );
                const missingSkills = jobSkills.filter(skill => 
                    !userSkills.some(userSkill => skill.toLowerCase().includes(userSkill.toLowerCase()))
                );
            
                // Update match percentage
                document.getElementById('match-percentage').textContent = matchPercent + '%';
                
                // Update skills list with matches and missing skills
                const skillsList = document.getElementById('skills-list');
                skillsList.innerHTML = '';
                
                // Add matching skills first (green checkmarks)
                matchingSkills.forEach(skill => {
                    const skillItem = document.createElement('div');
                    skillItem.className = 'skill-item';
                    skillItem.innerHTML = `
                        <div class="skill-status match">✓</div>
                        <div class="skill-name">${skill}</div>
                    `;
                    skillsList.appendChild(skillItem);
                });
                
                // Add missing skills (yellow exclamation marks)
                missingSkills.forEach(skill => {
                    const skillItem = document.createElement('div');
                    skillItem.className = 'skill-item';
                    skillItem.innerHTML = `
                        <div class="skill-status missing">!</div>
                        <div class="skill-name">${skill}</div>
                    `;
                    skillsList.appendChild(skillItem);
                });
                
                // Update inclusion score with number and stars
                if (typeof analysisData.inclusionScore === 'number') {
                    // Update the numeric score
                    document.getElementById('inclusion-number').textContent = analysisData.inclusionScore + '/5';
                    // Update the star display
                    const stars = '★'.repeat(analysisData.inclusionScore) + '☆'.repeat(5 - analysisData.inclusionScore);
                    document.getElementById('inclusion-stars').innerHTML = stars;
                }
                
                // Update support programs with new card styling
                if (Array.isArray(analysisData.supportPrograms)) {
                    document.getElementById('programs-list').innerHTML = 
                        analysisData.supportPrograms
                            .map(program => `<div class="program-item">${program}</div>`)
                            .join('');
                }
            } catch (error) {
                console.error('Error processing response:', error);
                showError('Error processing job details: ' + error.message);
            }
        });
    });
});