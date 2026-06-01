# Frontend Engineering Guide

# Frontend Stack

Framework:

* Next.js

UI:

* Tailwind CSS
* ShadCN UI

State Management:

* Zustand or Redux Toolkit

---

# Frontend Goals

The frontend must:

* look modern
* support real-time updates
* remain modular
* be scalable
* support enterprise dashboards

---

# Frontend Structure

```text id="v2sp8s"
frontend/
├── app/
├── components/
├── services/
├── hooks/
├── store/
├── types/
├── lib/
└── styles/
```

---

# Component Rules

Rules:

* reusable components only
* separate logic from UI
* avoid duplicated components
* keep components isolated

---

# API Communication

Use:

* Axios
* centralized API service layer

Requirements:

* token interceptors
* error handling
* retry logic

---

# Authentication Handling

Store:

* access token
* refresh token

Rules:

* auto-refresh expired tokens
* protect private routes
* redirect unauthorized users

---

# UI Standards

Requirements:

* responsive design
* accessibility support
* consistent spacing
* loading states
* error states

---

# Dashboard Features

Pages:

* login
* dashboard
* workflow builder
* workflow history
* logs
* notifications
* AI analytics

---

# Real-Time Features

Use:

* WebSockets

Real-time updates:

* workflow status
* notifications
* execution progress

---

# Form Standards

Use:

* React Hook Form
* Zod validation

Requirements:

* client validation
* server validation
* reusable form components

---

# State Management Strategy

Global state:

* authentication
* notifications
* workflow execution status

Local state:

* form inputs
* modal states
* temporary UI state

---

# Frontend Security

Rules:

* never store secrets in frontend
* sanitize user inputs
* protect against XSS
* secure token storage

---

# Future Frontend Enhancements

Future upgrades:

* drag-and-drop workflow builder
* AI workflow recommendations
* multi-tenant dashboards
* advanced analytics
