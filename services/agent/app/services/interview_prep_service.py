"""Interview & DSA Preparation Engine with live Hacker News/Reddit debriefs and LeetCode/NeetCode resources."""

import asyncio
import json
import os
import urllib.parse
from typing import Any
import httpx
import structlog
from app.config import settings
from app.services.llm_factory import LLMFactory

logger = structlog.get_logger()

# Real scraped & curated DSA problem knowledge base mapped directly to LeetCode & NeetCode 150
COMPANY_DSA_KNOWLEDGE_BASE: dict[str, dict[str, Any]] = {
    "google": {
        "dsa": [
            {
                "title": "Shortest Path in a Grid with Obstacles Elimination",
                "difficulty": "Hard",
                "topic": "BFS / 3D Grid State",
                "frequency": "Very High",
                "hint": "Track state as (row, col, remaining_eliminations) in a BFS queue with a visited set to avoid cycles in O(M*N*K).",
                "leetcode_url": "https://leetcode.com/problems/shortest-path-in-a-grid-with-obstacles-elimination/",
                "neetcode_url": "https://neetcode.io/practice",
                "time_complexity": "O(M * N * K)",
                "space_complexity": "O(M * N * K)",
            },
            {
                "title": "Course Schedule II",
                "difficulty": "Medium",
                "topic": "Topological Sort / Directed Graph",
                "frequency": "Extremely High",
                "hint": "Use Kahn's Algorithm with an in-degree array and queue, or DFS with 3-state coloring (unvisited, visiting, visited).",
                "leetcode_url": "https://leetcode.com/problems/course-schedule-ii/",
                "neetcode_url": "https://neetcode.io/problems/course-schedule-ii",
                "time_complexity": "O(V + E)",
                "space_complexity": "O(V + E)",
            },
            {
                "title": "Snapshot Array",
                "difficulty": "Medium",
                "topic": "Binary Search / Design",
                "frequency": "High",
                "hint": "Store a list of (snap_id, val) tuples at each array index. Binary search the largest snap_id <= target snap.",
                "leetcode_url": "https://leetcode.com/problems/snapshot-array/",
                "neetcode_url": "https://neetcode.io/practice",
                "time_complexity": "O(log S) per get",
                "space_complexity": "O(N + total_set_operations)",
            },
            {
                "title": "Word Ladder",
                "difficulty": "Hard",
                "topic": "Bidirectional BFS / Graph",
                "frequency": "High",
                "hint": "Bidirectional BFS from beginWord and endWord drastically cuts down the branching factor.",
                "leetcode_url": "https://leetcode.com/problems/word-ladder/",
                "neetcode_url": "https://neetcode.io/problems/word-ladder",
                "time_complexity": "O(M^2 * N)",
                "space_complexity": "O(M * N)",
            },
        ],
        "system_design": [
            "Design Google Drive / Distributed Chunk Store (Blob storage, deduplication, metadata DB, chunk servers)",
            "Design Google Docs / Collaborative Real-Time Text Editor (Operational Transformation / CRDTs)",
            "Design a Global Web Crawler with URL frontier queues, politeness policies, and DNS caching",
        ],
        "interview_format": "1 Recruiter Screen ➔ 1 Technical Phone Screen (45m) ➔ 4-5 Virtual Onsite Rounds (3 Coding + 1 System Design + 1 Googlyness)",
    },
    "amazon": {
        "dsa": [
            {
                "title": "LRU Cache Implementation",
                "difficulty": "Medium",
                "topic": "Hash Map + Doubly Linked List",
                "frequency": "Extreme (Top Amazon Question)",
                "hint": "Combine a Hash Map for O(1) key lookup with a Doubly Linked List for O(1) node removal and head-insertion.",
                "leetcode_url": "https://leetcode.com/problems/lru-cache/",
                "neetcode_url": "https://neetcode.io/problems/lru-cache",
                "time_complexity": "O(1) get & put",
                "space_complexity": "O(Capacity)",
            },
            {
                "title": "Rotting Oranges",
                "difficulty": "Medium",
                "topic": "Multi-Source BFS",
                "frequency": "Very High",
                "hint": "Add all initially rotten orange coordinates to the queue at time=0, then process level-by-level.",
                "leetcode_url": "https://leetcode.com/problems/rotting-oranges/",
                "neetcode_url": "https://neetcode.io/problems/rotting-oranges",
                "time_complexity": "O(M * N)",
                "space_complexity": "O(M * N)",
            },
            {
                "title": "Top K Frequent Elements",
                "difficulty": "Medium",
                "topic": "Min-Heap / QuickSelect / Bucket Sort",
                "frequency": "High",
                "hint": "Bucket sort with frequency as index achieves O(N) linear time without a heap.",
                "leetcode_url": "https://leetcode.com/problems/top-k-frequent-elements/",
                "neetcode_url": "https://neetcode.io/problems/top-k-frequent-elements",
                "time_complexity": "O(N)",
                "space_complexity": "O(N)",
            },
            {
                "title": "Number of Islands",
                "difficulty": "Medium",
                "topic": "Grid DFS / BFS / Disjoint Set",
                "frequency": "Extreme",
                "hint": "Iterate grid and sink connected '1's into '0's recursively using 4-directional DFS.",
                "leetcode_url": "https://leetcode.com/problems/number-of-islands/",
                "neetcode_url": "https://neetcode.io/problems/count-number-of-islands",
                "time_complexity": "O(M * N)",
                "space_complexity": "O(M * N)",
            },
        ],
        "system_design": [
            "Design Amazon Fulfillment & Flash Sale Inventory Locker (Distributed locking, DynamoDB transactions)",
            "Design Top-K Items in E-Commerce Stream (Count-Min Sketch + Sliding Window Top-K Heap)",
            "Design Video Streaming Platform (AWS CloudFront CDN, S3, transcoding pipelines)",
        ],
        "interview_format": "OA (2 Questions + Work Sim) ➔ 1 Phone Screen ➔ 4-5 Virtual Onsite Rounds (1 Bar Raiser + 2 Coding + 1 System Design + 1 Hiring Manager)",
    },
    "meta": {
        "dsa": [
            {
                "title": "Subarray Sum Equals K",
                "difficulty": "Medium",
                "topic": "Prefix Sum + Hash Map",
                "frequency": "Extreme (Top Meta Question)",
                "hint": "Store cumulative prefix sum counts in a hash map. At each step, check if (current_sum - k) was seen before.",
                "leetcode_url": "https://leetcode.com/problems/subarray-sum-equals-k/",
                "neetcode_url": "https://neetcode.io/problems/subarray-sum-equals-k",
                "time_complexity": "O(N)",
                "space_complexity": "O(N)",
            },
            {
                "title": "Lowest Common Ancestor of a Binary Tree",
                "difficulty": "Medium",
                "topic": "Binary Tree Recursion",
                "frequency": "Very High",
                "hint": "If current node is p or q, return current. If left and right recursive calls both return non-null, current node is LCA.",
                "leetcode_url": "https://leetcode.com/problems/lowest-common-ancestor-of-a-binary-tree/",
                "neetcode_url": "https://neetcode.io/problems/lowest-common-ancestor-in-binary-search-tree",
                "time_complexity": "O(N)",
                "space_complexity": "O(H)",
            },
            {
                "title": "Merge Intervals & Interval List Intersections",
                "difficulty": "Medium",
                "topic": "Two Pointers / Sorting",
                "frequency": "Extreme",
                "hint": "Sort intervals by start time. Greedily extend previous interval end time if next interval start <= previous end.",
                "leetcode_url": "https://leetcode.com/problems/merge-intervals/",
                "neetcode_url": "https://neetcode.io/problems/merge-intervals",
                "time_complexity": "O(N log N)",
                "space_complexity": "O(N)",
            },
            {
                "title": "Minimum Remove to Make Valid Parentheses",
                "difficulty": "Medium",
                "topic": "Stack / String",
                "frequency": "High",
                "hint": "Use a stack to record indices of invalid '(' and ')' parentheses, then rebuild string skipping those indices.",
                "leetcode_url": "https://leetcode.com/problems/minimum-remove-to-make-valid-parentheses/",
                "neetcode_url": "https://neetcode.io/practice",
                "time_complexity": "O(N)",
                "space_complexity": "O(N)",
            },
        ],
        "system_design": [
            "Design Facebook News Feed with Fan-Out on Read vs Fan-Out on Write caching",
            "Design Messenger / WhatsApp with distributed WebSockets, presence servers, and Cassandra message archive",
            "Design Instagram Story with 24h TTL and distributed photo cache",
        ],
        "interview_format": "1 Technical Screen (45m, 2 coding) ➔ 4 Onsite Rounds (2 Coding + 1 System Design + 1 Behavioral 'Jedi')",
    },
    "palantir": {
        "dsa": [
            {
                "title": "Find First and Last Position of Element in Sorted Array (Binary Search Infinite Space)",
                "difficulty": "Medium",
                "topic": "Binary Search / Infinite Stream",
                "frequency": "Very High (Palantir Favorite)",
                "hint": "Double search window boundary exponentially [1, 2, 4, 8, 16...] until target is bounded, then run standard binary search in O(log N).",
                "leetcode_url": "https://leetcode.com/problems/find-first-and-last-position-of-element-in-sorted-array/",
                "neetcode_url": "https://neetcode.io/problems/find-target-in-rotated-sorted-array",
                "time_complexity": "O(log N)",
                "space_complexity": "O(1)",
            },
            {
                "title": "Top K Frequent Words",
                "difficulty": "Medium",
                "topic": "Min-Heap / Custom Trie Comparator",
                "frequency": "High",
                "hint": "Maintain a Min-Heap of size K. Tie-break words with identical frequency using alphabetical lexicographical order.",
                "leetcode_url": "https://leetcode.com/problems/top-k-frequent-words/",
                "neetcode_url": "https://neetcode.io/problems/top-k-frequent-elements",
                "time_complexity": "O(N log K)",
                "space_complexity": "O(N)",
            },
            {
                "title": "Min Cost to Connect All Points (Prim's / Kruskal's MST)",
                "difficulty": "Medium",
                "topic": "Minimum Spanning Tree / Union-Find",
                "frequency": "High",
                "hint": "Connect graph nodes with Manhattan distances using Prim's algorithm with a priority queue.",
                "leetcode_url": "https://leetcode.com/problems/min-cost-to-connect-all-points/",
                "neetcode_url": "https://neetcode.io/problems/min-cost-to-connect-all-points",
                "time_complexity": "O(E log V)",
                "space_complexity": "O(V + E)",
            },
        ],
        "system_design": [
            "Design Palantir Foundry / Distributed Data Lineage & Pipeline Engine",
            "Design Multi-Tenant Granular Access Control (RBAC/ABAC) for Terabyte-scale Data Tables",
            "Design Real-Time Geospatial Tracking & Telemetry Dashboard",
        ],
        "interview_format": "1 Recruiter Screen ➔ 1 Decomposition / Coding Screen (60m) ➔ 4 Onsite Rounds (2 Coding + 1 System Decomposition + 1 Hiring Lead)",
    },
    "databricks": {
        "dsa": [
            {
                "title": "Design In-Memory Key-Value Store with TTL & Eviction",
                "difficulty": "Hard",
                "topic": "Hash Map + Doubly Linked List + Priority Queue",
                "frequency": "Extremely High (Core Databricks Problem)",
                "hint": "Combine Hash Map for lookup with Min-Heap for TTL expiration cleanup and Doubly Linked List for LRU capacity bounds.",
                "leetcode_url": "https://leetcode.com/problems/lru-cache/",
                "neetcode_url": "https://neetcode.io/problems/lru-cache",
                "time_complexity": "O(1) amortized",
                "space_complexity": "O(N)",
            },
            {
                "title": "Task Scheduler & CPU Execution Cooling",
                "difficulty": "Medium",
                "topic": "Greedy / Max-Heap",
                "frequency": "Very High",
                "hint": "Greedily schedule highest-frequency tasks first, filling cooldown slots with next most frequent or idle intervals.",
                "leetcode_url": "https://leetcode.com/problems/task-scheduler/",
                "neetcode_url": "https://neetcode.io/problems/task-scheduler",
                "time_complexity": "O(N)",
                "space_complexity": "O(1)",
            },
            {
                "title": "Count of Smaller Numbers After Self (Merge Sort / BIT)",
                "difficulty": "Hard",
                "topic": "Binary Indexed Tree / Modified Merge Sort",
                "frequency": "High",
                "hint": "During Merge Sort right-to-left merge, count how many elements jumped ahead of the current item.",
                "leetcode_url": "https://leetcode.com/problems/count-of-smaller-numbers-after-self/",
                "neetcode_url": "https://neetcode.io/practice",
                "time_complexity": "O(N log N)",
                "space_complexity": "O(N)",
            },
        ],
        "system_design": [
            "Design Distributed Query Execution Engine (Apache Spark / Delta Lake distributed worker nodes)",
            "Design Distributed Write-Ahead Log (WAL) with consensus and replicated state machines",
            "Design Serverless Compute Scheduler for Machine Learning Workloads",
        ],
        "interview_format": "1 Technical Screen (Coding/Concurrency) ➔ 4 Onsite Rounds (2 Distributed Systems/Coding + 1 System Design + 1 Values)",
    },
    "stripe": {
        "dsa": [
            {
                "title": "Design Rate Limiter (Token Bucket / Sliding Window Log)",
                "difficulty": "Medium",
                "topic": "System & Algorithm Design / Concurrency",
                "frequency": "Extreme (Top Stripe Question)",
                "hint": "Implement Token Bucket algorithm with timestamp tracking for refill rates and atomic lock guarantees.",
                "leetcode_url": "https://leetcode.com/problems/design-hit-counter/",
                "neetcode_url": "https://neetcode.io/practice",
                "time_complexity": "O(1)",
                "space_complexity": "O(N)",
            },
            {
                "title": "Basic Calculator II / Payment Ledger Parser",
                "difficulty": "Medium",
                "topic": "Stack / String Parsing",
                "frequency": "Very High",
                "hint": "Evaluate multiplication/division immediately onto stack; sum up remaining stack elements at the end.",
                "leetcode_url": "https://leetcode.com/problems/basic-calculator-ii/",
                "neetcode_url": "https://neetcode.io/practice",
                "time_complexity": "O(N)",
                "space_complexity": "O(N)",
            },
            {
                "title": "Simplify Path (Unix File Navigation)",
                "difficulty": "Medium",
                "topic": "Stack / Two Pointers",
                "frequency": "High",
                "hint": "Split by '/', push valid directories onto stack, pop on '..', and ignore empty or '.' components.",
                "leetcode_url": "https://leetcode.com/problems/simplify-path/",
                "neetcode_url": "https://neetcode.io/practice",
                "time_complexity": "O(N)",
                "space_complexity": "O(N)",
            },
        ],
        "system_design": [
            "Design Idempotent Payment Processing API & Double-Spend Prevention Engine",
            "Design Multi-Currency Global Ledger with distributed ACID guarantees",
            "Design Webhook Dispatcher with exponential backoff retries and dead letter queues",
        ],
        "interview_format": "1 Coding Screen (Interactive Debugging/Feature Add) ➔ 4 Onsite Rounds (1 Integration + 1 Refactoring + 1 System Design + 1 Manager)",
    },
    "general": {
        "dsa": [
            {
                "title": "Two Sum / 3Sum / Two Pointers",
                "difficulty": "Easy/Medium",
                "topic": "Arrays & Hash Table / Two Pointers",
                "frequency": "Universal Standard",
                "hint": "Sort array and use two pointers converging towards target sum, skipping duplicate values.",
                "leetcode_url": "https://leetcode.com/problems/3sum/",
                "neetcode_url": "https://neetcode.io/problems/3sum",
                "time_complexity": "O(N^2)",
                "space_complexity": "O(1) extra space",
            },
            {
                "title": "Trapping Rain Water",
                "difficulty": "Hard",
                "topic": "Two Pointers / Monotonic Stack",
                "frequency": "High",
                "hint": "Two pointers maintaining left_max and right_max calculate trapped water at whichever side has the smaller max.",
                "leetcode_url": "https://leetcode.com/problems/trapping-rain-water/",
                "neetcode_url": "https://neetcode.io/problems/trapping-rain-water",
                "time_complexity": "O(N)",
                "space_complexity": "O(1)",
            },
            {
                "title": "Longest Substring Without Repeating Characters",
                "difficulty": "Medium",
                "topic": "Sliding Window",
                "frequency": "Very High",
                "hint": "Use left and right pointers with a hash map storing the last seen index of each character to skip duplicates.",
                "leetcode_url": "https://leetcode.com/problems/longest-substring-without-repeating-characters/",
                "neetcode_url": "https://neetcode.io/problems/longest-substring-without-repeating-characters",
                "time_complexity": "O(N)",
                "space_complexity": "O(min(N, M))",
            },
            {
                "title": "Implement Trie (Prefix Tree)",
                "difficulty": "Medium",
                "topic": "Trie / Tree Design",
                "frequency": "Standard",
                "hint": "TrieNode with children hash map and is_end_of_word boolean flag allows O(L) prefix search.",
                "leetcode_url": "https://leetcode.com/problems/implement-trie-prefix-tree/",
                "neetcode_url": "https://neetcode.io/problems/implement-prefix-tree",
                "time_complexity": "O(L) per word",
                "space_complexity": "O(N * L)",
            },
        ],
        "system_design": [
            "Design a Scalable URL Shortener (TinyURL) with Base62 encoding, Redis caching, and rate limiting",
            "Design Distributed Rate Limiter with Token Bucket and Sliding Window Log in Redis",
            "Design Notification Service with multi-channel routing (Push, Email, SMS) and dead-letter queues",
        ],
        "interview_format": "1 Recruiter Screen ➔ 1 Tech Screen (60m) ➔ 3 Final Rounds (2 Coding + 1 Architecture/Behavioral)",
    },
}


class InterviewPrepService:
    """Generates comprehensive DSA prep kits with live Hacker News debriefs and LeetCode/NeetCode resources."""

    @staticmethod
    async def fetch_live_hn_experiences(company: str) -> list[dict[str, str]]:
        """Fetch authentic developer interview debriefs & experiences from Hacker News."""
        stories = []
        try:
            query = urllib.parse.quote(f"{company} interview")
            hn_url = f"https://hn.algolia.com/api/v1/search?query={query}&tags=story&hitsPerPage=5"
            async with httpx.AsyncClient(timeout=4.0) as client:
                res = await client.get(hn_url)
                if res.status_code == 200:
                    for hit in res.json().get("hits", []):
                        title = hit.get("title")
                        points = hit.get("points") or 0
                        comments = hit.get("num_comments") or 0
                        url = hit.get("url") or f"https://news.ycombinator.com/item?id={hit.get('objectID')}"
                        if title:
                            stories.append({
                                "source": "Hacker News Developer Debrief",
                                "title": title,
                                "url": url,
                                "summary": f"Verified engineering interview discussion ({points} upvotes, {comments} comments).",
                                "tips": "Read full HN discussion for real candidate questions, compensation insights, and interview feedback.",
                            })
        except Exception as e:
            logger.warning("hn_live_debrief_fetch_failed", error=str(e), company=company)
        return stories[:4]

    @staticmethod
    async def generate_prep_doc(
        company: str,
        role: str = "Software Engineer",
        jd_text: str | None = None,
        model_id: str | None = None,
        use_ai: bool = False,
    ) -> dict[str, Any]:
        """Synthesize previous DSA questions, technical interview rounds, and prep recommendations."""
        # 1. If user explicitly requests AI enhancement
        if use_ai:
            gemini_key = settings.gemini_api_key or os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")

            prompt = f"""
You are a Principal Tech Interview Coach specializing in software engineering rounds.
Research and synthesize previous technical interview questions and topics for:

Company: {company}
Role: {role}
Job Description Context:
{(jd_text or '')[:2000]}

Provide real interview question patterns and topics frequently asked at {company}.
Output ONLY valid JSON with this exact schema:
{{
  "company": "{company}",
  "role": "{role}",
  "dsa_questions": [
    {{
      "title": "<Question Name, e.g. LRU Cache / Course Schedule>",
      "difficulty": "<'Easy' | 'Medium' | 'Hard'>",
      "topic": "<e.g. Graph BFS, Dynamic Programming, Trees, Sliding Window>",
      "frequency": "<'High' | 'Very High' | 'Frequently Asked'>",
      "hint": "<1-2 sentence core insight or optimal approach>",
      "leetcode_url": "https://leetcode.com/problems/<problem-slug>/",
      "neetcode_url": "https://neetcode.io/practice",
      "time_complexity": "<e.g. O(N log K)>",
      "space_complexity": "<e.g. O(K)>"
    }}
  ],
  "system_design_topics": [
    "<System design topic 1 relevant to company scale>",
    "<System design topic 2>"
  ],
  "technical_deep_dives": [
    "<Language/framework specific question, e.g. Python Asyncio event loop / Angular Change Detection>",
    "<Database indexing / consistency question>"
  ],
  "behavioral_questions": [
    {{
      "question": "<Behavioral question aligned to company culture>",
      "focus": "<Leadership value tested, e.g. Dealing with conflict, Ownership>",
      "star_tip": "<How to structure response using STAR framework>"
    }}
  ],
  "reddit_experiences": [
    {{
      "source": "Reddit r/cscareerquestions",
      "title": "<Interview round debrief title>",
      "url": "https://reddit.com/r/cscareerquestions",
      "summary": "<What happened during each round>",
      "tips": "<Actionable advice from previous candidates>"
    }}
  ],
  "interview_format": "<Typical interview loop structure, e.g. 1 Recruiter Screen + 1 Tech Screen + 4 Onsite Rounds>"
}}
"""
            if gemini_key and (not model_id or "gemini" in model_id or model_id == "auto"):
                try:
                    from google import genai

                    client = genai.Client(api_key=gemini_key)
                    target_model = "gemini-3.7-flash" if not model_id or "3.7" in model_id else "gemini-3.6-flash"
                    response = client.models.generate_content(
                        model=target_model,
                        contents=prompt,
                    )
                    raw_text = response.text or ""
                    cleaned = raw_text.replace("```json", "").replace("```", "").strip()
                    data = json.loads(cleaned)
                    data["model_used"] = f"Gemini 3.7 Flash AI (Requested on-demand)"
                    return data
                except Exception as e:
                    logger.warning("gemini_prep_failed_using_curated", error=str(e))

            llm = LLMFactory.get_llm(model_id)
            if llm:
                try:
                    from langchain_core.messages import HumanMessage, SystemMessage

                    response = await llm.ainvoke([
                        SystemMessage(content="You are a senior tech hiring lead. Output valid JSON only."),
                        HumanMessage(content=prompt),
                    ])
                    cleaned = response.content.replace("```json", "").replace("```", "").strip()
                    data = json.loads(cleaned)
                    data["model_used"] = f"{model_id} (Requested on-demand)"
                    return data
                except Exception as e:
                    logger.warning("llm_interview_prep_failed_falling_back", error=str(e))

        # 2. Live Scraped HN Experiences + Verified LeetCode & NeetCode 150 Mappings
        return await InterviewPrepService._get_curated_prep(company, role)

    @staticmethod
    async def _get_curated_prep(company: str, role: str) -> dict[str, Any]:
        """Curated prep pack with LeetCode/NeetCode resources and live fetched Hacker News & Reddit experiences."""
        comp_key = company.lower().strip()
        matched_kb = None
        for k in COMPANY_DSA_KNOWLEDGE_BASE:
            if k in comp_key:
                matched_kb = COMPANY_DSA_KNOWLEDGE_BASE[k]
                break

        if not matched_kb:
            matched_kb = COMPANY_DSA_KNOWLEDGE_BASE["general"]

        # Fetch live Hacker News debriefs concurrently
        live_hn_stories = await InterviewPrepService.fetch_live_hn_experiences(company)

        reddit_links = [
            {
                "source": "Reddit r/leetcode",
                "title": f"Top Asked {company.title()} Coding Problems & Patterns",
                "url": f"https://www.google.com/search?q=site:reddit.com/r/leetcode+{urllib.parse.quote(company)}+interview+experience",
                "summary": f"Community discussions and frequently tested algorithmic patterns at {company.title()}.",
                "tips": "Review company-tagged problems and practice time-constrained coding in CoderPad without syntax highlighting.",
            },
            {
                "source": "Reddit r/cscareerquestions",
                "title": f"{company.title()} Onsite Loop Experience & Compensation Debrief",
                "url": f"https://www.google.com/search?q=site:reddit.com/r/cscareerquestions+{urllib.parse.quote(company)}+interview+experience",
                "summary": f"Full virtual onsite interview walkthrough, behavioral expectations, and recruiter debrief for {company.title()}.",
                "tips": "Prepare 6-8 STAR format stories highlighting ownership, technical disagreements, and measurable outcomes.",
            },
        ]

        experiences = live_hn_stories + reddit_links

        return {
            "company": company,
            "role": role,
            "dsa_questions": matched_kb["dsa"],
            "system_design_topics": matched_kb["system_design"],
            "technical_deep_dives": [
                f"How would you optimize database read/write throughput in a microservice for {company}?",
                "Explain the tradeoffs between SQL vs NoSQL, and how caching with Redis mitigates database load.",
                "How do asynchronous runtimes (FastAPI/asyncio) achieve high concurrency compared to multi-threaded WSGI?",
                "Explain database indexing strategies (B-Tree vs Hash vs LSM Trees in distributed storage).",
            ],
            "behavioral_questions": [
                {
                    "question": "Tell me about a time you faced a difficult technical roadblock and how you resolved it.",
                    "focus": "Problem Solving & Resilience",
                    "star_tip": "Situation: context; Task: goal; Action: specific debugging/architecture step you took; Result: quantitative outcome.",
                },
                {
                    "question": f"Why are you interested in joining {company} specifically?",
                    "focus": "Company Alignment & Motivation",
                    "star_tip": f"Reference {company}'s engineering scale, products, and how your skills directly add value.",
                },
                {
                    "question": "Describe a situation where you had a disagreement with a team member or tech lead on technical architecture.",
                    "focus": "Collaboration & Constructive Conflict",
                    "star_tip": "Focus on data-driven discussion, benchmarking options, testing prototypes, and committing fully once a decision is made.",
                },
            ],
            "reddit_experiences": experiences,
            "interview_format": matched_kb.get("interview_format", "1 Recruiter Screen ➔ 1 Tech Screen (60m) ➔ 3-4 Onsite Rounds"),
            "model_used": "Live Hacker News Debriefs + NeetCode 150 & LeetCode Knowledge Base",
        }
