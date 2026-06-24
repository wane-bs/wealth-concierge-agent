# Kaggle Submission & Pitch Preparation Guide

This guide details the remaining steps and requirements for submitting the **Personal Wealth Concierge Agent** to the Kaggle Vibe Coding Agents Capstone Project competition.

---

## 🗓️ Important Deadlines
*   **Submission Deadline**: July 6, 2026, 23:59 PT *(approx. 13:59 on July 7, 2026, Vietnam Time)*.
*   **Submission Format**: 1 single submission per team via the designated **Google Form**.

---

## 📦 Required Deliverables

| Deliverable | Format | Required Content |
| :--- | :--- | :--- |
| **GitHub Repository** | Public / Judge Access | Full codebase, comments, tests, and bilingual [README.md](file:///f:/capstone/wealth-concierge-agent/README.md). |
| **Kaggle Notebook** | Public Notebook | Interactive setup, installation guide, and agent demo script. |
| **YouTube Video** | Public / Unlisted | Max 5-minute presentation: Problem $\rightarrow$ Why Agent $\rightarrow$ Architecture $\rightarrow$ Live Demo $\rightarrow$ Technical Summary. |
| **Google Form** | Form Submission | Repository Link, Kaggle Notebook Link, YouTube Link, and Project Pitch Writeup. |

---

## 📋 Step-by-Step Submission Setup

### Step 1: Kaggle Notebook Preparation
Create a public Notebook on Kaggle representing the project. 
1. Enable **Internet connection** in the Kaggle Notebook Settings (right-hand panel).
2. Add a code block to clone the repository and sync dependencies:
   ```python
   # 1. Clone codebase
   !git clone https://github.com/wane-bs/wealth-concierge-agent.git
   %cd wealth-concierge-agent

   # 2. Install dependencies
   !pip install uv
   !uv pip install --system -r pyproject.toml
   ```
3. Add a code block to demonstrate the Agent run in the Notebook:
   ```python
   import os
   from app.agent import root_agent
   from google.adk.runners import Runner
   from google.adk.sessions import InMemorySessionService
   from google.genai import types

   # Set API Key (Or instruct judges to use Kaggle User Secrets)
   os.environ["GOOGLE_API_KEY"] = "YOUR_GEMINI_API_KEY"

   session_service = InMemorySessionService()
   runner = Runner(agent=root_agent, session_service=session_service, app_name="app")
   session = session_service.create_session_sync(user_id="demo_user", app_name="app")

   # Send query in English
   query = types.Content(
       role="user", 
       parts=[types.Part.from_text(text="[System: Language: English]\nHello, show my portfolio")]
   )
   events = list(runner.run(new_message=query, user_id="demo_user", session_id=session.id))

   for event in events:
       if event.content and event.content.parts:
           print("".join([p.text for p in event.content.parts if p.text]))
   ```

### Step 2: YouTube Presentation Video (Max 5 Minutes)
Record and edit a 5-minute video demonstrating the product. Use this structured slide/narration outline:
*   **0:00 - 1:00 (Problem & Value Proposition)**:
    *   Highlight the difficulties individual investors face in tracking stock quotes, performing fundamental analysis, and managing asset warning alerts.
    *   Introduce the *Personal Wealth Concierge Agent* as the solution.
*   **1:00 - 2:00 (Architecture Breakdown)**:
    *   Show the Mermaid architecture diagram from the README. Explain the Hub-and-Spoke coordination of Root Orchestrator and 3 specialized sub-agents.
*   **2:00 - 4:00 (Live Product Demo)**:
    *   Demonstrate Streamlit UI with language toggles (English and Vietnamese).
    *   Chat with the assistant: ask to view portfolio, request FPT financial analysis from the Wealth Advisor, and update alerts.
    *   Click "Trigger Manual Scan" to scan live prices and showcase the automatically delivered HTML email report.
*   **4:00 - 5:00 (Technical Merits & Outro)**:
    *   Highlight credentials protection, test coverage (6/6 passing pytest), and evaluation setup.

### Step 3: Project Pitch Writeup (10 Points)
Copy and use the following writeup for the Kaggle Notebook description and Google Form fields:

```markdown
# Personal Wealth Concierge Agent: Multi-Agent Portfolio Manager & Real-Time Sentinel

## 1. Problem Statement & Value Proposition
Individual investors in the Vietnamese stock market often struggle to manage their portfolios, perform quick fundamental analysis, and monitor rapid price fluctuations in real-time. Traditional tools are scattered, static, and require manual updates. 
Our solution, the **Personal Wealth Concierge Agent**, introduces an intelligent virtual assistant that coordinates dedicated sub-agents to streamline portfolio tracking, stock valuations, and automated email warning systems. It bridges the gap between raw financial APIs (Vnstock) and user-centric wealth management.

## 2. System Architecture & Concepts Illustrated
The project implements a modular **Hub-and-Spoke** design powered by the **Google Agent Development Kit (ADK)**:
*   **Root Orchestrator Agent**: Dynamically handles user intents and coordinates workflows through LLM Delegation.
*   **Portfolio Manager Agent**: Safely manages local asset holdings using structured local JSON files.
*   **Wealth Advisor Agent**: Performs real-time valuation, financial ratio calculations (P/E, P/B, EPS), and news extraction.
*   **Market Sentinel Agent**: Automatically runs periodic scans and flags price changes against cost bases.

### Kaggle Technical Criteria Coverage:
1.  **Multi-agent (ADK)**: Complex orchestration of 4 specialized agents.
2.  **Security & Privacy**: Absolute credential isolation via `.env` environments and local filesystem storage for user assets (`portfolio.json`) avoiding external database leaks.
3.  **Deployability**: Containerized deployment blueprint via `Dockerfile`, interactive Web UI utilizing `Streamlit`, and a background daemon (`sentinel_daemon.py`) running 24/7.
4.  **Bilingualism**: Localized dynamic UI mapping and bilingual system instructions for the LLM core.

## 3. Implementation Journey
We built this agent from prototype to production using the Google ADK Quality Flywheel:
1.  **Scaffolding**: Initialized project via `agents-cli`.
2.  **Integration**: Interfaced with the Vietnamese financial stock library `Vnstock v4.0.4` and Python's `smtplib` for email delivery.
3.  **Refinement**: Upgraded core model to `gemini-2.5-flash` to bypass free-tier rate limits via model-specific quota isolation.
4.  **Verification**: Wrote a robust integration test suite (`pytest`) mocking both the external stock quote APIs and SMTP endpoints, achieving 100% test passes.
```

---
---

# 🇻🇳 Hướng dẫn Hoàn thiện & Nộp bài Kaggle

Tài liệu này ghi lại chi tiết các bước cần thực hiện để chuẩn bị và nộp dự án **Personal Wealth Concierge Agent** cho cuộc thi Kaggle Vibe Coding Agents.

---

## 🗓️ Mốc thời gian quan trọng
*   **Hạn nộp bài**: Trước 23:59 ngày 06/07/2026 PT *(khoảng 13:59 ngày 07/07/2026 giờ Việt Nam)*.
*   **Hình thức**: Nộp qua **Google Form** chung của Ban tổ chức (chỉ nộp 1 lần duy nhất cho cả đội).

---

## 📦 Các sản phẩm cần chuẩn bị

1.  **Kaggle Notebook**: Tạo Notebook công khai trên Kaggle. Notebook cần chứa lệnh clone GitHub repo của đội, cài đặt dependencies và có một đoạn mã chạy demo để Ban giám khảo kiểm thử nhanh.
2.  **Video YouTube (Tối đa 5 phút)**: Thiết lập chế độ Công khai (Public) hoặc Không công khai (Unlisted). Video cần chứa các phân mục rõ ràng: Đặt vấn đề $\rightarrow$ Kiến trúc hệ thống $\rightarrow$ Demo hoạt động thực tế trên giao diện Streamlit $\rightarrow$ Chứng minh kỹ thuật bảo mật và kiểm thử.
3.  **GitHub Repository**: Mã nguồn sạch của dự án, có tệp [README.md](file:///f:/capstone/wealth-concierge-agent/README.md) đầy đủ và chuyên nghiệp (đã cấu hình an toàn không lộ API Keys).

---

## 🚀 Các bước thực thi chi tiết

### Bước 1: Thiết lập Kaggle Notebook
1. Khởi tạo một Notebook mới trên nền tảng Kaggle.
2. Bật kết nối Internet trong phần cài đặt của Notebook (bên phải màn hình) để có thể tải thư viện ngoài.
3. Tạo khối mã đầu tiên để nạp mã nguồn từ GitHub và đồng bộ môi trường:
   ```python
   !git clone https://github.com/wane-bs/wealth-concierge-agent.git
   %cd wealth-concierge-agent
   !pip install uv
   !uv pip install --system -r pyproject.toml
   ```
4. Viết kịch bản kiểm thử nhanh để minh họa Agent chạy trên dòng lệnh:
   ```python
   import os
   from app.agent import root_agent
   from google.adk.runners import Runner
   from google.adk.sessions import InMemorySessionService
   from google.genai import types

   # Thiết lập khóa API Key chạy thử
   os.environ["GOOGLE_API_KEY"] = "YOUR_API_KEY"

   session_service = InMemorySessionService()
   runner = Runner(agent=root_agent, session_service=session_service, app_name="app")
   session = session_service.create_session_sync(user_id="demo_user", app_name="app")

   # Gửi câu hỏi test bằng tiếng Việt hoặc tiếng Anh
   query = types.Content(
       role="user", 
       parts=[types.Part.from_text(text="[System: Language: Tiếng Việt]\nXin chào, hãy hiển thị danh mục của tôi")]
   )
   events = list(runner.run(new_message=query, user_id="demo_user", session_id=session.id))

   for event in events:
       if event.content and event.content.parts:
           print("".join([p.text for p in event.content.parts if p.text]))
   ```

### Bước 2: Dàn ý quay Video YouTube 5 phút
*   **0:00 - 1:00 (Bài toán & Giải pháp)**: Chỉ ra khó khăn của nhà đầu tư khi theo dõi danh mục chứng khoán và cách Wealth Concierge Agent giải quyết bài toán qua kiến trúc Multi-Agent.
*   **1:00 - 2:00 (Kiến trúc)**: Chiếu sơ đồ Mermaid trong README, làm rõ vai trò điều phối của Root Orchestrator đến 3 tác tử con.
*   **2:00 - 4:00 (Demo thực tế)**: Biểu diễn giao diện Dashboard đa ngôn ngữ (Tiếng Anh/Tiếng Việt). Chat yêu cầu thêm cổ phiếu, hỏi đáp phân tích kỹ thuật và click kích hoạt Sentinel quét gửi email cảnh báo tự động.
*   **4:00 - 5:00 (Tổng kết Kỹ thuật)**: Minh họa cơ chế bảo mật (file `.env` bị ẩn bởi `.gitignore`), đã viết test case đầy đủ và tích hợp CLI Eval.
