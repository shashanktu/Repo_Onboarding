import json
import requests
import streamlit as st

st.set_page_config(page_title="GitHub Repo Onboarding", layout="wide", page_icon="ValueMomentum_logo.png")

REPOS_PER_PAGE = 10
USERS_FILE = "users.json"

STYLES = """
<style>
    .main { background-color: #f0f4ff; }
    .block-container { padding: 2rem 3rem; }

    .page-title {
        font-size: 1.8rem; font-weight: 700;
        color: #2563eb; margin-bottom: 0.2rem;
    }
    .page-subtitle {
        font-size: 0.95rem; color: #64748b; margin-bottom: 1.5rem;
    }
    .login-card {
        background: #ffffff; border: 1px solid #bfdbfe;
        border-radius: 12px; padding: 2.5rem 2rem;
        max-width: 420px; margin: 4rem auto;
        box-shadow: 0 4px 20px rgba(37,99,235,0.08);
    }
    .login-title {
        font-size: 1.4rem; font-weight: 700;
        color: #2563eb; margin-bottom: 0.3rem; text-align: center;
    }
    .login-subtitle {
        font-size: 0.85rem; color: #64748b;
        text-align: center; margin-bottom: 1.5rem;
    }
    .repo-card {
        background: #ffffff; border: 1px solid #bfdbfe;
        border-radius: 10px; padding: 1rem 1.4rem;
        margin-bottom: 0.75rem; transition: box-shadow 0.2s;
    }
    .repo-card:hover { box-shadow: 0 4px 14px rgba(37,99,235,0.1); }
    .repo-name {
        font-size: 1rem; font-weight: 600;
        color: #1d4ed8; text-decoration: none;
    }
    .repo-name:hover { text-decoration: underline; }
    .repo-desc { font-size: 0.85rem; color: #64748b; margin-top: 0.4rem; }
    .repo-meta {
        display: flex; flex-wrap: wrap; gap: 1.2rem;
        font-size: 0.8rem; color: #64748b; margin-top: 0.6rem;
    }
    .repo-meta span { white-space: nowrap; }
    .repo-meta-label { color: #94a3b8; margin-right: 3px; }
    .badge {
        display: inline-block; padding: 2px 10px;
        border-radius: 12px; font-size: 0.75rem;
        font-weight: 500; margin-right: 6px;
    }
    .badge-private { background: #fee2e2; color: #dc2626; }
    .badge-public  { background: #dcfce7; color: #16a34a; }
    .badge-lang    { background: #dbeafe; color: #2563eb; }
    .divider { border: none; border-top: 1px solid #bfdbfe; margin: 1.2rem 0; }
    .pagination-info {
        font-size: 0.85rem; color: #64748b;
        text-align: center; margin-top: 0.5rem;
    }
    .user-info {
        font-size: 0.85rem; color: #64748b; text-align: right;
    }
    .stButton > button {
        background-color: #2563eb; color: #ffffff;
        border: none; border-radius: 6px;
        padding: 0.35rem 1rem; font-size: 0.85rem;
        font-weight: 500; cursor: pointer; width: 100%;
    }
    .stButton > button:hover { background-color: #1d4ed8; }
    .stButton > button:disabled { background-color: #bfdbfe; color: #93c5fd; }
    section[data-testid="stSidebar"] { display: none; }
</style>
"""

st.markdown(STYLES, unsafe_allow_html=True)


def load_users():
    with open(USERS_FILE, "r") as f:
        return json.load(f)


def authenticate(username, password):
    for user in load_users():
        if user["username"] == username and user["password"] == password:
            return user
    return None


WEBHOOK_URL = "https://github-webhook-endpoint.vercel.app/github-webhook"


def fetch_repos(pat):
    headers = {"Authorization": f"token {pat}"}
    response = requests.get(
        "https://api.github.com/user/repos?per_page=100&sort=updated&affiliation=owner",
        headers=headers,
    )
    return response


def webhook_exists(github_username, repo_name, pat):
    url = f"https://api.github.com/repos/{github_username}/{repo_name}/hooks"
    headers = {"Authorization": f"token {pat}", "Accept": "application/vnd.github+json"}
    resp = requests.get(url, headers=headers)
    if resp.status_code == 200:
        return any(h.get("config", {}).get("url") == WEBHOOK_URL for h in resp.json())
    return False


def create_webhook(github_username, repo_name, pat):
    url = f"https://api.github.com/repos/{github_username}/{repo_name}/hooks"
    headers = {"Authorization": f"token {pat}", "Accept": "application/vnd.github+json"}
    payload = {
        "name": "web",
        "active": True,
        "events": ["push", "pull_request"],
        "config": {
            "url": WEBHOOK_URL,
            "content_type": "application/json",
            "insecure_ssl": "0",
        },
    }
    return requests.post(url, headers=headers, json=payload)


def show_login():
    _, center, _ = st.columns([1, 2, 1])
    with center:
        st.image("ValueMomentum_logo.png", use_container_width=True)
        st.markdown("""
            <div style="text-align:center; margin-top:0.5rem;">
                <div class="login-title">GitHub Repo Onboarding</div>
                <div class="login-subtitle">Sign in to manage and onboard your repositories</div>
            </div>
        """, unsafe_allow_html=True)

    _, center, _ = st.columns([1, 2, 1])
    with center:
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Sign In", use_container_width=True)

        if submitted:
            user = authenticate(username, password)
            if user:
                st.session_state["user"] = user
                st.session_state["repos"] = None
                st.session_state["page"] = 1
                st.rerun()
            else:
                st.error("Invalid username or password.")


def show_dashboard():
    user = st.session_state["user"]

    header_col1, header_col2 = st.columns([8, 2])
    with header_col1:
        logo_col, title_col = st.columns([1, 6])
        with logo_col:
            st.image("ValueMomentum_logo.png", width=60)
        with title_col:
            st.markdown('<div class="page-title">GitHub Repository Onboarding</div>', unsafe_allow_html=True)
        st.markdown(
            f'<div class="page-subtitle">Logged in as <strong>{user["username"]}</strong> '
            f'— GitHub: <strong>{user["github_username"]}</strong></div>',
            unsafe_allow_html=True,
        )
    with header_col2:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Sign Out", use_container_width=True):
            st.session_state.clear()
            st.rerun()

    st.markdown('<hr class="divider">', unsafe_allow_html=True)

    if st.session_state.get("repos") is None:
        with st.spinner("Fetching repositories..."):
            response = fetch_repos(user["github_pat"])

        if response.status_code == 200:
            repos = response.json()
            if not repos:
                st.info("No repositories found for this account.")
                return
            st.session_state["repos"] = repos
            st.session_state["page"] = 1
        elif response.status_code == 404:
            st.error("GitHub user not found. Please verify the username in users.json.")
            return
        elif response.status_code == 403:
            st.error("GitHub API rate limit exceeded or invalid PAT.")
            return
        else:
            st.error(f"Failed to fetch repositories. Status code: {response.status_code}")
            return

    repos = st.session_state["repos"]
    total = len(repos)
    page = st.session_state.get("page", 1)
    total_pages = (total + REPOS_PER_PAGE - 1) // REPOS_PER_PAGE
    start = (page - 1) * REPOS_PER_PAGE
    end = start + REPOS_PER_PAGE
    page_repos = repos[start:end]

    summary_col, onboard_all_col = st.columns([8, 2])
    with summary_col:
        st.markdown(f"**{total} repositories found** — showing {start + 1} to {min(end, total)}")
    with onboard_all_col:
        if st.button("Onboard All Repos", use_container_width=True):
            st.session_state["onboard_all"] = True
            st.rerun()

    if st.session_state.get("onboard_all"):
        st.session_state["onboard_all"] = False
        progress_bar = st.progress(0, text="Starting onboarding...")
        status_placeholder = st.empty()
        onboarded = st.session_state.setdefault("onboarded", set())
        webhook_status = st.session_state.setdefault("webhook_status", {})

        for i, repo in enumerate(repos):
            repo_name = repo["name"]
            progress_bar.progress((i + 1) / total, text=f"Processing {repo_name} ({i + 1}/{total})")
            if webhook_exists(user["github_username"], repo_name, user["github_pat"]):
                onboarded.add(repo["id"])
                webhook_status[repo["id"]] = "already_exists"
            else:
                result = create_webhook(user["github_username"], repo_name, user["github_pat"])
                if result.status_code in (200, 201):
                    onboarded.add(repo["id"])
                    webhook_status[repo["id"]] = "added"
                else:
                    webhook_status[repo["id"]] = "failed"

        progress_bar.progress(1.0, text="Onboarding complete.")
        status_placeholder.success(f"Onboarding complete for all {total} repositories.")
        st.rerun()

    st.markdown("")

    for repo in page_repos:
        visibility = "Private" if repo["private"] else "Public"
        badge_class = "badge-private" if repo["private"] else "badge-public"
        lang = repo.get("language") or "N/A"
        stars = repo.get("stargazers_count", 0)
        forks = repo.get("forks_count", 0)
        watchers = repo.get("watchers_count", 0)
        open_issues = repo.get("open_issues_count", 0)
        default_branch = repo.get("default_branch", "N/A")
        license_name = (repo.get("license") or {}).get("spdx_id") or "No License"
        updated_at = repo.get("updated_at", "")[:10]
        description = repo.get("description") or "No description provided."

        with st.container():
            info_col, btn_col = st.columns([9, 1.4])
            with info_col:
                st.markdown(f"""
                    <div class="repo-card">
                        <div style="display:flex; align-items:center; gap:0.5rem; flex-wrap:wrap;">
                            <a class="repo-name" href="{repo['html_url']}" target="_blank">{repo['name']}</a>
                            <span class="badge {badge_class}">{visibility}</span>
                            <span class="badge badge-lang">{lang}</span>
                            <span class="badge" style="background:#f0fdf4;color:#15803d;">Branch: {default_branch}</span>
                            <span class="badge" style="background:#fef9c3;color:#854d0e;">{license_name}</span>
                        </div>
                        <div class="repo-desc">{description}</div>
                        <div class="repo-meta">
                            <span><span class="repo-meta-label">Stars</span>{stars}</span>
                            <span><span class="repo-meta-label">Forks</span>{forks}</span>
                            <span><span class="repo-meta-label">Watchers</span>{watchers}</span>
                            <span><span class="repo-meta-label">Open Issues</span>{open_issues}</span>
                            <span><span class="repo-meta-label">Updated</span>{updated_at}</span>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
            with btn_col:
                st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)
                already_onboarded = repo["id"] in st.session_state.get("onboarded", set())
                wh_status = st.session_state.get("webhook_status", {}).get(repo["id"])

                if wh_status == "added":
                    st.markdown("<div style='color:#16a34a;font-size:0.8rem;font-weight:600;text-align:center;padding-top:6px;'>Webhook Added</div>", unsafe_allow_html=True)
                elif wh_status == "already_exists":
                    st.markdown("<div style='color:#2563eb;font-size:0.8rem;font-weight:600;text-align:center;padding-top:6px;'>Already Exists</div>", unsafe_allow_html=True)
                elif wh_status == "failed":
                    st.markdown("<div style='color:#dc2626;font-size:0.8rem;font-weight:600;text-align:center;padding-top:6px;'>Failed</div>", unsafe_allow_html=True)
                else:
                    btn_label = "Onboarded" if already_onboarded else "Onboard"
                    if st.button(btn_label, key=f"onboard_{repo['id']}", use_container_width=True, disabled=already_onboarded):
                        with st.spinner(f"Creating webhook for {repo['name']}..."):
                            if webhook_exists(user["github_username"], repo["name"], user["github_pat"]):
                                st.session_state.setdefault("onboarded", set()).add(repo["id"])
                                st.session_state.setdefault("webhook_status", {})[repo["id"]] = "already_exists"
                            else:
                                result = create_webhook(user["github_username"], repo["name"], user["github_pat"])
                                if result.status_code in (200, 201):
                                    st.session_state.setdefault("onboarded", set()).add(repo["id"])
                                    st.session_state.setdefault("webhook_status", {})[repo["id"]] = "added"
                                elif result.status_code == 404:
                                    st.error(f"Repository '{repo['name']}' not found or insufficient permissions.")
                                else:
                                    st.session_state.setdefault("webhook_status", {})[repo["id"]] = "failed"
                                    st.error(f"Failed to create webhook. Status: {result.status_code} — {result.json().get('message', '')}")
                        st.rerun()


    st.markdown('<hr class="divider">', unsafe_allow_html=True)

    nav_col1, nav_col2, nav_col3 = st.columns([1, 4, 1])
    with nav_col1:
        if st.button("Previous", disabled=(page <= 1), use_container_width=True):
            st.session_state["page"] -= 1
            st.rerun()
    with nav_col2:
        st.markdown(
            f'<div class="pagination-info">Page {page} of {total_pages}</div>',
            unsafe_allow_html=True,
        )
    with nav_col3:
        if st.button("Next", disabled=(page >= total_pages), use_container_width=True):
            st.session_state["page"] += 1
            st.rerun()


if "user" not in st.session_state:
    show_login()
else:
    show_dashboard()
