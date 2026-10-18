# Product Requirements Document (PRD)

**Project Name:** SkillSight
**Document Status:** Draft
**Target Completion:** 4-6 Weeks

## 1. Product Overview
SkillSight is an automated data pipeline and analytics dashboard designed to monitor and visualize live trends in the software engineering job market. It automatically extracts daily job postings from public APIs, cleans and aggregates the data to find the most in-demand skills, and serves it to an interactive web dashboard.

## 2. Objectives & Goals
*   **Business Goal:** Provide developers and recruiters with daily insights into which programming languages and frameworks are surging in demand.
*   **Technical Goal:** Architect a fully automated, fault-tolerant ETL (Extract, Transform, Load) pipeline that requires zero manual intervention once deployed.
*   **Portfolio Goal:** Demonstrate full-stack and data engineering proficiency to hiring managers.

## 3. Tech Stack Details
SkillSight leverages a modern data engineering and web development stack:

*   **Workflow Orchestration:** **Apache Airflow** (Schedules and runs the ETL pipeline)
*   **Data Processing:** **Python & Pandas** (Fetches API data, cleans text, extracts keywords)
*   **Database:** **MySQL** (Stores historical job data and daily aggregates)
*   **Backend Framework:** **Django** (Serves REST API endpoints to the frontend)
*   **Frontend UI:** **HTML5 & CSS3** (Responsive dashboard layout)
*   **Data Visualization:** **JavaScript & Chart.js** (Renders interactive trend charts)
*   **Version Control:** **Git & GitHub**

## 4. Architecture & Data Flow
The system operates in four distinct automated phases:

1.  **Extract:** Triggered daily by Airflow, a Python script calls a public job API (e.g., Arbeitnow or Adzuna) to fetch the latest tech job postings in JSON format.
2.  **Transform:** Pandas parses the JSON, normalizes the data, and scans job descriptions for specific tech keywords (e.g., "Python", "React", "AWS") to generate aggregate counts.
3.  **Load:** The cleaned, aggregated data is inserted into the MySQL database.
4.  **Visualize:** The user accesses the Django web app, which queries the MySQL database and displays the trends using Chart.js.

## 5. User Stories
*   **As a user,** I want to see a live bar chart of the top 10 most requested programming languages this week, so I know what to learn next.
*   **As a user,** I want to see a 30-day historical trend line for specific technologies (e.g., Django vs. Flask).
*   **As a system administrator (developer),** I want the database to update automatically every night at midnight UTC via an Airflow DAG.
*   **As a system administrator,** I want to view Airflow logs to easily debug if an API connection fails during the daily data pull.

## 6. Success Metrics
*   **Reliability:** The Airflow DAG successfully completes 7 consecutive daily runs without crashing or requiring manual restarts.
*   **Performance:** The Django dashboard loads and renders charts in under 1.5 seconds by querying optimized aggregate tables.
*   **Documentation:** Clean, heavily commented code with a comprehensive `README.md` explaining how to run the pipeline locally.