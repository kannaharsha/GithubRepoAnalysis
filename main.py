import requests
import json
from dotenv import load_dotenv
import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st

load_dotenv()
GITHUB_PAT = os.getenv("GITHUB_PAT")
headers = {"Authorization": f"token {GITHUB_PAT}"}

st.title("GitHub Repository Analyzer")

# Input repo URL from user
repo_url_input = st.text_input("Enter GitHub Repository URL (e.g., https://github.com/tensorflow/tensorflow):")

if repo_url_input:
    try:
        # Extract owner and repo name
        parts = repo_url_input.strip().split("/")
        repo_owner = parts[-2]
        repo_name = parts[-1]
        st.subheader(f"Analyzing Repository: {repo_owner}/{repo_name}")

        # --- Repository Info ---
        repo_api_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}"
        repo_response = requests.get(repo_api_url, headers=headers)
        if repo_response.status_code != 200:
            st.error(f"Error fetching repository info: {repo_response.status_code}")
        else:
            repo_data = repo_response.json()
            st.write("**Repository Name:**", repo_data["name"])
            st.write("**Full Name:**", repo_data["full_name"])
            st.write("**Description:**", repo_data["description"])
            st.write("**Stars:**", repo_data["stargazers_count"])
            st.write("**Forks:**", repo_data["forks_count"])
            st.write("**Watchers:**", repo_data["watchers_count"])
            st.write("**Open Issues:**", repo_data["open_issues_count"])
            st.write("**Primary Language:**", repo_data["language"])
            st.write("**Created At:**", repo_data["created_at"])
            st.write("**Last Updated:**", repo_data["updated_at"])

        # --- Commits ---
        commits_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/commits?per_page=100"
        commits_response = requests.get(commits_url, headers=headers)
        commits_data = commits_response.json()
        commits_list = []
        for commit in commits_data:
            commits_list.append({
                "author_name": commit["commit"]["author"]["name"] if commit["commit"]["author"] else "Unknown",
                "commit_date": commit["commit"]["author"]["date"],
                "message": commit["commit"]["message"]
            })
        commits_df = pd.DataFrame(commits_list)
        commits_df['commit_date'] = pd.to_datetime(commits_df['commit_date'])
        commits_df['year'] = commits_df['commit_date'].dt.year
        commits_df['month'] = commits_df['commit_date'].dt.month
        commits_df['week'] = commits_df['commit_date'].dt.isocalendar().week

        # Commits per month and week
        monthly_commits = commits_df.groupby(['year','month']).size().reset_index(name='commit_count')
        weekly_commits = commits_df.groupby(['year','week']).size().reset_index(name='commit_count')

        st.header("Commits Over Time")
        st.subheader("Monthly Commits")
        st.line_chart(monthly_commits.set_index('month')['commit_count'])
        st.subheader("Weekly Commits")
        st.line_chart(weekly_commits.set_index('week')['commit_count'])

        # --- Contributors ---
        contributors_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/contributors?per_page=100"
        contributors_response = requests.get(contributors_url, headers=headers)
        contributors_data = contributors_response.json()
        contributors_list = []
        for contrib in contributors_data:
            contributors_list.append({
                "user_name": contrib.get("login", "Unknown"),
                "contributions": contrib.get("contributions", 0)
            })
        contributors_df = pd.DataFrame(contributors_list)
        contributors_df['contrib_percentage'] = (contributors_df['contributions'] / contributors_df['contributions'].sum()) * 100
        top_contributors = contributors_df.sort_values(by='contributions', ascending=False).head(10)

        st.header("Top Contributors")
        st.bar_chart(top_contributors.set_index('user_name')['contributions'])

        # --- Languages ---
        languages_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/languages"
        languages_response = requests.get(languages_url, headers=headers)
        languages_data = languages_response.json()

        languages_list = [{"language": lang, "bytes_code": size} for lang, size in languages_data.items()]
        languages_df = pd.DataFrame(languages_list)

        languages_df['percentage'] = (languages_df['bytes_code'] / languages_df['bytes_code'].sum()) * 100

        languages_df = languages_df.sort_values(by='percentage', ascending=False)

        st.header("Languages Used")
        st.dataframe(languages_df[['language', 'percentage']])

        st.subheader("Languages Usage Chart")
        st.bar_chart(languages_df.set_index('language')['percentage'])

        pulls_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/pulls?state=all&per_page=100"
        pulls_response = requests.get(pulls_url, headers=headers)
        pulls_data = pulls_response.json()
        pulls_df = pd.DataFrame(pulls_data)
        st.header("Pull Requests Info")
        st.write("Total Pull Requests:", len(pulls_df))
        if not pulls_df.empty:
            pulls_state_count = pulls_df['state'].value_counts()
            st.subheader("Pull Requests by State")
            st.bar_chart(pulls_state_count)

        # --- Issues ---
        issues_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/issues?state=all&per_page=100"
        issues_response = requests.get(issues_url, headers=headers)
        issues_data = issues_response.json()
        issues_list = [issue for issue in issues_data if 'pull_request' not in issue]  # Exclude PRs
        issues_df = pd.DataFrame(issues_list)
        st.header("Issues Info")
        st.write("Total Issues:", len(issues_df))
        if not issues_df.empty:
            issues_state_count = issues_df['state'].value_counts()
            st.subheader("Issues by State")
            st.bar_chart(issues_state_count)

    except Exception as e:
        st.error(f"Error: {e}")
