"""Automated tests for Interview Lab routes: Tags, Questions, Experiences, Flashcards, and Excel Export."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_tags_crud(app_client: AsyncClient):
    """Test creating, listing, and deleting tags."""
    # 1. Create a tag
    payload = {"name": "Dynamic Programming", "color": "#c25e2e"}
    res = await app_client.post("/api/interview-lab/tags", json=payload)
    assert res.status_code == 201
    tag = res.json()
    assert tag["name"] == "Dynamic Programming"
    assert tag["color"] == "#c25e2e"
    tag_id = tag["id"]

    # 2. List tags
    res_list = await app_client.get("/api/interview-lab/tags")
    assert res_list.status_code == 200
    tags = res_list.json()
    assert len(tags) >= 1
    assert any(t["name"] == "Dynamic Programming" for t in tags)

    # 3. Delete tag
    res_del = await app_client.delete(f"/api/interview-lab/tags/{tag_id}")
    assert res_del.status_code == 204


@pytest.mark.asyncio
async def test_questions_crud(app_client: AsyncClient):
    """Test creating, querying with filters, updating, and deleting LeetCode questions."""
    # 1. Create a question
    payload = {
        "title": "Two Sum",
        "description": "Given an array of integers, return indices of two numbers that add up to target.",
        "difficulty": "Easy",
        "topic": "Array / Hash Map",
        "company": "Google",
        "role": "Software Engineer",
        "solutions": [
            {
                "label": "One-Pass Hash Table",
                "code": "def twoSum(nums, target): ...",
                "language": "python",
                "explanation": "Iterate while checking diff in hash map",
                "time_complexity": "O(N)",
                "space_complexity": "O(N)",
                "tags": ["Hash Table"],
            }
        ],
        "links": [{"label": "LeetCode Problem", "url": "https://leetcode.com/problems/two-sum/"}],
        "tags": ["Array", "Hash Table"],
        "notes": "Always check for negative target numbers",
    }
    res = await app_client.post("/api/interview-lab/questions", json=payload)
    assert res.status_code == 201
    q = res.json()
    assert q["title"] == "Two Sum"
    assert q["difficulty"] == "Easy"
    assert len(q["solutions"]) == 1
    assert q["solutions"][0]["time_complexity"] == "O(N)"
    question_id = q["id"]

    # 2. List questions with filter
    res_list = await app_client.get("/api/interview-lab/questions?company=Google&difficulty=Easy")
    assert res_list.status_code == 200
    questions = res_list.json()
    assert len(questions) == 1
    assert questions[0]["title"] == "Two Sum"

    # 3. Update question
    res_upd = await app_client.put(
        f"/api/interview-lab/questions/{question_id}",
        json={"notes": "Updated note with edge case handling"},
    )
    assert res_upd.status_code == 200
    assert res_upd.json()["notes"] == "Updated note with edge case handling"

    # 4. Delete question
    res_del = await app_client.delete(f"/api/interview-lab/questions/{question_id}")
    assert res_del.status_code == 204


@pytest.mark.asyncio
async def test_experiences_crud(app_client: AsyncClient):
    """Test logging interview loops with pipeline rounds, Q&As, and self-ratings."""
    # 1. Create an experience
    payload = {
        "company": "Amazon",
        "role": "Software Development Engineer II",
        "rating": 8,
        "outcome": "Offer Received",
        "interview_process": [
            {"round_number": 1, "round_type": "OA", "description": "2 HackerRank questions (90 min)"},
            {"round_number": 2, "round_type": "TA", "description": "Live CoderPad graph BFS question"},
            {"round_number": 3, "round_type": "SD", "description": "Design distributed inventory locker"},
        ],
        "questions_asked": [
            {
                "question": "Implement an LRU cache with O(1) get and put.",
                "answer": "Used Doubly Linked List with Hash Map for O(1) operations.",
                "category": "Technical",
                "links": [],
            }
        ],
        "overall_notes": "Focused heavily on Leadership Principles for each round.",
        "tags": ["Amazon", "Offer"],
    }
    res = await app_client.post("/api/interview-lab/experiences", json=payload)
    assert res.status_code == 201
    exp = res.json()
    assert exp["company"] == "Amazon"
    assert exp["rating"] == 8
    assert len(exp["interview_process"]) == 3
    assert len(exp["questions_asked"]) == 1
    exp_id = exp["id"]

    # 2. List experiences with filter
    res_list = await app_client.get("/api/interview-lab/experiences?company=Amazon&min_rating=7")
    assert res_list.status_code == 200
    exps = res_list.json()
    assert len(exps) == 1
    assert exps[0]["company"] == "Amazon"

    # 3. Delete experience
    res_del = await app_client.delete(f"/api/interview-lab/experiences/{exp_id}")
    assert res_del.status_code == 204


@pytest.mark.asyncio
async def test_flashcards_crud_and_study(app_client: AsyncClient):
    """Test creating manual revision flashcards and retrieving study deck."""
    # 1. Create flashcard
    payload = {
        "front": "What is the time complexity of Floyd's Heap Construction (heapify)?",
        "back": "O(N) linear time because the sum of heights of all nodes converges to 2N.",
        "company": "Google",
        "difficulty": "Medium",
        "tags": ["Heap", "Data Structures"],
    }
    res = await app_client.post("/api/interview-lab/flashcards", json=payload)
    assert res.status_code == 201
    card = res.json()
    assert card["front"].startswith("What is the time complexity")
    card_id = card["id"]

    # 2. Get study deck
    res_study = await app_client.get("/api/interview-lab/flashcards/study?count=10")
    assert res_study.status_code == 200
    deck = res_study.json()
    assert len(deck) >= 1
    assert deck[0]["id"] == card_id

    # 3. Delete flashcard
    res_del = await app_client.delete(f"/api/interview-lab/flashcards/{card_id}")
    assert res_del.status_code == 204


@pytest.mark.asyncio
async def test_export_interview_lab_excel(app_client: AsyncClient):
    """Test generating styled Excel spreadsheet export from Interview Lab data."""
    # Seed a question and an experience
    await app_client.post(
        "/api/interview-lab/questions",
        json={"title": "LRU Cache", "difficulty": "Medium", "company": "Stripe"},
    )
    await app_client.post(
        "/api/interview-lab/experiences",
        json={"company": "Stripe", "role": "Backend Engineer", "rating": 9},
    )

    # Request Excel export
    res = await app_client.get("/api/interview-lab/export/excel?company=Stripe")
    assert res.status_code == 200
    assert (
        res.headers["content-type"]
        == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    assert len(res.content) > 1000  # Valid binary Excel file
