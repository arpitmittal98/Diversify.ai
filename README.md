# Diversify.ai

**A Chrome extension and backend system designed to help neurodivergent job seekers understand job descriptions, assess their skills match, evaluate company inclusivity and practice job specific interviews.**

---

## 🌟 Overview

Job hunting can be overwhelming for neurodivergent individuals due to technical jargon and complex job descriptions. **Diversify.ai** simplifies this process by:

1. **Converting Job Descriptions into actionable skills** and comparing them to the user's profile, returning a **skill match percentage**.
2. **Researching company disability friendliness**, summarizing inclusivity for specific neurodivergent conditions (e.g., ADHD, Autism) based on publicly available data like Glassdoor reviews, company DEI pages, and blogs.
3. Displaying all results **directly within job websites** such as LinkedIn, Indeed, and Glassdoor via an **in-page overlay**.
4. Providing links to a web platform for advanced tools like **mock interview simulations** and personalized resources.

---

## ⚡ Features

- **Skill Extraction & Match %**
  - Extracts key skills from job descriptions using NLP.
  - Compares extracted skills with the user's uploaded skill profile.
  - Computes a **skill match percentage** to highlight compatibility.

- **Company Inclusivity Insights**
  - Extracts company name from job post.
  - Collects and summarizes information about disability support and inclusivity.
  - Returns a **disability friendliness score** along with evidence snippets.

- **Browser Integration**
  - Chrome extension that overlays insights directly within job listings.
  - Works on popular job portals: LinkedIn, Indeed, Glassdoor.
  - Lightweight, non-intrusive, and easy to use.

- **Backend API**
  - Built with **FastAPI**.
  - Handles skill extraction, match computation, and inclusivity research.
  - Supports LLM integration for summarization and analysis.

---

## 🏗️ Architecture

```text
+----------------------+       +----------------------+
|   Chrome Extension   | <---> |      Backend API     |
|  (Content Scripts)   |       |     (FastAPI)        |
+----------------------+       +----------------------+
         |                                |
         | Extract Job Text               | Extract Skills
         |--------------------------------> Compute Match %
         |                                | Research Company Inclusivity
         | <------------------------------- Return JSON Results
         | Display Overlay on Job Page

