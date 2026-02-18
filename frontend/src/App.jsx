import { useEffect, useRef, useState } from "react";
import "./App.css";

const CATEGORY_OPTIONS = [
  { value: "billing", label: "Billing" },
  { value: "technical", label: "Technical" },
  { value: "account", label: "Account" },
  { value: "general", label: "General" },
];

const PRIORITY_OPTIONS = [
  { value: "low", label: "Low" },
  { value: "medium", label: "Medium" },
  { value: "high", label: "High" },
  { value: "critical", label: "Critical" },
];

const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

const emptyStats = {
  total_tickets: 0,
  open_tickets: 0,
  avg_tickets_per_day: 0,
  priority_breakdown: {},
  category_breakdown: {},
};

function App() {
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [category, setCategory] = useState("general");
  const [priority, setPriority] = useState("low");
  const [tickets, setTickets] = useState([]);
  const [stats, setStats] = useState(null);
  const [classifyLoading, setClassifyLoading] = useState(false);
  const [submitLoading, setSubmitLoading] = useState(false);
  const [classifyError, setClassifyError] = useState("");
  const [submitError, setSubmitError] = useState("");

  const classifyTimer = useRef(null);
  const lastClassified = useRef("");

  const fetchTickets = async () => {
    const response = await fetch(`${API_BASE}/api/tickets/`);
    if (!response.ok) {
      throw new Error("Failed to load tickets");
    }
    const data = await response.json();
    setTickets(Array.isArray(data) ? data : []);
  };

  const fetchStats = async () => {
    const response = await fetch(`${API_BASE}/api/tickets/stats/`);
    if (!response.ok) {
      throw new Error("Failed to load stats");
    }
    const data = await response.json();
    setStats(data || emptyStats);
  };

  useEffect(() => {
    Promise.all([fetchTickets(), fetchStats()]).catch(() => {
      // Ignore initial load errors; surface through UI later if needed.
    });
  }, []);

  const runClassify = async (text) => {
    if (!text.trim()) {
      return;
    }

    if (text.trim() === lastClassified.current) {
      return;
    }

    lastClassified.current = text.trim();
    setClassifyLoading(true);
    setClassifyError("");

    try {
      const response = await fetch(`${API_BASE}/api/tickets/classify/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ description: text }),
      });

      if (!response.ok) {
        throw new Error("Classification failed");
      }

      const data = await response.json();
      if (data.suggested_category) {
        setCategory(data.suggested_category);
      }
      if (data.suggested_priority) {
        setPriority(data.suggested_priority);
      }
    } catch (error) {
      setClassifyError("Unable to classify description. Please choose manually.");
    } finally {
      setClassifyLoading(false);
    }
  };

  useEffect(() => {
    if (!description.trim()) {
      return;
    }

    if (classifyTimer.current) {
      clearTimeout(classifyTimer.current);
    }

    classifyTimer.current = setTimeout(() => {
      runClassify(description);
    }, 500);

    return () => {
      if (classifyTimer.current) {
        clearTimeout(classifyTimer.current);
      }
    };
  }, [description]);

  const handleDescriptionBlur = () => {
    if (classifyTimer.current) {
      clearTimeout(classifyTimer.current);
    }
    runClassify(description);
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setSubmitLoading(true);
    setSubmitError("");

    try {
      const response = await fetch(`${API_BASE}/api/tickets/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title, description, category, priority }),
      });

      if (!response.ok) {
        throw new Error("Ticket creation failed");
      }

      setTitle("");
      setDescription("");
      setCategory("general");
      setPriority("low");
      lastClassified.current = "";

      await Promise.all([fetchTickets(), fetchStats()]);
    } catch (error) {
      setSubmitError("Unable to submit ticket. Please try again.");
    } finally {
      setSubmitLoading(false);
    }
  };

  const statsData = stats || emptyStats;

  return (
    <div className="app">
      <header className="hero">
        <div>
          <p className="eyebrow">Support Command</p>
          <h1>Ticket Intelligence Console</h1>
          <p className="subhead">
            Capture support requests, auto-classify urgency, and keep a live pulse
            on ticket flow.
          </p>
        </div>
        <div className="hero-chip">Live Ops</div>
      </header>

      <main className="layout">
        <section className="panel form-panel">
          <div className="panel-header">
            <h2>New Ticket</h2>
            <span className={classifyLoading ? "pill active" : "pill"}>
              {classifyLoading ? "Classifying..." : "Ready"}
            </span>
          </div>

          <form onSubmit={handleSubmit} className="form">
            <label>
              Title
              <input
                type="text"
                value={title}
                onChange={(event) => setTitle(event.target.value)}
                placeholder="Short summary"
                required
              />
            </label>

            <label>
              Description
              <textarea
                value={description}
                onChange={(event) => setDescription(event.target.value)}
                onBlur={handleDescriptionBlur}
                placeholder="Describe the issue..."
                rows={5}
                required
              />
            </label>

            {classifyError ? <p className="error">{classifyError}</p> : null}

            <div className="row">
              <label>
                Category
                <select
                  value={category}
                  onChange={(event) => setCategory(event.target.value)}
                  disabled={classifyLoading}
                >
                  {CATEGORY_OPTIONS.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </label>

              <label>
                Priority
                <select
                  value={priority}
                  onChange={(event) => setPriority(event.target.value)}
                  disabled={classifyLoading}
                >
                  {PRIORITY_OPTIONS.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </label>
            </div>

            {submitError ? <p className="error">{submitError}</p> : null}

            <button type="submit" disabled={submitLoading}>
              {submitLoading ? "Submitting..." : "Create Ticket"}
            </button>
          </form>
        </section>

        <section className="panel stats-panel">
          <div className="panel-header">
            <h2>Dashboard</h2>
            <span className="pill">Auto-refresh</span>
          </div>

          <div className="stats-grid">
            <div className="stat-card">
              <p>Total Tickets</p>
              <h3>{statsData.total_tickets}</h3>
            </div>
            <div className="stat-card">
              <p>Open Tickets</p>
              <h3>{statsData.open_tickets}</h3>
            </div>
            <div className="stat-card">
              <p>Avg Tickets / Day</p>
              <h3>{Number(statsData.avg_tickets_per_day).toFixed(2)}</h3>
            </div>
          </div>

          <div className="breakdown">
            <div>
              <h4>Priority Breakdown</h4>
              <ul>
                {PRIORITY_OPTIONS.map((option) => (
                  <li key={option.value}>
                    <span>{option.label}</span>
                    <span>{statsData.priority_breakdown[option.value] || 0}</span>
                  </li>
                ))}
              </ul>
            </div>
            <div>
              <h4>Category Breakdown</h4>
              <ul>
                {CATEGORY_OPTIONS.map((option) => (
                  <li key={option.value}>
                    <span>{option.label}</span>
                    <span>{statsData.category_breakdown[option.value] || 0}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </section>

        <section className="panel list-panel">
          <div className="panel-header">
            <h2>Tickets</h2>
            <span className="pill">Newest First</span>
          </div>

          <div className="ticket-list">
            {tickets.length === 0 ? (
              <div className="empty">No tickets yet. Create the first one.</div>
            ) : (
              tickets.map((ticket) => (
                <article key={ticket.id} className="ticket-card">
                  <div>
                    <h3>{ticket.title}</h3>
                    <p>{ticket.description}</p>
                  </div>
                  <div className="ticket-meta">
                    <span>{ticket.category}</span>
                    <span>{ticket.priority}</span>
                    <span>{ticket.status}</span>
                    <span>
                      {ticket.created_at
                        ? new Date(ticket.created_at).toLocaleString()
                        : ""}
                    </span>
                  </div>
                </article>
              ))
            )}
          </div>
        </section>
      </main>
    </div>
  );
}

export default App;
