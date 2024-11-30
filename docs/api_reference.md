# API Reference

The **H(t) Zkaedi Healing Solution Dashboard** offers a set of API endpoints to facilitate data integration, retrieval, and manipulation. This reference guide provides detailed information about each endpoint, including request methods, parameters, responses, and examples.

## Table of Contents

- [Authentication](#authentication)
- [Patient Data](#patient-data)
  - [Retrieve All Patients](#retrieve-all-patients)
  - [Retrieve Single Patient](#retrieve-single-patient)
  - [Create New Patient](#create-new-patient)
  - [Update Patient](#update-patient)
  - [Delete Patient](#delete-patient)
- [Reports](#reports)
  - [Generate Healing Progress Report](#generate-healing-progress-report)
- [Utilities](#utilities)
  - [Health Check](#health-check)

## Authentication

All API endpoints (except `Health Check`) require authentication using JWT tokens.

### **Login**

- **Endpoint:** `/api/login`
- **Method:** `POST`
- **Description:** Authenticates a user and returns a JWT token.

#### **Request Body**

```json
{
  "username": "user123",
  "password": "securepassword"
}
