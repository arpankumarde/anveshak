import os

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from github import Github
from github.GithubException import GithubException
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from pydantic import BaseModel

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

token = os.getenv("GITHUB_TOKEN")
github = Github(token) if token else Github()
sendgrid = SendGridAPIClient(os.getenv("SENDGRID_API_KEY", ""))


@app.get("/users/{username}/repos")
def list_user_repos(username: str) -> list[dict[str, str | None]]:
    """
    Return a basic list of public GitHub repositories for the given user.
    """

    try:
        user = github.get_user(username)
        repos = user.get_repos()
        return [{"name": repo.name, "html_url": repo.html_url} for repo in repos]
    except GithubException as exc:
        if exc.status == 404:
            raise HTTPException(status_code=404, detail="GitHub user not found")
        raise HTTPException(
            status_code=exc.status or 500,
            detail=f"Failed to fetch repositories: {exc.data.get('message', str(exc))}",
        )


class CreateIssueRequest(BaseModel):
    title: str
    description: str


@app.post("/create-issue")
async def create_issue(payload: CreateIssueRequest) -> dict[str, str | int]:
    """
    Create a GitHub issue in the specified repository.

    Args:
        payload: Request body containing owner, repo, title, and description (markdown)

    Returns:
        Dictionary with issue URL and issue number
    """
    if not token:
        raise HTTPException(status_code=500, detail="GITHUB_TOKEN is not configured")

    try:
        owner = os.getenv("REPO_OWNER")
        repo_name = os.getenv("REPO_NAME")
        repository = github.get_repo(f"{owner}/{repo_name}")
        print(repository)
        issue = repository.create_issue(title=payload.title, body=payload.description)
        print(issue)
        return {
            "issue_url": issue.html_url,
            "issue_number": issue.number,
            "detail": "Issue created successfully",
        }
    except GithubException as exc:
        if exc.status == 404:
            raise HTTPException(
                status_code=404,
                detail=f"Repository '{payload.owner}/{payload.repo}' not found",
            )
        raise HTTPException(
            status_code=exc.status or 500,
            detail=f"Failed to create issue: {exc.data.get('message', str(exc))}",
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500, detail=f"Failed to create issue: {exc}"
        ) from exc


class EmailRequest(BaseModel):
    subject: str = "Sending with Twilio SendGrid is Fun"
    html_content: str = "<strong>and easy to do anywhere, even with Python</strong>"


@app.post("/send-email")
async def send_email(payload: EmailRequest) -> dict[str, str]:
    if not os.getenv("SENDGRID_API_KEY"):
        raise HTTPException(
            status_code=500, detail="SENDGRID_API_KEY is not configured"
        )

    from_email = os.getenv("FROM_EMAIL", "from_email@example.com")
    to_email = os.getenv("TO_EMAIL", "from_email@example.com")
    message = Mail(
        from_email=from_email,
        to_emails=to_email,
        subject=payload.subject,
        html_content=payload.html_content,
    )

    try:
        response = sendgrid.send(message)
        return {
            "status_code": str(response.status_code),
            "detail": "Email sent",
        }
    except Exception as exc:
        raise HTTPException(
            status_code=500, detail=f"Failed to send email: {exc}"
        ) from exc


class WhatsappMessageRequest(BaseModel):
    message: str
    message_type: str = "text"


@app.post("/send-whatsapp-message")
async def send_whatsapp_message(
    payload: WhatsappMessageRequest,
) -> dict[str, str | dict]:
    """
    Send a WhatsApp message using waplify.io API.

    Args:
        payload: Request body containing message and message_type (optional)
                waba_phone_id and to are read from environment variables

    Returns:
        Dictionary with response status and detail
    """
    waplify_token = os.getenv("WAPLIFY_AUTH_TOKEN")
    waba_phone_id = os.getenv("WABA_PHONE_ID")
    to_number = os.getenv("WHATSAPP_TO_NUMBER")

    if not waplify_token:
        raise HTTPException(
            status_code=500, detail="WAPLIFY_AUTH_TOKEN is not configured"
        )
    if not waba_phone_id:
        raise HTTPException(status_code=500, detail="WABA_PHONE_ID is not configured")
    if not to_number:
        raise HTTPException(
            status_code=500, detail="WHATSAPP_TO_NUMBER is not configured"
        )

    url = "https://app.waplify.io/api/whatsapp/send-message"
    headers = {
        "authorization": f"Bearer {waplify_token}",
        "content-type": "application/json",
    }
    data = {
        "waba_phone_id": waba_phone_id,
        "to": to_number,
        "message": payload.message,
        "message_type": payload.message_type,
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=data)
            response.raise_for_status()
            response_data = response.json() if response.content else {}
            return {
                "status_code": str(response.status_code),
                "detail": "WhatsApp message sent successfully",
                "response": response_data,
            }
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=exc.response.status_code,
            detail=f"Failed to send WhatsApp message: {exc.response.text}",
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500, detail=f"Failed to send WhatsApp message: {exc}"
        ) from exc
