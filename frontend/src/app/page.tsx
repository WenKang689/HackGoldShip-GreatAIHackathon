"use client";

import { useState, useEffect, useRef } from "react";

// Invoice Preview Component
function InvoicePreview({ invoice, onApprove, onEdit }: any) {
  return (
    <div style={{ 
      fontFamily: 'Arial, sans-serif', 
      maxWidth: '800px', 
      margin: '0 auto', 
      padding: '20px', 
      border: '1px solid #ddd',
      borderRadius: '4px'
    }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '30px' }}>
        <div style={{ height: '60px', width: '60px' }}>
          <img 
            src={invoice.logo_url || 'https://hackathon-static-invoice-template.s3.ap-southeast-5.amazonaws.com/logo.svg'} 
            alt="Company Logo" 
            style={{ height: '60px', width: '60px', objectFit: 'contain' }}
          />
        </div>
        <div style={{ textAlign: 'right', lineHeight: '1.4' }}>
          <strong style={{ fontSize: '18px' }}>The Great Company</strong><br />
          12, Hack Road 5,<br />
          Techville, Cheras,<br />
          56000, Kuala Lumpur
        </div>
      </div>

      {/* Invoice Info */}
      <div style={{ margin: '30px 0' }}>
        <h2 style={{ color: '#333', margin: '0' }}>INVOICE #{invoice.invoice_id}</h2>
        <p style={{ margin: '5px 0', color: '#666' }}>Date: {invoice.issue_date}</p>
        <p style={{ margin: '5px 0', color: '#666' }}>Status: {invoice.status}</p>
      </div>

      {/* Bill To */}
      <div style={{ margin: '30px 0' }}>
        <strong style={{ color: '#333' }}>Bill To:</strong><br />
        <div style={{ marginTop: '10px', lineHeight: '1.4' }}>
          <strong>{invoice.account?.name || 'N/A'}</strong><br />
          {invoice.account?.billing_address?.street || 'Address not available'}<br />
          {invoice.account?.billing_address?.city}, {invoice.account?.billing_address?.postal_code}<br />
          {invoice.account?.phone || 'N/A'}<br />
        </div>
      </div>

      {/* Contact */}
      <div style={{ margin: '30px 0' }}>
        <strong style={{ color: '#333' }}>Contact:</strong><br />
        <div style={{ marginTop: '10px', lineHeight: '1.4' }}>
          {invoice.contact?.phone || 'N/A'}<br />
          {invoice.contact?.email || 'N/A'}
        </div>
      </div>

      {/* Line Items */}
      <table style={{ width: '100%', borderCollapse: 'collapse', margin: '30px 0' }}>
        <thead>
          <tr style={{ backgroundColor: '#f8f9fa' }}>
            <th style={{ padding: '12px', textAlign: 'left', border: '1px solid #ddd' }}>Product</th>
            <th style={{ padding: '12px', textAlign: 'center', border: '1px solid #ddd' }}>Qty</th>
            <th style={{ padding: '12px', textAlign: 'right', border: '1px solid #ddd' }}>Unit Price</th>
            <th style={{ padding: '12px', textAlign: 'right', border: '1px solid #ddd' }}>Total</th>
          </tr>
        </thead>
        <tbody>
          {(invoice.line_items || []).map((item: any, idx: number) => (
            <tr key={idx}>
              <td style={{ padding: '12px', border: '1px solid #ddd' }}>{item.product}</td>
              <td style={{ padding: '12px', textAlign: 'center', border: '1px solid #ddd' }}>{item.qty}</td>
              <td style={{ padding: '12px', textAlign: 'right', border: '1px solid #ddd' }}>
                ${item.unit_price?.toFixed(2) || '0.00'}
              </td>
              <td style={{ padding: '12px', textAlign: 'right', border: '1px solid #ddd' }}>
                ${item.total?.toFixed(2) || '0.00'}
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      {/* Total */}
      <div style={{ textAlign: 'right', marginTop: '30px' }}>
        <div style={{ margin: '10px 0', fontSize: '18px', color: '#333' }}>
          <strong>Total: ${invoice.total_amount?.toFixed(2) || '0.00'} {invoice.currency || 'USD'}</strong>
        </div>
      </div>

      {/* Actions */}
      <div style={{ marginTop: '20px', display: 'flex', gap: '10px' }}>
        <button 
          onClick={onApprove}
          style={{
            padding: '12px 24px',
            backgroundColor: '#28a745',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer',
            fontSize: '14px',
            fontWeight: '500'
          }}
        >
          ✓ Approve & Send Invoice PDF to Email
        </button>
      </div>
    </div>
  );
}

export default function Home() {
  const [messages, setMessages] = useState<
    {
      text?: string;
      isUser: boolean;
      type?: string;
      html?: string;
      data?: any;
      actions?: string[];
    }[]
  >([{ text: "Hi, how can I help you?", isUser: false }]);
  const [input, setInput] = useState("");
  const [ws, setWs] = useState<WebSocket | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [activeTab, setActiveTab] = useState("dashboard");

  // Simple tab change without persistence to avoid hydration issues
  const handleTabChange = (tab: string) => {
    setActiveTab(tab);
  };
  const [statusFilter, setStatusFilter] = useState("all");
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const [invoiceStatusFilter, setInvoiceStatusFilter] = useState("all");
  const [invoiceDropdownOpen, setInvoiceDropdownOpen] = useState(false);
  const [dashboardData, setDashboardData] = useState({
    today_revenue: 0,
    invoice_stats: {
      pending: { count: 0, amount: 0 },
      processing: { count: 0, amount: 0 },
      success: { count: 0, amount: 0 },
      fail: { count: 0, amount: 0 },
      overdue: { count: 0, amount: 0 },
    },
  });
  const [subscriptionStatusFilter, setSubscriptionStatusFilter] =
    useState("all");
  const [subscriptionDropdownOpen, setSubscriptionDropdownOpen] =
    useState(false);
  const [overdueInvoices, setOverdueInvoices] = useState([]);
  const [closedOpportunities, setClosedOpportunities] = useState([]);
  const [reminderModalOpen, setReminderModalOpen] = useState(false);
  const [selectedPayment, setSelectedPayment] = useState<any>(null);
  const [reminderMethod, setReminderMethod] = useState<string[]>([]);
  const [isTyping, setIsTyping] = useState(false);
  const [selectedDays, setSelectedDays] = useState(7);
  const [daysDropdownOpen, setDaysDropdownOpen] = useState(false);

  const handleReminderClick = (payment: any) => {
    setSelectedPayment(payment);
    setReminderModalOpen(true);
    setReminderMethod([]);
  };

  const handleMethodChange = (method: string) => {
    setReminderMethod((prev) =>
      prev.includes(method)
        ? prev.filter((m) => m !== method)
        : [...prev, method]
    );
  };

  const handleSendReminder = () => {
    console.log(
      "Sending reminder via:",
      reminderMethod,
      "to:",
      selectedPayment?.user
    );
    setReminderModalOpen(false);
    setSelectedPayment(null);
    setReminderMethod([]);
  };
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const invoiceDropdownRef = useRef<HTMLDivElement>(null);
  const subscriptionDropdownRef = useRef<HTMLDivElement>(null);
  const daysDropdownRef = useRef<HTMLDivElement>(null);

  // Fetch dashboard data
  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        const response = await fetch(
          "http://localhost:8000/api/dashboard/invoices"
        );
        const data = await response.json();
        setDashboardData(data);
      } catch (error) {
        console.error("Failed to fetch dashboard data:", error);
      }
    };

    fetchDashboardData();
    // Refresh every 30 seconds
    const interval = setInterval(fetchDashboardData, 30000);
    return () => clearInterval(interval);
  }, []);

  // Fetch overdue recurring invoices
  useEffect(() => {
    const fetchOverdueInvoices = async () => {
      try {
        const response = await fetch(
          "http://localhost:8000/api/invoices/overdue-recurring"
        );
        const data = await response.json();
        setOverdueInvoices(data.invoices || []);
      } catch (error) {
        console.error("Failed to fetch overdue invoices:", error);
      }
    };

    fetchOverdueInvoices();
  }, []);

  // Fetch closed opportunities
  useEffect(() => {
    const fetchClosedOpportunities = async () => {
      try {
        const response = await fetch(
          "http://localhost:8000/api/opportunities/closed"
        );
        const data = await response.json();
        setClosedOpportunities(data.opportunities || []);
      } catch (error) {
        console.error("Failed to fetch closed opportunities:", error);
      }
    };
    fetchClosedOpportunities();
  }, []);

  // Fetch closed opportunities
  useEffect(() => {
    const fetchClosedOpportunities = async () => {
      try {
        const response = await fetch(
          "http://localhost:8000/api/opportunities/closed"
        );
        const data = await response.json();
        setClosedOpportunities(data.opportunities || []);
      } catch (error) {
        console.error("Failed to fetch closed opportunities:", error);
      }
    };

    fetchClosedOpportunities();
  }, []);

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(event.target as Node)
      ) {
        setDropdownOpen(false);
      }
      if (
        invoiceDropdownRef.current &&
        !invoiceDropdownRef.current.contains(event.target as Node)
      ) {
        setInvoiceDropdownOpen(false);
      }
      if (
        subscriptionDropdownOpen &&
        subscriptionDropdownRef.current &&
        !subscriptionDropdownRef.current.contains(event.target as Node)
      ) {
        setSubscriptionDropdownOpen(false);
      }
      if (
        daysDropdownOpen &&
        daysDropdownRef.current &&
        !daysDropdownRef.current.contains(event.target as Node)
      ) {
        setDaysDropdownOpen(false);
      }
    }

    document.addEventListener("mousedown", handleClickOutside);
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, []);

  useEffect(() => {
    setIsConnected(false);
    const websocket = new WebSocket("ws://localhost:8000/ws/admin");

    websocket.onopen = () => {
      console.log("Connected to admin WebSocket");
      setIsConnected(true);
    };

    websocket.onmessage = (event) => {
      const cleanMessage = event.data.replace(/^admin bot:\s*/i, "");
      setIsTyping(false);

      // Try to parse as JSON for structured responses
      try {
        const parsed = JSON.parse(cleanMessage);
        if (parsed.type === "invoice_preview") {
          setMessages((prev) => [...prev, { ...parsed, isUser: false }]);
          return;
        }
      } catch (e) {
        // Not JSON, treat as regular text
      }

      setMessages((prev) => [...prev, { text: cleanMessage, isUser: false }]);
    };

    websocket.onerror = (error) => {
      console.error("WebSocket error:", error);
      setIsConnected(false);
    };

    websocket.onclose = () => {
      console.log("WebSocket connection closed");
      setIsConnected(false);
    };

    setWs(websocket);

    return () => {
      websocket.close();
    };
  }, []);

  useEffect(() => {
    // Auto-scroll removed to prevent page jumping to bottom
  }, [messages]);

  const sendMessage = () => {
    if (input.trim() && ws && isConnected) {
      setMessages((prev) => [...prev, { text: input, isUser: true }]);
      ws.send(input);
      setInput("");
      setIsTyping(true);
    } else if (!isConnected) {
      console.error("WebSocket not connected");
    }
  };

  const handleInvoiceAction = (action: string, data: any) => {
    if (action === 'approve') {
      if (ws && isConnected) {
        setMessages(prev => [...prev, { text: `Approve and send invoice ${data?.invoice_id}`, isUser: true }])
        ws.send(`approveAndSendInvoice: ${JSON.stringify(data)}`)
      }
    }
  };

  return (
    <div className="container">
      <div className="left-column">
        <div className="header-row">
          <h2>Finance Dashboard</h2>
          <div className="tabs">
            <button
              className={`tab ${activeTab === "dashboard" ? "active" : ""}`}
              onClick={() => handleTabChange("dashboard")}
            >
              Overview
            </button>
            <button
              className={`tab ${activeTab === "pending" ? "active" : ""}`}
              onClick={() => handleTabChange("pending")}
            >
              Invoice
            </button>
            <button
              className={`tab ${activeTab === "overdue" ? "active" : ""}`}
              onClick={() => handleTabChange("overdue")}
            >
              Subscription
            </button>
          </div>
        </div>
        <div className="tab-content">
          {activeTab === "dashboard" && (
            <div className="analytics-grid">
              <div className="analytics-card">
                <h3>Today's Revenue</h3>
                <div className="number revenue-number">
                  ${(dashboardData.today_revenue || 0).toLocaleString()}
                </div>
              </div>
              <div className="analytics-card">
                <h3>Pending Invoice</h3>
                <div className="number pending-number">
                  {dashboardData.invoice_stats.pending.count}
                </div>
              </div>
              <div className="analytics-card">
                <h3>Overdue Payment</h3>
                <div className="number processing-number">
                  {dashboardData.invoice_stats.processing.count}
                </div>
              </div>
              <div className="status-row">
                <div className="analytics-card status-card">
                  <h3>Payment Status</h3>
                  <div className="status-chart">
                    <div
                      className="pie-chart"
                      style={{
                        background: `conic-gradient(
                      #8b5cf6 0deg ${
                        (dashboardData.invoice_stats.success.count /
                          (dashboardData.invoice_stats.success.count +
                            dashboardData.invoice_stats.pending.count +
                            dashboardData.invoice_stats.overdue.count +
                            dashboardData.invoice_stats.processing.count)) *
                        360
                      }deg,
                      #3b82f6 ${
                        (dashboardData.invoice_stats.success.count /
                          (dashboardData.invoice_stats.success.count +
                            dashboardData.invoice_stats.pending.count +
                            dashboardData.invoice_stats.overdue.count +
                            dashboardData.invoice_stats.processing.count)) *
                        360
                      }deg ${
                          ((dashboardData.invoice_stats.success.count +
                            dashboardData.invoice_stats.pending.count) /
                            (dashboardData.invoice_stats.success.count +
                              dashboardData.invoice_stats.pending.count +
                              dashboardData.invoice_stats.overdue.count +
                              dashboardData.invoice_stats.processing.count)) *
                          360
                        }deg,
                      #06b6d4 ${
                        ((dashboardData.invoice_stats.success.count +
                          dashboardData.invoice_stats.pending.count) /
                          (dashboardData.invoice_stats.success.count +
                            dashboardData.invoice_stats.pending.count +
                            dashboardData.invoice_stats.overdue.count +
                            dashboardData.invoice_stats.processing.count)) *
                        360
                      }deg ${
                          ((dashboardData.invoice_stats.success.count +
                            dashboardData.invoice_stats.pending.count +
                            dashboardData.invoice_stats.processing.count) /
                            (dashboardData.invoice_stats.success.count +
                              dashboardData.invoice_stats.pending.count +
                              dashboardData.invoice_stats.overdue.count +
                              dashboardData.invoice_stats.processing.count)) *
                          360
                        }deg,
                      #4338ca ${
                        ((dashboardData.invoice_stats.success.count +
                          dashboardData.invoice_stats.pending.count +
                          dashboardData.invoice_stats.processing.count) /
                          (dashboardData.invoice_stats.success.count +
                            dashboardData.invoice_stats.pending.count +
                            dashboardData.invoice_stats.overdue.count +
                            dashboardData.invoice_stats.processing.count)) *
                        360
                      }deg 360deg
                    )`,
                      }}
                    ></div>
                    <div className="status-legend">
                      <div className="legend-item">
                        <div className="legend-color success"></div>
                        <span className="legend-title">Success</span>
                        <span className="legend-number">
                          {dashboardData.invoice_stats.success.count}
                        </span>
                      </div>
                      <div className="legend-item">
                        <div className="legend-color pending"></div>
                        <span className="legend-title">Pending</span>
                        <span className="legend-number">
                          {dashboardData.invoice_stats.pending.count}
                        </span>
                      </div>
                      <div className="legend-item">
                        <div className="legend-color processing"></div>
                        <span className="legend-title">Processing</span>
                        <span className="legend-number">
                          {dashboardData.invoice_stats.processing.count}
                        </span>
                      </div>
                      <div className="legend-item">
                        <div className="legend-color overdue"></div>
                        <span className="legend-title">Overdue</span>
                        <span className="legend-number">
                          {dashboardData.invoice_stats.overdue.count}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
                <div className="analytics-card risk-card">
                  <h3>Overdue Risk</h3>
                  <div className="risk-threshold">
                    <div className="risk-level">Medium Risk</div>
                    <div className="gauge-container">
                      <svg className="gauge" viewBox="0 0 200 120">
                        <path
                          d="M 20 100 A 80 80 0 0 1 100 20"
                          fill="none"
                          stroke="#10b981"
                          strokeWidth="12"
                        />
                        <path
                          d="M 100 20 A 80 80 0 0 1 156 43"
                          fill="none"
                          stroke="#f59e0b"
                          strokeWidth="12"
                        />
                        <path
                          d="M 156 43 A 80 80 0 0 1 180 100"
                          fill="none"
                          stroke="#ef4444"
                          strokeWidth="12"
                        />
                        <line
                          x1="100"
                          y1="100"
                          x2="135"
                          y2="65"
                          stroke="#333"
                          strokeWidth="3"
                        />
                        <circle cx="100" cy="100" r="5" fill="#333" />
                      </svg>
                    </div>
                    <div className="threshold-labels">
                      <span>Low</span>
                      <span>High</span>
                    </div>
                  </div>
                </div>
              </div>

              <div className="analytics-card">
                <div className="revenue-header">
                  <h3>Revenue Analytics</h3>
                </div>
                <div className="revenue-chart">
                  <svg
                    width="100%"
                    height="200"
                    viewBox="0 0 800 200"
                    preserveAspectRatio="none"
                  >
                    <defs>
                      <linearGradient
                        id="revenueGradient"
                        x1="0%"
                        y1="0%"
                        x2="0%"
                        y2="100%"
                      >
                        <stop
                          offset="0%"
                          stopColor="#3b82f6"
                          stopOpacity="0.3"
                        />
                        <stop
                          offset="100%"
                          stopColor="#3b82f6"
                          stopOpacity="0"
                        />
                      </linearGradient>
                    </defs>

                    {/* Grid lines */}
                    {[0, 1, 2, 3, 4].map((i) => (
                      <line
                        key={i}
                        x1="60"
                        y1={40 + i * 30}
                        x2="740"
                        y2={40 + i * 30}
                        stroke="#e5e5e5"
                        strokeWidth="1"
                      />
                    ))}

                    {/* Revenue line */}
                    <polyline
                      fill="none"
                      stroke="#3b82f6"
                      strokeWidth="3"
                      points="100,120 200,80 300,100 400,60 500,90"
                    />

                    {/* Forecast line (dotted) */}
                    <polyline
                      fill="none"
                      stroke="#3b82f6"
                      strokeWidth="3"
                      strokeDasharray="8,4"
                      points="500,90 600,85 700,95"
                    />

                    {/* Area under line */}
                    <polygon
                      fill="url(#revenueGradient)"
                      points="100,120 200,80 300,100 400,60 500,90 500,160 100,160"
                    />

                    {/* Data points */}
                    {[
                      { x: 100, y: 120, value: "$2.1k" },
                      { x: 200, y: 80, value: "$3.2k" },
                      { x: 300, y: 100, value: "$2.8k" },
                      { x: 400, y: 60, value: "$4.1k" },
                      { x: 500, y: 90, value: "$3.5k" },
                    ].map((point, i) => (
                      <g key={i}>
                        <circle
                          cx={point.x}
                          cy={point.y}
                          r="4"
                          fill="#3b82f6"
                        />
                        <circle
                          cx={point.x}
                          cy={point.y}
                          r="8"
                          fill="#3b82f6"
                          fillOpacity="0.2"
                        />
                      </g>
                    ))}

                    {/* X-axis labels */}
                    {[
                      "Sep 15",
                      "Sep 16",
                      "Sep 17",
                      "Sep 18",
                      "Sep 19",
                      "Sep 20",
                      "Sep 21",
                    ].map((date, i) => (
                      <text
                        key={i}
                        x={100 + i * 100}
                        y="185"
                        textAnchor="middle"
                        fontSize="12"
                        fill="#666"
                      >
                        {date}
                      </text>
                    ))}
                  </svg>
                </div>
                <div className="revenue-summary">
                  <div className="summary-item">
                    <span className="summary-label">Total Revenue</span>
                    <span className="summary-value">$10m</span>
                  </div>
                  <div className="summary-item">
                    <span className="summary-label">Average Daily</span>
                    <span className="summary-value">$350k</span>
                  </div>
                  <div className="summary-item">
                    <span className="summary-label">Growth</span>
                    <span className="summary-value growth-positive">
                      +12.5%
                    </span>
                  </div>
                </div>
              </div>
            </div>
          )}
          {activeTab === "pending" && (
            <div>
              <div className="filter-section">
                <h2 className="payment-title">Closed Opportunities</h2>
                <div className="custom-dropdown" ref={invoiceDropdownRef}>
                  <div
                    className={`dropdown-trigger ${
                      invoiceDropdownOpen ? "open" : ""
                    }`}
                    onClick={() => setInvoiceDropdownOpen(!invoiceDropdownOpen)}
                  >
                    <span>
                      {invoiceStatusFilter === "all"
                        ? "All Status"
                        : invoiceStatusFilter.charAt(0).toUpperCase() +
                          invoiceStatusFilter.slice(1)}
                    </span>
                    <svg
                      className={`dropdown-arrow ${
                        invoiceDropdownOpen ? "open" : ""
                      }`}
                      width="12"
                      height="12"
                      viewBox="0 0 12 12"
                    >
                      <path
                        d="M3 4.5L6 7.5L9 4.5"
                        stroke="currentColor"
                        strokeWidth="1.5"
                        fill="none"
                      />
                    </svg>
                  </div>
                  {invoiceDropdownOpen && (
                    <div className="dropdown-menu">
                      {[
                        "all",
                        "pending",
                        "processing",
                        "success",
                        "failed",
                        "overdue",
                      ].map((status) => (
                        <div
                          key={status}
                          className={`dropdown-item ${
                            invoiceStatusFilter === status ? "active" : ""
                          }`}
                          onClick={() => {
                            setInvoiceStatusFilter(status);
                            setInvoiceDropdownOpen(false);
                          }}
                        >
                          {status === "all"
                            ? "All Status"
                            : status.charAt(0).toUpperCase() + status.slice(1)}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
              <div className="payment-list">
                <div className="payment-header">
                  <div className="header-cell">No.</div>
                  <div className="header-cell">Opportunity Name</div>
                  <div className="header-cell">Date</div>
                  <div className="header-cell">Status</div>
                  <div className="header-cell">Action</div>
                </div>
                {closedOpportunities.map((opportunity, index) => (
                  <div
                    key={opportunity.opportunity_name}
                    className="payment-row"
                  >
                    <div className="payment-cell">{index + 1}</div>
                    <div className="payment-cell">
                      {opportunity.opportunity_name}
                    </div>
                    <div className="payment-cell">{opportunity.date}</div>
                    <div className="payment-cell">
                      <span
                        className={`status-badge ${opportunity.status
                          .toLowerCase()
                          .replace(" ", "-")}`}
                      >
                        {opportunity.status}
                      </span>
                    </div>
                    <div className="payment-cell">
                      <button
                        className="invoice-btn"
                        onClick={() => {
                          const message = `Generate Invoice for Opportunity ${opportunity.opportunity_name}`;
                          setMessages((prev) => [
                            ...prev,
                            { text: message, isUser: true },
                          ]);
                          if (ws && isConnected) {
                            ws.send(message);
                          }
                        }}
                      >
                        Generate Invoice
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
          {activeTab === "overdue" && (
            <div>
              <div className="filter-section">
                <h2 className="payment-title">Overdue Recurring Invoices</h2>
              </div>
              <div className="payment-list">
                <div className="payment-header">
                  <div className="header-cell">No.</div>
                  <div className="header-cell">Invoice ID</div>
                  <div className="header-cell">Issued Date</div>
                  <div className="header-cell">Overdue Days</div>
                  <div className="header-cell">Action</div>
                </div>
                {overdueInvoices.map((invoice, index) => (
                  <div key={invoice.invoice_id} className="payment-row">
                    <div className="payment-cell">{index + 1}</div>
                    <div className="payment-cell">{invoice.invoice_id}</div>
                    <div className="payment-cell">
                      {new Date(invoice.created_at).toLocaleDateString()}
                    </div>
                    <div className="payment-cell">{invoice.overdue_days}</div>
                    <div className="payment-cell">
                      <button
                        className="reminder-btn"
                        onClick={() => {
                          const message = `Send reminder to invoice ${invoice.invoice_id}`;
                          setMessages((prev) => [
                            ...prev,
                            { text: message, isUser: true },
                          ]);
                          if (ws && isConnected) {
                            ws.send(message);
                          }
                        }}
                      >
                        Send Reminder
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      <div className="right-column">
        <div className="chat-container">
          <div className="chat-header">
            <h3>Live Agent</h3>
          </div>
          <div className="messages">
            {messages.map((msg, idx) => (
              <div key={idx} className={`message-wrapper ${msg.isUser ? 'user' : 'bot'}`}>
                {!msg.isUser && <div className="agent-icon">
                  <img src="/chatbot icon.svg" alt="Agent" width="16" height="16" />
                </div>}
                {msg.type === 'invoice_preview' ? (
                  <InvoicePreview 
                    invoice={msg} 
                    onApprove={() => handleInvoiceAction('approve', msg)}
                    onEdit={() => handleInvoiceAction('edit', msg)}
                  />
                ) : (
                  <div
                    className={`message-bubble ${msg.isUser ? "user" : "bot"}`}
                  >
                    {msg.text}
                  </div>
                )}
              </div>
            ))}
            {isTyping && (
              <div className="message agent-message">
                <div className="typing-indicator">
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          <div className="input-area">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={(e) => e.key === "Enter" && sendMessage()}
              placeholder="Type your message..."
              className="input"
            />
            <button
              onClick={sendMessage}
              className="send-button"
              disabled={!isConnected}
            >
              {isConnected ? "Send" : "Connecting..."}
            </button>
          </div>
        </div>
      </div>

      {reminderModalOpen && (
        <div
          className="modal-overlay"
          onClick={() => setReminderModalOpen(false)}
        >
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h3>Send Reminder to {selectedPayment?.user}</h3>
            <div className="method-selection">
              <div>
                <label
                  className={reminderMethod.includes("email") ? "selected" : ""}
                >
                  <input
                    type="checkbox"
                    checked={reminderMethod.includes("email")}
                    onChange={() => handleMethodChange("email")}
                  />
                  {reminderMethod.includes("email") && (
                    <div className="selection-dot"></div>
                  )}
                  <div
                    style={{
                      display: "flex",
                      flexDirection: "column",
                      alignItems: "center",
                      gap: "8px",
                      justifyContent: "center",
                      height: "100%",
                    }}
                  >
                    <img src="/mail.svg" alt="Email" width="36" height="36" />
                    <span style={{ fontSize: "14px" }}>Email</span>
                  </div>
                </label>
              </div>
              <div>
                <label
                  className={
                    reminderMethod.includes("whatsapp") ? "selected" : ""
                  }
                >
                  <input
                    type="checkbox"
                    checked={reminderMethod.includes("whatsapp")}
                    onChange={() => handleMethodChange("whatsapp")}
                  />
                  {reminderMethod.includes("whatsapp") && (
                    <div className="selection-dot"></div>
                  )}
                  <div
                    style={{
                      display: "flex",
                      flexDirection: "column",
                      alignItems: "center",
                      gap: "8px",
                      justifyContent: "center",
                      height: "100%",
                    }}
                  >
                    <svg
                      width="36"
                      height="36"
                      viewBox="0 0 24 24"
                      fill="#25D366"
                    >
                      <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893A11.821 11.821 0 0020.893 3.488" />
                    </svg>
                    <span style={{ fontSize: "14px" }}>WhatsApp</span>
                  </div>
                </label>
              </div>
            </div>
            <div className="modal-buttons">
              <button
                className="send-btn"
                onClick={handleSendReminder}
                disabled={reminderMethod.length === 0}
              >
                Send
              </button>
              <button
                className="cancel-btn"
                onClick={() => setReminderModalOpen(false)}
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
