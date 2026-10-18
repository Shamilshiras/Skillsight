/**
 * SkillSight Dashboard Interactive Frontend Logic.
 * Manages Chart.js visualizations, REST API data fetching, interactive filters,
 * comparison presets, pagination, and real-time ETL pipeline execution triggers.
 */

document.addEventListener('DOMContentLoaded', () => {
    // State
    const state = {
        topSkills: {
            days: 7,
            category: 'language',
            chart: null,
        },
        trends: {
            days: 30,
            skills: ['django', 'flask'],
            chart: null,
        },
        categoryShare: {
            chart: null,
        },
        jobs: {
            page: 1,
            pageSize: 6,
            search: '',
            skill: '',
            remote: false,
        },
        allSkills: [],
    };

    // Helper: Toast Notifications
    function showToast(message, type = 'success') {
        const container = document.getElementById('toast-container');
        if (!container) return;
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.innerHTML = `<span>${type === 'success' ? '✓' : '⚠️'}</span> <span>${message}</span>`;
        container.appendChild(toast);
        setTimeout(() => {
            toast.style.opacity = '0';
            setTimeout(() => toast.remove(), 300);
        }, 4000);
    }

    // --- 1. Fetch & Update KPI Summary ---
    async function loadSummaryMetrics() {
        try {
            const res = await fetch('/api/summary/?days=7');
            if (!res.ok) return;
            const data = await res.json();

            document.getElementById('val-total-jobs').textContent = data.total_jobs_analyzed.toLocaleString();
            document.getElementById('val-top-lang').textContent = data.top_language || 'Python';
            document.getElementById('val-top-framework').textContent = data.top_framework || 'React';
            document.getElementById('val-growth-skill').textContent = data.fastest_growing_skill || 'Python';
            
            const growthPct = data.fastest_growth_percentage || 0;
            document.getElementById('val-growth-pct').textContent = `${growthPct >= 0 ? '+' : ''}${growthPct}% vs prior week`;
            document.getElementById('val-remote-ratio').textContent = `${data.remote_percentage || 0}%`;

            if (data.latest_pipeline_run) {
                const run = data.latest_pipeline_run;
                document.getElementById('val-pipeline-status').textContent = run.status;
                const statusDot = document.querySelector('#pipeline-status-badge .status-indicator-dot');
                if (statusDot) {
                    statusDot.className = `status-indicator-dot ${run.status === 'SUCCESS' ? 'success' : run.status === 'WARNING' ? 'warning' : 'failed'}`;
                }
                const execDate = new Date(run.executed_at);
                document.getElementById('last-sync-time').textContent = `Last Run: ${execDate.toLocaleDateString()} ${execDate.toLocaleTimeString()}`;
                document.getElementById('val-pipeline-duration').textContent = `Run time: ${run.duration_seconds}s (${run.jobs_fetched} fetched)`;
            }
        } catch (err) {
            console.error('Error fetching summary KPIs:', err);
        }
    }

    // --- 2. Top In-Demand Skills Bar Chart ---
    async function renderTopSkillsChart() {
        const { days, category } = state.topSkills;
        try {
            const res = await fetch(`/api/top-skills/?days=${days}&category=${category}&limit=10`);
            if (!res.ok) return;
            const data = await res.json();
            const skills = data.skills || [];

            const labels = skills.map(s => s.name);
            const counts = skills.map(s => s.job_count);
            const percentages = skills.map(s => s.demand_percentage);
            const colors = skills.map(s => s.color || '#38bdf8');

            const ctx = document.getElementById('topSkillsChart').getContext('2d');

            if (state.topSkills.chart) {
                state.topSkills.chart.destroy();
            }

            state.topSkills.chart = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: labels,
                    datasets: [{
                        label: 'Job Postings Mentioning Skill',
                        data: counts,
                        backgroundColor: colors.map(c => c + 'CC'),
                        borderColor: colors,
                        borderWidth: 1.5,
                        borderRadius: 6,
                        hoverBackgroundColor: colors,
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { display: false },
                        tooltip: {
                            backgroundColor: '#111827',
                            titleColor: '#f8fafc',
                            bodyColor: '#94a3b8',
                            borderColor: '#374151',
                            borderWidth: 1,
                            padding: 12,
                            displayColors: false,
                            callbacks: {
                                label: function(context) {
                                    const idx = context.dataIndex;
                                    return [
                                        `Postings: ${context.parsed.y} jobs`,
                                        `Market Presence: ${percentages[idx]}% of analyzed jobs`
                                    ];
                                }
                            }
                        }
                    },
                    scales: {
                        x: {
                            grid: { display: false },
                            ticks: { color: '#94a3b8', font: { family: 'Inter', size: 12 } }
                        },
                        y: {
                            grid: { color: 'rgba(55, 65, 81, 0.4)' },
                            ticks: {
                                color: '#94a3b8',
                                font: { family: 'Inter', size: 11 },
                                precision: 0
                            },
                            beginAtZero: true
                        }
                    }
                }
            });

            // Also update Leaderboard Table with this data
            updateLeaderboardTable(skills);
        } catch (err) {
            console.error('Error rendering top skills chart:', err);
        }
    }

    // --- 3. 30-Day Historical Trend Line Chart ---
    async function renderTrendsChart() {
        const { days, skills } = state.trends;
        const skillsQuery = skills.join(',');
        try {
            const res = await fetch(`/api/trends/?skills=${skillsQuery}&days=${days}`);
            if (!res.ok) return;
            const data = await res.json();

            const dates = data.dates || [];
            const seriesList = data.series || [];

            const datasets = seriesList.map(s => ({
                label: s.name,
                data: s.counts,
                borderColor: s.color || '#38bdf8',
                backgroundColor: s.color ? s.color + '22' : 'rgba(56, 189, 248, 0.1)',
                borderWidth: 2.5,
                tension: 0.35,
                fill: true,
                pointRadius: dates.length > 30 ? 2 : 4,
                pointHoverRadius: 6,
                pointBackgroundColor: s.color,
            }));

            const ctx = document.getElementById('trendsChart').getContext('2d');

            if (state.trends.chart) {
                state.trends.chart.destroy();
            }

            state.trends.chart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: dates,
                    datasets: datasets
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    interaction: {
                        mode: 'index',
                        intersect: false,
                    },
                    plugins: {
                        legend: {
                            position: 'top',
                            labels: {
                                color: '#f8fafc',
                                font: { family: 'Inter', weight: 600, size: 12 },
                                usePointStyle: true,
                                boxWidth: 8
                            }
                        },
                        tooltip: {
                            backgroundColor: '#111827',
                            titleColor: '#f8fafc',
                            bodyColor: '#94a3b8',
                            borderColor: '#374151',
                            borderWidth: 1,
                            padding: 12,
                        }
                    },
                    scales: {
                        x: {
                            grid: { display: false },
                            ticks: {
                                color: '#94a3b8',
                                font: { family: 'JetBrains Mono', size: 10 },
                                maxTicksLimit: 10
                            }
                        },
                        y: {
                            grid: { color: 'rgba(55, 65, 81, 0.4)' },
                            ticks: {
                                color: '#94a3b8',
                                font: { family: 'Inter', size: 11 },
                                precision: 0
                            },
                            beginAtZero: true
                        }
                    }
                }
            });

            renderActiveChips();
        } catch (err) {
            console.error('Error rendering trends chart:', err);
        }
    }

    // Helper: Render active comparison chips
    function renderActiveChips() {
        const container = document.getElementById('active-skill-chips');
        if (!container) return;
        container.innerHTML = '';

        state.trends.skills.forEach(slug => {
            const skillObj = state.allSkills.find(s => s.slug === slug) || { name: slug, color: '#38bdf8' };
            const chip = document.createElement('div');
            chip.className = 'skill-chip';
            chip.innerHTML = `
                <span class="chip-color-dot" style="background-color: ${skillObj.color || '#38bdf8'};"></span>
                <span>${skillObj.name}</span>
                ${state.trends.skills.length > 1 ? `<button class="chip-remove-btn" data-slug="${slug}">&times;</button>` : ''}
            `;
            container.appendChild(chip);
        });

        // Attach chip remove listeners
        container.querySelectorAll('.chip-remove-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const slugToRemove = e.target.getAttribute('data-slug');
                state.trends.skills = state.trends.skills.filter(s => s !== slugToRemove);
                renderTrendsChart();
            });
        });
    }

    // --- 4. Category Demand Share Doughnut Chart ---
    async function renderCategoryShareChart() {
        try {
            const res = await fetch('/api/top-skills/?days=30&category=all&limit=50');
            if (!res.ok) return;
            const data = await res.json();
            const skills = data.skills || [];

            const categoryCounts = {
                'language': 0,
                'framework': 0,
                'database': 0,
                'cloud_devops': 0,
            };

            skills.forEach(s => {
                if (categoryCounts[s.category] !== undefined) {
                    categoryCounts[s.category] += s.job_count;
                }
            });

            const labels = ['Languages', 'Frameworks', 'Databases', 'Cloud & DevOps'];
            const counts = [
                categoryCounts.language,
                categoryCounts.framework,
                categoryCounts.database,
                categoryCounts.cloud_devops,
            ];

            const ctx = document.getElementById('categoryShareChart').getContext('2d');

            if (state.categoryShare.chart) {
                state.categoryShare.chart.destroy();
            }

            state.categoryShare.chart = new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: labels,
                    datasets: [{
                        data: counts,
                        backgroundColor: ['#38bdf8', '#10b981', '#a78bfa', '#fbbf24'],
                        borderColor: '#111827',
                        borderWidth: 2,
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'bottom',
                            labels: {
                                color: '#f8fafc',
                                font: { family: 'Inter', size: 11 },
                                boxWidth: 10
                            }
                        }
                    },
                    cutout: '68%'
                }
            });
        } catch (err) {
            console.error('Error rendering category share chart:', err);
        }
    }

    // --- 5. Leaderboard Table ---
    function updateLeaderboardTable(skills) {
        const tbody = document.getElementById('leaderboard-tbody');
        if (!tbody) return;

        if (!skills || skills.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" class="text-center">No skill data recorded yet.</td></tr>';
            return;
        }

        tbody.innerHTML = skills.map((s, idx) => `
            <tr>
                <td><strong>#${idx + 1}</strong></td>
                <td>
                    <div class="tech-cell">
                        <span class="tech-dot" style="background-color: ${s.color || '#38bdf8'};"></span>
                        <span>${s.name}</span>
                    </div>
                </td>
                <td><span class="badge-tag ${s.category}">${s.category.replace('_', ' ')}</span></td>
                <td><strong>${s.job_count.toLocaleString()}</strong> postings</td>
                <td>
                    <div style="display:flex; align-items:center; gap:0.5rem;">
                        <div style="flex:1; height:6px; background-color:#1f2937; border-radius:3px; overflow:hidden;">
                            <div style="width:${Math.min(s.demand_percentage * 2, 100)}%; height:100%; background-color:${s.color || '#38bdf8'};"></div>
                        </div>
                        <span style="font-size:0.75rem; font-family:'JetBrains Mono';">${s.demand_percentage}%</span>
                    </div>
                </td>
                <td><span class="status-badge success">High Demand</span></td>
            </tr>
        `).join('');
    }

    // --- 6. Live Job Postings Feed ---
    async function loadJobFeed() {
        const { page, pageSize, search, skill, remote } = state.jobs;
        const container = document.getElementById('jobs-list');
        if (!container) return;

        try {
            const query = new URLSearchParams({
                page: page,
                page_size: pageSize,
                search: search,
                skill: skill,
                remote: remote ? 'true' : ''
            });

            const res = await fetch(`/api/jobs/?${query.toString()}`);
            if (!res.ok) return;
            const data = await res.json();

            const jobs = data.jobs || [];
            if (jobs.length === 0) {
                container.innerHTML = '<div class="loading-state">No matching job postings found.</div>';
                return;
            }

            container.innerHTML = jobs.map(j => `
                <div class="job-card">
                    <div class="job-main">
                        <div class="job-header">
                            <h3 class="job-title">${j.title}</h3>
                            ${j.is_remote ? '<span class="job-badge-remote">Remote</span>' : ''}
                        </div>
                        <div class="job-company">${j.company_name} &bull; ${j.location || 'Remote'}</div>
                        <p class="job-snippet">${j.description_snippet || 'No description preview available.'}</p>
                        <div class="job-skills">
                            ${(j.skills || []).map(s => `<span class="skill-pill" style="border-color:${s.color}44; color:${s.color}">${s.name}</span>`).join('')}
                        </div>
                    </div>
                    <div class="job-side">
                        <span class="job-date">${j.posted_date}</span>
                        ${j.url ? `<a href="${j.url}" target="_blank" rel="noopener noreferrer" class="btn btn-secondary btn-sm">Apply &rarr;</a>` : ''}
                    </div>
                </div>
            `).join('');

            // Update pagination
            document.getElementById('page-indicator').textContent = `Page ${data.current_page} of ${data.total_pages || 1}`;
            document.getElementById('btn-prev-page').disabled = !data.has_previous;
            document.getElementById('btn-next-page').disabled = !data.has_next;
        } catch (err) {
            console.error('Error loading job feed:', err);
        }
    }

    // --- 7. Pipeline Operational Logs ---
    async function loadPipelineLogs() {
        const tbody = document.getElementById('logs-tbody');
        if (!tbody) return;

        try {
            const res = await fetch('/api/logs/?limit=10');
            if (!res.ok) return;
            const data = await res.json();
            const logs = data.logs || [];

            if (logs.length === 0) {
                tbody.innerHTML = '<tr><td colspan="7" class="text-center">No pipeline execution logs recorded yet.</td></tr>';
                return;
            }

            tbody.innerHTML = logs.map(l => {
                const date = new Date(l.executed_at);
                const statusClass = l.status === 'SUCCESS' ? 'success' : l.status === 'WARNING' ? 'warning' : 'failed';
                const errorSnippet = l.error_message ? `<span style="color:#f87171;" title="${l.error_message}">${l.error_message.slice(0, 45)}...</span>` : '<span style="color:#34d399;">Clean Run</span>';

                return `
                    <tr>
                        <td><span class="status-badge ${statusClass}">${l.status}</span></td>
                        <td class="mono-text">${l.run_id}</td>
                        <td class="mono-text">${date.toISOString().replace('T', ' ').slice(0, 19)}</td>
                        <td>${l.duration_seconds}s</td>
                        <td><strong>${l.jobs_fetched}</strong> jobs</td>
                        <td>${l.source}</td>
                        <td>${errorSnippet}</td>
                    </tr>
                `;
            }).join('');
        } catch (err) {
            console.error('Error loading pipeline logs:', err);
        }
    }

    // --- 8. Populate Skills Taxonomy in Dropdowns ---
    async function loadSkillsTaxonomy() {
        try {
            const res = await fetch('/api/categories/');
            if (!res.ok) return;
            const data = await res.json();
            const categories = data.categories || [];

            const flatSkills = [];
            const pickerSelect = document.getElementById('skill-picker-select');
            const jobSkillFilter = document.getElementById('job-skill-filter');

            categories.forEach(cat => {
                const optGroup = document.createElement('optgroup');
                optGroup.label = cat.category_name;

                cat.skills.forEach(s => {
                    flatSkills.push(s);
                    const opt = document.createElement('option');
                    opt.value = s.slug;
                    opt.textContent = s.name;
                    optGroup.appendChild(opt);
                });

                if (pickerSelect) pickerSelect.appendChild(optGroup.cloneNode(true));
                if (jobSkillFilter) jobSkillFilter.appendChild(optGroup.cloneNode(true));
            });

            state.allSkills = flatSkills;
        } catch (err) {
            console.error('Error loading taxonomy:', err);
        }
    }

    // --- 9. Event Listeners ---

    // Top Skills Category Tabs
    document.querySelectorAll('#skill-category-tabs .tab-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            document.querySelectorAll('#skill-category-tabs .tab-btn').forEach(b => b.classList.remove('active'));
            e.target.classList.add('active');
            state.topSkills.category = e.target.getAttribute('data-category');
            renderTopSkillsChart();
        });
    });

    // Top Skills Time Window
    document.getElementById('top-skills-days')?.addEventListener('change', (e) => {
        state.topSkills.days = parseInt(e.target.value);
        renderTopSkillsChart();
    });

    // Trends Presets
    document.querySelectorAll('.preset-pills .pill-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            document.querySelectorAll('.preset-pills .pill-btn').forEach(b => b.classList.remove('active'));
            e.target.classList.add('active');
            const skillsStr = e.target.getAttribute('data-skills');
            state.trends.skills = skillsStr.split(',');
            renderTrendsChart();
        });
    });

    // Trends Time Window
    document.getElementById('trends-days')?.addEventListener('change', (e) => {
        state.trends.days = parseInt(e.target.value);
        renderTrendsChart();
    });

    // Custom Skill Picker Select
    document.getElementById('skill-picker-select')?.addEventListener('change', (e) => {
        const selectedSlug = e.target.value;
        if (selectedSlug && !state.trends.skills.includes(selectedSlug)) {
            state.trends.skills.push(selectedSlug);
            document.querySelectorAll('.preset-pills .pill-btn').forEach(b => b.classList.remove('active'));
            renderTrendsChart();
        }
        e.target.value = '';
    });

    // Job Feed Filters
    let searchDebounce = null;
    document.getElementById('job-search-input')?.addEventListener('input', (e) => {
        clearTimeout(searchDebounce);
        searchDebounce = setTimeout(() => {
            state.jobs.search = e.target.value;
            state.jobs.page = 1;
            loadJobFeed();
        }, 350);
    });

    document.getElementById('job-skill-filter')?.addEventListener('change', (e) => {
        state.jobs.skill = e.target.value;
        state.jobs.page = 1;
        loadJobFeed();
    });

    document.getElementById('job-remote-filter')?.addEventListener('change', (e) => {
        state.jobs.remote = e.target.checked;
        state.jobs.page = 1;
        loadJobFeed();
    });

    document.getElementById('btn-prev-page')?.addEventListener('click', () => {
        if (state.jobs.page > 1) {
            state.jobs.page -= 1;
            loadJobFeed();
        }
    });

    document.getElementById('btn-next-page')?.addEventListener('click', () => {
        state.jobs.page += 1;
        loadJobFeed();
    });

    document.getElementById('btn-refresh-logs')?.addEventListener('click', () => {
        loadPipelineLogs();
        showToast('Logs refreshed.');
    });

    // On-Demand ETL Pipeline Trigger Button
    document.getElementById('btn-trigger-etl')?.addEventListener('click', async () => {
        const btn = document.getElementById('btn-trigger-etl');
        btn.disabled = true;
        btn.querySelector('.btn-text').textContent = 'Running Pipeline...';
        showToast('ETL Pipeline execution started...', 'success');

        try {
            const res = await fetch('/api/trigger-etl/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ pages: 2, force_fallback: false })
            });
            const data = await res.json();

            if (res.ok) {
                showToast(`Pipeline Complete! Processed ${data.details.jobs_saved} jobs.`, 'success');
                // Refresh all dashboard metrics
                loadSummaryMetrics();
                renderTopSkillsChart();
                renderTrendsChart();
                renderCategoryShareChart();
                loadJobFeed();
                loadPipelineLogs();
            } else {
                showToast(`ETL Run Failed: ${data.error || 'Server error'}`, 'error');
            }
        } catch (err) {
            showToast('Failed to trigger ETL pipeline.', 'error');
            console.error(err);
        } finally {
            btn.disabled = false;
            btn.querySelector('.btn-text').textContent = 'Run ETL Now';
        }
    });

    // --- Initial Load ---
    async function init() {
        await loadSkillsTaxonomy();
        loadSummaryMetrics();
        renderTopSkillsChart();
        renderTrendsChart();
        renderCategoryShareChart();
        loadJobFeed();
        loadPipelineLogs();
    }

    init();
});
