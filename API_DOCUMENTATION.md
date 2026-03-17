# Django Ecommerce & MLM API Documentation

**Base URL**: `http://127.0.0.1:8000/web/api/`

**Authentication**:
Most APIs require an Authentication Token.
- **Header**: `Authorization: Token <your_token_here>`

**Request Format**:
- **Method**: `POST` (for almost all dynamic APIs)
- **Content-Type**: `application/json`
- **Body**: Must include `api_key` and other required parameters.

---

## 1. Authentication & User

### Login User
- **Key**: `4276502b-a9c5-4c2d-ad12-47eb44e405b0`
- **Auth Required**: No
- **Payload**:
  ```json
  {
    "api_key": "4276502b-a9c5-4c2d-ad12-47eb44e405b0",
    "username": "VEDAON_1234567",
    "password": "your_password"
  }
  ```

### Register User
- **Key**: `6ab0ccc6-240d-4940-9127-9782634a029a`
- **Auth Required**: No
- **Payload**:
  ```json
  {
    "api_key": "6ab0ccc6-240d-4940-9127-9782634a029a",
    "name": "New User",
    "mobile": "9876543210", 
    "password": "securepassword",
    "sponsor_id": "1", 
    "position": "L"
  }
  ```

### Change Password
- **Key**: `d97926fe-720e-4aa8-b632-0892d95191db`
- **Auth Required**: Yes

### Manage Address
- **Key**: `7adbecd8-7b07-4abd-96d4-f5e60863e787`
- **Auth Required**: Yes
- **Actions**: `add`, `edit`, `delete`, `get`

### Manage KYC
- **Key**: `cadcbdcb-77d3-4caa-bca0-02dce1b704da`
- **Auth Required**: Yes
- **Actions**: `create`, `edit`, `get`
- **Payload (Create/Edit)**:
  ```json
  {
      "api_key": "cadcbdcb-77d3-4caa-bca0-02dce1b704da",
      "action": "create",
      "name_on_card": "John Doe",
      "aadhar_number": "123456789012",
      "pan_number": "ABCDE1234F",
      "bank_name": "State Bank of India",
      "bank_account_number": "1234567890",
      "ifsc_code": "SBIN0001234",
      "account_holder_name": "John Doe"
  }
  ```

---

## 2. MLM & Network

### Get MLM Dashboard
- **Key**: `91b1f76e-f709-499f-9e78-831ec42581e5`
- **Auth Required**: Yes

### Get Binary Tree
- **Key**: `c98492f9-3d00-4866-b84b-173908a53fa8`
- **Auth Required**: Yes

### Get Level Members
- **Key**: `5cbe44fd-efcb-44be-8779-ac6080d102f5`
- **Auth Required**: Yes

### Get Wallet
- **Key**: `1dd91f8e-d275-4f02-9bab-519d92f73574`
- **Auth Required**: Yes

### Create Payin Request
- **Key**: `31940984-7a91-4966-9b51-344cb89d98e8`
- **Auth Required**: Yes

---

## 3. Ecommerce

### Home Data
- **Key**: `d8350bc5-6495-46c5-8f6b-3136706e5d8b`
- **Auth Required**: No

### Get Category Products
- **Key**: `75a11d53-96cb-4490-9416-52578b4a4c97`
- **Auth Required**: No (Public)
- **Response**: List of Categories with nested Products.

### Get Profile
- **Key**: `9165d506-c87a-4299-abe1-de6a05952d43`
- **Auth Required**: Yes

### Get Cart
- **Key**: `a1e0954b-d729-4e00-8809-9fb4bf6e9ac8`
- **Auth Required**: Yes

### Add to Cart
- **Key**: `99a07156-f831-4a4b-84a2-9e992d95ea7f`
- **Auth Required**: Yes

### Remove from Cart
- **Key**: `a488e367-e9fa-47fa-b39b-cd7894a7e914`
- **Auth Required**: Yes

### Checkout
- **Key**: `24b525f0-5716-43a0-be7f-8566ef74e92e`
- **Auth Required**: Yes

---

## 4. Support

### Get Tickets
- **Key**: `d7f280ee-fc38-4d06-af6a-5d2305aac978`

### Create Ticket
- **Key**: `46286291-67f3-4afa-b19b-92f8e00328ab`

---

## 5. Coupons

### Get Coupons
- **Key**: `684c4e19-79d4-43df-a8e1-efd3aea6a50c`
- **Auth Required**: Yes
- **Response**: List of user's coupons.

### Redeem Coupon
- **Key**: `db3f80b1-64e7-4ef8-bc11-6650031f05cf`
- **Auth Required**: Yes
- **Payload**:
  ```json
  {
      "api_key": "db3f80b1-64e7-4ef8-bc11-6650031f05cf",
      "coupon_id": 1
  }
  ```
- **Effect**: Credits coupon amount to wallet.
