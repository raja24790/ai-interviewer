from backend.app.deps import get_settings


async def test_interview_flow_creates_report(client):
    start_response = await client.post("/interview/start", json={"role": "general"})
    assert start_response.status_code == 200
    start_payload = start_response.json()

    session_id = start_payload["session_id"]
    token = start_payload["token"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    append_response = await client.post(
        "/stt/append",
        json={"session_id": session_id, "text": "Sample answer", "question_index": 0},
        headers=headers,
    )
    assert append_response.status_code == 200

    transcripts = [
        {"question": question, "transcript": f"Automated answer {index + 1}."}
        for index, question in enumerate(start_payload["questions"])
    ]

    finalize_response = await client.post(
        "/report/finalize",
        json={
            "session_id": session_id,
            "transcripts": transcripts,
            "attention_summary": {"focused_ratio": 0.9, "distracted_ratio": 0.1},
        },
        headers=headers,
    )
    assert finalize_response.status_code == 200

    finalize_payload = finalize_response.json()
    assert finalize_payload["session_id"] == session_id
    assert finalize_payload["pdf_url"].endswith("final_report.pdf")
    assert len(finalize_payload["questions"]) == len(transcripts)

    settings = get_settings()
    pdf_path = settings.report_dir / session_id / "final_report.pdf"
    transcript_path = settings.transcript_dir / session_id / "transcript.json"

    assert pdf_path.exists()
    assert transcript_path.exists()
