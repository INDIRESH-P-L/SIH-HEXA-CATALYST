import asyncio
import httpx

async def test_flow():
    async with httpx.AsyncClient(base_url="http://127.0.0.1:8000/api/v1") as client:
        print("Registering...")
        resp = await client.post("/auth/register", json={
            "email": "testflow@example.com",
            "password": "Password123!",
            "full_name": "Test Flow User",
            "job_role_code": "STAT_OFF_1"
        })
        if resp.status_code != 201:
            print("Register failed:", resp.text)
            return
        
        token = resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        print("Fetching /auth/me...")
        resp = await client.get("/auth/me", headers=headers)
        me_data = resp.json()
        print("onboarded:", me_data["onboarded"])
        print("initial_assessment_completed:", me_data["profile"]["initial_assessment_completed"])

        print("\nUpdating profile (Step 1)...")
        resp = await client.patch("/profiles/me", headers=headers, json={"years_experience": 5})
        print(resp.status_code)

        print("\nDeclaring competencies (Step 2)...")
        # Find some competencies first
        resp = await client.get("/competencies", headers=headers)
        comps = resp.json()[:2]
        decls = [{"competency_id": c["id"], "level": 2} for c in comps]
        resp = await client.post("/competencies/me/declare", headers=headers, json={"declarations": decls})
        print("Declare status:", resp.status_code)

        print("\nFetching /auth/me after declaration...")
        resp = await client.get("/auth/me", headers=headers)
        me_data = resp.json()
        print("onboarded:", me_data["onboarded"])
        print("initial_assessment_completed:", me_data["profile"]["initial_assessment_completed"])

        print("\nFetching initial topics (Step 3)...")
        resp = await client.get("/assessments/initial/topics", headers=headers)
        if resp.status_code != 200:
            print("Topics failed:", resp.text)
            return
        topics = resp.json()
        print("Topics:", topics["total_questions"])

        print("\nStarting initial assessment...")
        resp = await client.post("/assessments/initial/start", headers=headers)
        if resp.status_code != 200:
            print("Start failed:", resp.text)
            return
        start_data = resp.json()
        print("Started assessments:", len(start_data["assessments"]))
        
        assessment_ids = []
        for a in start_data["assessments"]:
            aid = a["assessment_id"]
            assessment_ids.append(aid)
            # Answer one question
            resp = await client.get(f"/assessments/{aid}", headers=headers)
            q = resp.json()["questions"][0]
            resp = await client.post(f"/assessments/{aid}/answer", headers=headers, json={"question_id": q["id"], "selected_index": 1})
            
            # Submit
            resp = await client.post(f"/assessments/{aid}/submit", headers=headers)
            print("Submitted", aid, resp.status_code)

        print("\nCompleting initial assessment...")
        resp = await client.post("/assessments/initial/complete", headers=headers, json={"assessment_ids": assessment_ids})
        if resp.status_code != 200:
            print("Complete failed:", resp.text)
            return
        print("Overall Score:", resp.json()["overall_score"])

        print("\nFetching /auth/me after completion...")
        resp = await client.get("/auth/me", headers=headers)
        me_data = resp.json()
        print("initial_assessment_completed:", me_data["profile"]["initial_assessment_completed"])

asyncio.run(test_flow())
