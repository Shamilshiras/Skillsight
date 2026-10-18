"""
SkillSight ETL Configuration.
Defines tech skill taxonomy, regex patterns, categories, and color schemes.
"""

# Technical skill taxonomy with categories, regex patterns, and UI colors
TECH_SKILLS = [
    # Programming Languages
    {
        "name": "Python",
        "slug": "python",
        "category": "language",
        "pattern": r"\bpython\b",
        "color": "#3B82F6",  # Blue
    },
    {
        "name": "JavaScript",
        "slug": "javascript",
        "category": "language",
        "pattern": r"\b(javascript|js|es6|es20\d\d)\b",
        "color": "#F59E0B",  # Amber/Yellow
    },
    {
        "name": "TypeScript",
        "slug": "typescript",
        "category": "language",
        "pattern": r"\b(typescript|ts)\b",
        "color": "#2563EB",  # Deep Blue
    },
    {
        "name": "Java",
        "slug": "java",
        "category": "language",
        "pattern": r"\bjava\b(?!\s*script)",
        "color": "#DC2626",  # Red
    },
    {
        "name": "C++",
        "slug": "cpp",
        "category": "language",
        "pattern": r"(?<!\w)c\+\+(?!\w)",
        "color": "#0284C7",  # Sky Blue
    },
    {
        "name": "C#",
        "slug": "csharp",
        "category": "language",
        "pattern": r"(?<!\w)c#(?!\w)|\bc\s*sharp\b",
        "color": "#7C3AED",  # Violet
    },
    {
        "name": "Go",
        "slug": "go",
        "category": "language",
        "pattern": r"\b(golang|go)\b",
        "color": "#06B6D4",  # Cyan
    },
    {
        "name": "Rust",
        "slug": "rust",
        "category": "language",
        "pattern": r"\brust\b",
        "color": "#EA580C",  # Orange
    },
    {
        "name": "Ruby",
        "slug": "ruby",
        "category": "language",
        "pattern": r"\bruby\b",
        "color": "#E11D48",  # Rose
    },
    {
        "name": "PHP",
        "slug": "php",
        "category": "language",
        "pattern": r"\bphp\b",
        "color": "#8B5CF6",  # Purple
    },
    {
        "name": "Swift",
        "slug": "swift",
        "category": "language",
        "pattern": r"\bswift\b",
        "color": "#F97316",  # Orange
    },
    {
        "name": "Kotlin",
        "slug": "kotlin",
        "category": "language",
        "pattern": r"\bkotlin\b",
        "color": "#A855F7",  # Purple
    },
    {
        "name": "SQL",
        "slug": "sql",
        "category": "language",
        "pattern": r"\bsql\b",
        "color": "#10B981",  # Emerald
    },

    # Frameworks & Libraries
    {
        "name": "Django",
        "slug": "django",
        "category": "framework",
        "pattern": r"\bdjango\b",
        "color": "#059669",  # Dark Emerald
    },
    {
        "name": "Flask",
        "slug": "flask",
        "category": "framework",
        "pattern": r"\bflask\b",
        "color": "#64748B",  # Slate
    },
    {
        "name": "FastAPI",
        "slug": "fastapi",
        "category": "framework",
        "pattern": r"\bfastapi\b",
        "color": "#0D9488",  # Teal
    },
    {
        "name": "React",
        "slug": "react",
        "category": "framework",
        "pattern": r"\b(react|react\.js|reactjs)\b",
        "color": "#38BDF8",  # Light Blue
    },
    {
        "name": "Vue.js",
        "slug": "vue",
        "category": "framework",
        "pattern": r"\b(vue|vue\.js|vuejs)\b",
        "color": "#10B981",  # Green
    },
    {
        "name": "Angular",
        "slug": "angular",
        "category": "framework",
        "pattern": r"\bangular\b",
        "color": "#EF4444",  # Red
    },
    {
        "name": "Next.js",
        "slug": "nextjs",
        "category": "framework",
        "pattern": r"\b(next\.js|nextjs)\b",
        "color": "#475569",  # Slate
    },
    {
        "name": "Node.js",
        "slug": "nodejs",
        "category": "framework",
        "pattern": r"\b(node\.js|nodejs|node)\b",
        "color": "#22C55E",  # Green
    },
    {
        "name": "Express",
        "slug": "express",
        "category": "framework",
        "pattern": r"\b(express|express\.js)\b",
        "color": "#6B7280",  # Gray
    },
    {
        "name": "Spring Boot",
        "slug": "spring-boot",
        "category": "framework",
        "pattern": r"\b(spring\s*boot|spring\s*framework)\b",
        "color": "#84CC16",  # Lime
    },
    {
        "name": "Ruby on Rails",
        "slug": "rails",
        "category": "framework",
        "pattern": r"\b(rails|ruby\s*on\s*rails)\b",
        "color": "#DC2626",  # Red
    },
    {
        "name": ".NET Core",
        "slug": "dotnet",
        "category": "framework",
        "pattern": r"(?<!\w)\.net(?!\w)|\bdotnet\b|\basp\.net\b",
        "color": "#7C3AED",  # Purple
    },

    # Databases
    {
        "name": "MySQL",
        "slug": "mysql",
        "category": "database",
        "pattern": r"\bmysql\b",
        "color": "#0284C7",  # Blue
    },
    {
        "name": "PostgreSQL",
        "slug": "postgresql",
        "category": "database",
        "pattern": r"\b(postgres|postgresql)\b",
        "color": "#336791",  # Postgres Blue
    },
    {
        "name": "MongoDB",
        "slug": "mongodb",
        "category": "database",
        "pattern": r"\b(mongodb|mongo)\b",
        "color": "#16A34A",  # Forest Green
    },
    {
        "name": "Redis",
        "slug": "redis",
        "category": "database",
        "pattern": r"\bredis\b",
        "color": "#DC2626",  # Red
    },
    {
        "name": "Elasticsearch",
        "slug": "elasticsearch",
        "category": "database",
        "pattern": r"\b(elasticsearch|elastic\s*search)\b",
        "color": "#FBBF24",  # Yellow
    },

    # Cloud & DevOps
    {
        "name": "AWS",
        "slug": "aws",
        "category": "cloud_devops",
        "pattern": r"\b(aws|amazon\s*web\s*services)\b",
        "color": "#F59E0B",  # Orange
    },
    {
        "name": "Azure",
        "slug": "azure",
        "category": "cloud_devops",
        "pattern": r"\b(azure|microsoft\s*azure)\b",
        "color": "#0284C7",  # Blue
    },
    {
        "name": "GCP",
        "slug": "gcp",
        "category": "cloud_devops",
        "pattern": r"\b(gcp|google\s*cloud)\b",
        "color": "#EA4335",  # Google Red
    },
    {
        "name": "Docker",
        "slug": "docker",
        "category": "cloud_devops",
        "pattern": r"\bdocker\b",
        "color": "#0EA5E9",  # Ocean Blue
    },
    {
        "name": "Kubernetes",
        "slug": "kubernetes",
        "category": "cloud_devops",
        "pattern": r"\b(kubernetes|k8s)\b",
        "color": "#326CE5",  # K8s Blue
    },
    {
        "name": "Terraform",
        "slug": "terraform",
        "category": "cloud_devops",
        "pattern": r"\bterraform\b",
        "color": "#8B5CF6",  # Purple
    },
    {
        "name": "CI/CD",
        "slug": "cicd",
        "category": "cloud_devops",
        "pattern": r"\b(ci\/cd|ci-cd|continuous\s*integration)\b",
        "color": "#10B981",  # Emerald
    },
    {
        "name": "Linux",
        "slug": "linux",
        "category": "cloud_devops",
        "pattern": r"\blinux\b",
        "color": "#EAB308",  # Yellow
    },
    {
        "name": "Git",
        "slug": "git",
        "category": "cloud_devops",
        "pattern": r"\bgit\b",
        "color": "#F97316",  # Orange
    },
]

# API Endpoints
DEFAULT_API_URL = "https://www.arbeitnow.com/api/job-board-api"
API_TIMEOUT_SECONDS = 15
DEFAULT_FETCH_PAGES = 3
