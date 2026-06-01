# Backend API contract & changes (barter-backend)

Django/DRF changes and **exact JSON shapes** required for the Flutter app (`barter_app/`). Cross-checked against:

- Mock data: [`barter_app/assets/mock/`](../barter_app/assets/mock/)
- Flutter models: [`barter_app/lib/data/models/`](../barter_app/lib/data/models/)
- Screens: [`barter_app/lib/features/`](../barter_app/lib/features/)

**OpenAPI (after changes):** `GET /api/schema/` · Swagger: `/api/docs/`  
**Backend repo:** `/Users/vaibhavnanda/CascadeProjects/barter-backend/`

**Product rules:** No payment gateway; creator **Pro** (`membership.pro_active`) gates deals. All JSON field names are **snake_case** on the wire (Flutter mappers convert to UI camelCase where needed).

---

## Table of contents

1. [Global conventions](#1-global-conventions)
2. [Mock → screen → endpoint matrix](#2-mock--screen--endpoint-matrix)
3. [Enums & shared objects](#3-enums--shared-objects)
4. [Auth & users](#4-auth--users)
5. [Offers](#5-offers)
6. [Proposals](#6-proposals)
7. [Deals & deal room](#7-deals--deal-room)
8. [Membership (subscription / Pro)](#8-membership-subscription--pro)
9. [Drops](#9-drops)
10. [Brand dashboard, discovery, inbox, pipeline](#10-brand-dashboard-discovery-inbox-pipeline)
11. [Analytics](#11-analytics)
12. [Notifications, ratings, contracts](#12-notifications-ratings-contracts)
13. [P0 behaviour changes (no new routes)](#13-p0-behaviour-changes-no-new-routes)
14. [Out of scope](#14-out-of-scope)
15. [Implementation order & files](#15-implementation-order--files)

---

## 1. Global conventions

### Pagination (all list endpoints)

```json
{
  "count": 124,
  "next": "http://127.0.0.1:8000/api/offers/?page=2",
  "previous": null,
  "results": [ ]
}
```

Flutter mock often uses custom wrappers (e.g. `{ "offers": [], "resultCount": 124 }`). **Do not change DRF pagination**; Flutter adapts in repositories.

### Auth header

```
Authorization: Bearer <access_jwt>
```

### Error responses (validation / 4xx)

```json
{
  "detail": "Human-readable message"
}
```

Or field errors:

```json
{
  "email": ["This field is required."],
  "deliverables": ["This field is required."]
}
```

### Dates

- **Date:** `"2025-06-15"` (ISO 8601 date)
- **DateTime:** `"2025-06-15T10:30:00Z"` (ISO 8601 UTC)

---

## 2. Mock → screen → endpoint matrix

| Mock file | Flutter model / provider | Screen(s) | Primary API(s) |
|-----------|--------------------------|-----------|----------------|
| `onboarding.json` | `OnboardingConfig` | Creator/brand onboarding | **NEW** `GET /api/config/onboarding/` |
| `offers.json` | `OffersPayload` / `OfferModel` | `creator_home_feed_screen`, `offer_feed_screen` | `GET /api/offers/` |
| `offer_detail.json` | (inline / partial) | `offer_detail_screen` | `GET /api/offers/:id/` |
| `membership.json` | `MembershipPayload` | `earn_membership_screen`, `submit_task_screen`, `membership_gate` | `GET /api/membership/status/`, `GET /api/membership/tasks/`, `POST /api/membership/submissions/` |
| `deal_room.json` | `DealRoomModel` | `deal_room_screen` | `GET /api/deals/:id/`, `GET .../messages/` |
| `pipeline.json` | `PipelinePayload` | `deal_pipeline_screen` | **NEW** `GET /api/brands/pipeline/` or compose proposals+deals |
| `proposal_inbox.json` | (static) | `proposal_inbox_screen`, `review_proposal_screen` | `GET /api/proposals/?status=pending` + **expand** serializer |
| `brand_dashboard_data.json` | `BrandDashboardData` | `brand_dashboard_screen` | **NEW** `GET /api/brands/dashboard/` or aggregate |
| `brand_discovery_data.json` | `BrandDiscoveryData` | `creator_discovery_screen`, `brand_inbox_screen` | `GET /api/users/creators/`, **NEW** `GET /api/brands/inbox/` |
| `brand_profile_data.json` | `BrandProfile` | `brand_profile_screen` | `GET /api/users/me/` + `GET /api/offers/my/` |
| `analytics.json` | `AnalyticsPayload` (+ extra charts in UI) | `analytics_dashboard_screen` | `GET /api/analytics/deals/` (+ extend) |
| `drops_campaign_data.json` | (static) | `drops_dashboard_screen`, `create_drops_campaign_screen` | `GET/POST /api/drops/` |
| `counter_offer_data.json` | (static) | `counter_offer_screen` | `POST /api/proposals/:id/counter/` |
| `creator_profile_data.json` | (hardcoded UI) | `creator_profile_screen` | `GET /api/users/me/`, `GET /api/users/:id/` |
| `creator_kpi_metrics.json` | (hardcoded) | `kpi_showcase_screen` | **NEW** or derive from social_accounts |
| `offer_feed.json` | Same as `offers.json` | `offer_feed_screen` | `GET /api/offers/` |
| `deal_pipeline_data.json` | Same as `pipeline.json` | `deal_pipeline_screen` | **NEW** `GET /api/brands/pipeline/` |
| `draft_proposals.json` | — | (future drafts UI) | **NEW** optional `GET /api/proposals/drafts/` |
| `barter_exchange_data.json` | — | `barter_value_engine_screen` | `GET /api/offers/:id/value-engine/` |
| `creator_niches.json` | — | onboarding pickers | **NEW** `GET /api/config/onboarding/` |
| `creator_interests.json` | — | onboarding pickers | same |
| `creator_content_types.json` | — | onboarding pickers | same |
| `social_platforms.json` | — | `connect_socials_screen` | same + OAuth URLs |

---

## 3. Enums & shared objects

### User `role`

`brand` | `creator` | `both`

### Offer `type`

`saas` | `physical` | `event_pass` | `experience` | `merchandise` | `course` | `gift_card`

### Offer `status`

`draft` | `live` | `paused` | `closed`

### Offer `currency`

`INR` | `AED` | `USD`

### Offer `rights_tier` / deal `rights_tier`

`none` | `standard` | `extended` | `buyout`

### Offer `exclusivity`

`none` | `category_30` | `full_60`

### Proposal `status`

`pending` | `countered` | `accepted` | `declined` | `expired`

### Deal `status`

`pending_membership` | `active` | `delivered` | `revision_requested` | `complete` | `disputed` | `cancelled`

### Membership task `platform`

`instagram` | `tiktok` | `open`

### Creator `tier`

`nano` | `micro` | `mid` | `macro` | `mega`

### Drops campaign `status`

`draft` | `live` | `closed` (confirm in model)

### Drops `approval_mode`

`auto` | `manual`

### `content_ask` (JSON on Offer)

```json
{
  "types": ["reel", "story", "carousel"],
  "platforms": ["instagram", "tiktok"],
  "count": 3
}
```

### `kpi_preferences` (JSON on Offer)

```json
{
  "niches": ["skincare", "beauty"],
  "min_followers": 50000,
  "min_engagement": 3.0
}
```

### `deliverables` (JSON on Proposal)

```json
{
  "types": ["reel", "story"],
  "platforms": ["instagram"],
  "count": 1,
  "details": "Optional free-text summary for brand"
}
```

### `agreed_terms` (JSON on Deal — set at accept)

```json
{
  "offer_title": "Smart Studio Display v2",
  "offer_type": "physical",
  "offer_estimated_value": "45500.00",
  "creator_deliverables": { "types": ["reel"], "platforms": ["instagram"], "count": 1 },
  "timeline": "2025-12-01",
  "rights_tier": "standard",
  "raw_files_required": false,
  "exclusivity": "none"
}
```

### `shipping_address` (JSON on ship)

```json
{
  "name": "Priya Sharma",
  "line1": "12 MG Road",
  "line2": "Apt 4B",
  "city": "Bangalore",
  "state": "Karnataka",
  "postal_code": "560001",
  "country": "IN",
  "phone": "+919876543210"
}
```

---

## 4. Auth & users

### `POST /api/auth/register/` — **exists**

**Request:**

```json
{
  "email": "creator@example.com",
  "password": "securepass123",
  "password_confirm": "securepass123",
  "role": "creator",
  "name": "Priya Sharma",
  "username": "priya_lifestyle",
  "bio": "",
  "location_city": "Mumbai",
  "location_country": "IN"
}
```

**Response `201`:**

```json
{
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "creator@example.com",
    "role": "creator",
    "name": "Priya Sharma",
    "username": "priya_lifestyle",
    "bio": "",
    "location_city": "Mumbai",
    "location_country": "IN",
    "profile_photo_url": "",
    "is_verified": false,
    "barter_score": "0.0",
    "created_at": "2025-01-15T08:00:00Z"
  },
  "message": "User created successfully"
}
```

**Screen:** `sign_in_screen.dart` (register flow)

---

### `GET /api/config/onboarding/` — **NEW (P1)**

Single payload for creator/brand onboarding pickers (replaces split mock files).

**Response `200`** (from `onboarding.json` + related mocks; API uses snake_case):

```json
{
  "niches": ["Beauty", "Skincare", "Fashion"],
  "interests": ["UGC", "Editorial", "Product Reviews"],
  "content_types": [
    "Instagram Reels",
    "Instagram Stories",
    "TikTok Videos"
  ],
  "platforms": [
    { "id": "instagram", "label": "Instagram", "color": "#E1306C" },
    { "id": "youtube", "label": "YouTube", "color": "#FF0000" }
  ],
  "follower_ranges": [
    { "id": "nano", "label": "Nano", "range": "1K–10K" },
    { "id": "micro", "label": "Micro", "range": "10K–50K" }
  ],
  "creator_profile_defaults": {
    "suggested_name": "Elena Rossi",
    "suggested_handle": "elenarossi",
    "suggested_bio": "Fashion & lifestyle content creator...",
    "suggested_location": "Milan, Italy",
    "default_avatar": "https://ui-avatars.com/api/?name=..."
  },
  "brand_profile_defaults": {
    "avatar_url": "https://...",
    "suggested_company_name": "Aura Collective",
    "suggested_industry": "Beauty & Wellness"
  }
}
```

**Screens:** `creator_onboarding_flow_screen.dart`, `brand_onboarding_screen.dart`, `connect_socials_screen.dart`

---

### `POST /api/auth/login/` — **exists** (SimpleJWT)

**Request:**

```json
{
  "email": "creator@example.com",
  "password": "securepass123"
}
```

**Response `200`:**

```json
{
  "access": "eyJ...",
  "refresh": "eyJ..."
}
```

---

### `POST /api/auth/token/refresh/` — **exists**

**Request:**

```json
{
  "refresh": "eyJ..."
}
```

**Response `200`:**

```json
{
  "access": "eyJ...",
  "refresh": "eyJ..."
}
```

---

### `GET /api/users/me/` — **exists**

**Response `200`:**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "creator@example.com",
  "role": "creator",
  "name": "Priya Sharma",
  "username": "priya_lifestyle",
  "bio": "Fashion & lifestyle creator",
  "location_city": "Mumbai",
  "location_country": "IN",
  "profile_photo_url": "https://cdn.example/avatar.jpg",
  "is_verified": true,
  "barter_score": "4.8",
  "brand_profile": null,
  "creator_profile": {
    "id": "660e8400-e29b-41d4-a716-446655440001",
    "niches": ["Skincare", "Beauty"],
    "content_types": ["Instagram Reels", "Instagram Stories"],
    "tier": "micro"
  },
  "social_accounts": [
    {
      "id": "770e8400-e29b-41d4-a716-446655440002",
      "platform": "instagram",
      "handle": "@priyasharma",
      "followers": 170000,
      "engagement_rate": 4.8,
      "avg_views": 42000,
      "demographics": {},
      "last_synced": "2025-01-20T10:00:00Z",
      "created_at": "2024-06-01T08:00:00Z"
    }
  ],
  "created_at": "2024-06-01T08:00:00Z",
  "updated_at": "2025-01-20T10:00:00Z"
}
```

**Mock gap:** `onboarding.json` → `creatorProfile.suggestedName` etc. are UI-only hints, not on User.

**Screen:** Post-login routing, profiles

---

### `PATCH /api/users/me/creator-profile/` — **exists**

**Request (maps from onboarding selections):**

```json
{
  "niches": ["Skincare", "Tech"],
  "content_types": ["Instagram Reels", "TikTok Videos"]
}
```

**Response:** Same shape as `creator_profile` inside `GET /api/users/me/`.

**Mock ref:** `onboarding.json` → `niches`, `contentTypes`  
**Screen:** `creator_onboarding_flow_screen.dart` — **must call on finish** (not wired yet)

---

### `PATCH /api/users/me/brand-profile/` — **exists**

**Request:**

```json
{
  "company_name": "Aura Collective",
  "website": "https://auracollective.co",
  "industry": "Beauty & Wellness"
}
```

**Response:**

```json
{
  "id": "880e8400-e29b-41d4-a716-446655440003",
  "company_name": "Aura Collective",
  "website": "https://auracollective.co",
  "industry": "Beauty & Wellness",
  "logo_url": "",
  "domain_verified": false
}
```

**Mock ref:** `onboarding.json` → `brandProfile`  
**Screen:** `brand_identity_screen.dart`, `brand_onboarding_screen.dart`

---

### `GET /api/users/creators/` — **exists** (extend)

**Query params:** `niche`, `tier`, `platform`, `min_followers`, `max_followers`, `search`, `ordering`

**Target item** (extend `CreatorListSerializer` for discovery cards):

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Priya Sharma",
  "username": "priya_lifestyle",
  "bio": "...",
  "location_city": "Mumbai",
  "location_country": "IN",
  "profile_photo_url": "https://...",
  "is_verified": true,
  "barter_score": "94.0",
  "creator_profile": {
    "id": "...",
    "niches": ["Beauty", "Skincare"],
    "content_types": ["Instagram Reels"],
    "tier": "micro"
  },
  "social_accounts": [ ],
  "total_followers": 170000,
  "avg_engagement_rate": 4.8,
  "past_collabs": 24,
  "primary_niche": "Beauty",
  "platforms": ["instagram", "youtube"],
  "tags": ["Clean Beauty", "Skincare"]
}
```

**Mock ref:** `brand_discovery_data.json` → `creators[]` (camelCase in mock; API uses snake_case)  
**Screen:** `creator_discovery_screen.dart`

---

### `GET /api/auth/oauth/:platform/url/` — **exists**

**Query:** `redirect_uri`, `state`

**Response:**

```json
{
  "platform": "instagram",
  "auth_url": "https://..."
}
```

**Screen:** `connect_socials_screen.dart` (not wired)

---

## 5. Offers

### `GET /api/offers/` — **exists** (public list)

**Query params:** `type`, `status`, `currency`, `rights_tier`, `exclusivity`, `niche`, `market`, `drops`, `min_value`, `max_value`, `search`, `ordering`, `page`

**Current `results[]` item (`OfferListSerializer`):**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440010",
  "brand_username": "lumix_home",
  "brand_name": "Lumix Home",
  "type": "physical",
  "title": "Smart Studio Display v2 Exchange",
  "estimated_value": "45500.00",
  "currency": "INR",
  "quantity_remaining": 5,
  "status": "live",
  "content_ask": {
    "types": ["reel", "story"],
    "platforms": ["instagram"],
    "count": 3
  },
  "created_at": "2025-01-10T12:00:00Z"
}
```

**Target `results[]` item** (for feed cards — maps mock `offers.json`):

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440010",
  "brand_username": "lumix_home",
  "brand_name": "Lumix Home",
  "brand_logo_url": "https://cdn.example/logo.png",
  "brand_company_name": "Lumix Home Pvt Ltd",
  "type": "physical",
  "title": "Smart Studio Display v2 Exchange",
  "estimated_value": "45500.00",
  "currency": "INR",
  "quantity_remaining": 5,
  "status": "live",
  "content_ask": { "types": ["reel", "story"], "platforms": ["instagram"], "count": 3 },
  "images": ["https://cdn.example/hero.jpg"],
  "match_score": 92,
  "is_drops": false,
  "created_at": "2025-01-10T12:00:00Z"
}
```

Flutter maps to UI: `brandName`, `brandLogoUrl`, `estimatedValueLabel`, `offerTypeLabel`, `requirementTags`, `matchTag`, `heroImageUrl` (see `offer_mapper.dart`).

**Mock ref:** `offers.json`  
**Screens:** `creator_home_feed_screen.dart`, `offer_feed_screen.dart` (must wire)

---

### `GET /api/offers/:id/` — **exists**

**Current response (`OfferSerializer`) — key fields:**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440010",
  "brand": "440e8400-e29b-41d4-a716-446655440099",
  "brand_username": "glow_lab",
  "brand_name": "Glow Lab",
  "brand_company_name": "Glow Lab Inc",
  "type": "physical",
  "title": "Glow Lab Serum Review",
  "description": "Review our new vitamin C serum...",
  "estimated_value": "7500.00",
  "currency": "INR",
  "quantity": 10,
  "quantity_remaining": 8,
  "status": "live",
  "content_ask": { "types": ["reel"], "platforms": ["instagram"], "count": 1 },
  "kpi_preferences": { "niches": ["skincare"], "min_followers": 50000, "min_engagement": 3.0 },
  "rights_tier": "standard",
  "raw_files_required": false,
  "exclusivity": "none",
  "images": ["https://..."],
  "attachments": [],
  "proposal_deadline": "2025-02-10T23:59:59Z",
  "max_proposals": 25,
  "shipping_required": true,
  "proposal_count": 12,
  "is_drops": false,
  "created_at": "2025-01-20T08:00:00Z",
  "updated_at": "2025-01-20T08:00:00Z"
}
```

**Mock ref:** `offer_detail.json` (camelCase, richer nested `requirements` / `rights` — Flutter can map from flat offer fields + enums)

**Screen:** `offer_detail_screen.dart`, `proposal_compose_screen.dart`

---

### `POST /api/offers/` — **exists** (brand only)

**Request (`OfferCreateSerializer`):**

```json
{
  "type": "physical",
  "title": "Spring Glow Collection Launch",
  "description": "Launch our new summer skincare collection with creator exchanges.",
  "estimated_value": "12000.00",
  "currency": "INR",
  "quantity": 5,
  "status": "live",
  "content_ask": {
    "types": ["reel", "story"],
    "platforms": ["instagram"],
    "count": 4
  },
  "kpi_preferences": {
    "niches": ["skincare", "beauty"],
    "min_followers": 10000,
    "min_engagement": 2.5
  },
  "rights_tier": "standard",
  "raw_files_required": false,
  "exclusivity": "category_30",
  "images": ["https://cdn.example/offer-hero.jpg"],
  "attachments": [],
  "proposal_deadline": "2025-03-01T23:59:59Z",
  "max_proposals": 30,
  "shipping_required": true
}
```

**Response `201`:** Full `OfferSerializer` object.

**Mock ref:** Create-offer wizard fields in `create_offer_*_screen.dart`  
**Screen:** `create_offer_details_screen.dart`, `create_offer_requirements_screen.dart`, `create_offer_rights_screen.dart` (not wired)

---

### `GET /api/offers/:id/value-engine/` — **exists**

**Response (`ValueEngineSerializer`):**

```json
{
  "offer_id": "550e8400-e29b-41d4-a716-446655440010",
  "estimated_value": "45500.00",
  "currency": "INR",
  "recommended_content_types": ["reel", "story"],
  "recommended_platforms": ["instagram", "tiktok"],
  "recommended_post_count": 3,
  "estimated_engagement": 42000,
  "similar_offers_count": 8
}
```

**Screen:** `barter_value_engine_screen.dart`

---

### `GET /api/offers/my/` — **exists** (brand's offers)

Same list item shape as `GET /api/offers/` but filtered to authenticated brand. Used for campaigns list / brand profile previews.

---

## 6. Proposals

### `POST /api/offers/:offer_id/proposals/` — **exists** (creator)

**Request (`ProposalCreateSerializer`):**

```json
{
  "offer": "550e8400-e29b-41d4-a716-446655440010",
  "pitch": "I'd love to collaborate! I've used your products for 6 months...",
  "deliverables": {
    "types": ["reel", "story"],
    "platforms": ["instagram"],
    "count": 1,
    "details": "Morning routine integration"
  },
  "timeline": "2025-11-24"
}
```

**Response `201`:** `ProposalSerializer` (see below).

**Screen:** `proposal_compose_screen.dart`

---

### `GET /api/proposals/` — **exists** (extend filters)

**Query params (add):** `status`, `offer_id`, `page`

**Current `results[]` (`ProposalListSerializer`) — too thin for inbox:**

```json
{
  "id": "660e8400-e29b-41d4-a716-446655440020",
  "offer_title": "Glow Lab Serum Review",
  "offer_brand_username": "glow_lab",
  "creator_username": "priya_lifestyle",
  "status": "pending",
  "round_number": 1,
  "created_at": "2025-01-28T10:00:00Z"
}
```

**Target list item** (inbox card) OR use `?expand=1` with full serializer:

```json
{
  "id": "660e8400-e29b-41d4-a716-446655440020",
  "status": "pending",
  "round_number": 1,
  "created_at": "2025-01-28T10:00:00Z",
  "pitch": "I'd love to collaborate...",
  "deliverables": { "types": ["reel"], "platforms": ["instagram"], "count": 1 },
  "timeline": "2025-02-15",
  "match_score": 95,
  "offer": {
    "id": "550e8400-e29b-41d4-a716-446655440010",
    "title": "Glow Lab Serum Review",
    "estimated_value": "7500.00",
    "currency": "INR"
  },
  "creator": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "Priya Sharma",
    "username": "priya_lifestyle",
    "profile_photo_url": "https://..."
  }
}
```

**Mock ref:** `proposal_inbox.json`  
**Screens:** `proposal_inbox_screen.dart`, `review_proposal_screen.dart`

---

### `GET /api/proposals/:id/` — **exists**

**Response (`ProposalSerializer`):**

```json
{
  "id": "660e8400-e29b-41d4-a716-446655440020",
  "offer": "550e8400-e29b-41d4-a716-446655440010",
  "offer_title": "Glow Lab Serum Review",
  "offer_brand_username": "glow_lab",
  "creator": "550e8400-e29b-41d4-a716-446655440000",
  "creator_username": "priya_lifestyle",
  "creator_name": "Priya Sharma",
  "pitch": "...",
  "deliverables": { "types": ["reel"], "platforms": ["instagram"], "count": 1 },
  "timeline": "2025-02-15",
  "round_number": 1,
  "status": "pending",
  "counter_by": null,
  "can_counter": true,
  "counters": [
    {
      "id": "...",
      "sent_by": "...",
      "sent_by_username": "glow_lab",
      "deliverables": { },
      "timeline": "2025-02-20",
      "note": "Can we add one more story?",
      "round_number": 2,
      "created_at": "2025-01-29T12:00:00Z"
    }
  ],
  "created_at": "2025-01-28T10:00:00Z",
  "updated_at": "2025-01-28T10:00:00Z"
}
```

---

### `POST /api/proposals/:id/counter/` — **exists**

**Request:**

```json
{
  "deliverables": {
    "types": ["reel", "story"],
    "platforms": ["instagram"],
    "count": 2
  },
  "timeline": "2025-12-01",
  "note": "Adding one story frame"
}
```

**Response:** Updated `ProposalSerializer`.

**Mock ref:** `counter_offer_data.json`  
**Screen:** `counter_offer_screen.dart`

---

### `POST /api/proposals/:id/accept/` — **exists** (brand)

**Request:** `{}` (empty body)

**Response `200`:**

```json
{
  "message": "Proposal accepted successfully",
  "deal_id": "770e8400-e29b-41d4-a716-446655440030"
}
```

**Side effect:** Creates deal; status `active` or `pending_membership` per [P0](#13-p0-behaviour-changes-no-new-routes).

**Screen:** `review_proposal_screen.dart`

---

### `POST /api/proposals/:id/decline/` — **exists**

**Request:** `{}`  
**Response:** `{ "message": "Proposal declined successfully" }`

---

## 7. Deals & deal room

### `GET /api/deals/` — **exists**

**`results[]` (`DealListSerializer`):**

```json
{
  "id": "770e8400-e29b-41d4-a716-446655440030",
  "offer_title": "Glow Lab Serum Review",
  "brand_username": "glow_lab",
  "creator_username": "priya_lifestyle",
  "status": "active",
  "deal_fee": "1499.00",
  "currency": "INR",
  "deadline": "2025-02-15",
  "created_at": "2025-01-29T12:00:00Z"
}
```

**Note:** `deal_fee` remains in DB but is **not used** for gating (no payments).

---

### `GET /api/deals/:id/` — **exists**

**Response (`DealSerializer`) — backend today:**

```json
{
  "id": "770e8400-e29b-41d4-a716-446655440030",
  "offer": "550e8400-e29b-41d4-a716-446655440010",
  "offer_title": "Glow Lab Serum Review",
  "offer_type": "physical",
  "brand": "...",
  "brand_username": "glow_lab",
  "brand_name": "Glow Lab",
  "creator": "...",
  "creator_username": "priya_lifestyle",
  "creator_name": "Priya Sharma",
  "agreed_terms": { "offer_title": "...", "creator_deliverables": { }, "timeline": "2025-02-15" },
  "rights_tier": "standard",
  "raw_files_required": false,
  "exclusivity": "none",
  "deal_fee": "1499.00",
  "currency": "INR",
  "status": "active",
  "shipping_address": { "city": "Mumbai", "line1": "..." },
  "shipped_at": null,
  "delivered_at": null,
  "completed_at": null,
  "deadline": "2025-02-15",
  "contract_url": "",
  "latest_delivery": null,
  "revisions": [],
  "created_at": "2025-01-29T12:00:00Z",
  "updated_at": "2025-01-29T12:00:00Z"
}
```

**Target composite for Flutter `DealRoomModel`** (mapper builds from deal + messages; optional **NEW** `GET /api/deals/:id/room/`):

```json
{
  "deal_id": "770e8400-e29b-41d4-a716-446655440030",
  "brand_name": "Vanguard Global",
  "brand_logo_url": "https://...",
  "creator_avatar_url": "https://...",
  "terms_summary": "3x High-Res Editorial Posts + Story",
  "milestones": [
    { "id": "agreement", "label": "Agreement signed", "done": true },
    { "id": "ship", "label": "Product shipped", "done": false },
    { "id": "deliver", "label": "Content delivered", "done": false },
    { "id": "complete", "label": "Deal complete", "done": false }
  ],
  "days_remaining": 4,
  "agreement_date_label": "Agreement finalized Oct 24, 2025",
  "messages": []
}
```

**Mock ref:** `deal_room.json` (mock has extra: `pinnedAssets`, `deliverables[]` with status — **P2** UI enhancement; not in current `DealRoomModel`)

**Screen:** `deal_room_screen.dart`

---

### `GET /api/deals/:id/messages/` — **exists**

**`results[]` (`DealMessageSerializer`):**

```json
{
  "id": "880e8400-e29b-41d4-a716-446655440040",
  "sender": "550e8400-e29b-41d4-a716-446655440099",
  "sender_username": "glow_lab",
  "sender_name": "Glow Lab",
  "body": "Excited to have you on board!",
  "attachment_url": "",
  "created_at": "2025-01-29T10:00:00Z",
  "read_at": null,
  "is_read": false
}
```

Flutter maps: `from` ← `sender_name`, `text` ← `body`, `time` ← formatted `created_at`, `avatarUrl` ← sender profile photo (add `sender_profile_photo_url` on serializer **recommended**).

---

### `POST /api/deals/:id/messages/send/` — **exists**

**Request:**

```json
{
  "body": "Rooftop garden sounds amazing — approved!",
  "attachment_url": ""
}
```

**Response `201`:** `DealMessageSerializer` object.

---

### `POST /api/deals/:id/ship/` — **exists**

**Request:**

```json
{
  "shipping_address": {
    "name": "Priya Sharma",
    "line1": "12 MG Road",
    "city": "Bangalore",
    "state": "Karnataka",
    "postal_code": "560001",
    "country": "IN",
    "phone": "+919876543210"
  }
}
```

**Screen:** `shipping_address_entry_screen.dart`, `shipping_status_screen.dart`

---

### `POST /api/deals/:id/confirm-receipt/` — **exists**

**Request:** `{}`  
**Screen:** `shipping_status_screen.dart` (creator confirms product received)

---

### `POST /api/deals/:id/deliver/` — **exists**

**Request:**

```json
{
  "files": ["https://cdn.example/raw1.mp4"],
  "post_urls": ["https://www.instagram.com/reel/abc123/"],
  "notes": "Draft reel attached"
}
```

**Screen:** Creator deliver flow / `review_content_screen.dart`

---

### `POST /api/deals/:id/approve/` — **exists** (brand)

**Request:** `{}`  
**Screen:** `review_content_screen.dart` (brand)

---

### `POST /api/deals/:id/request-revision/` — **exists**

**Request:**

```json
{
  "reason": "Please reshoot with natural light; current grade is too warm."
}
```

**Screen:** `request_revision_screen.dart`

---

### `POST /api/deals/:id/complete/` — **exists**

**Request:** `{}`

---

### `POST /api/deals/:id/dispute/` — **exists**

**Request:** `{}` (no body fields today)

**Response `200`:**

```json
{
  "message": "Deal marked as disputed, admin notified"
}
```

---

## 8. Membership (subscription / Pro)

### `GET /api/membership/status/` — **exists** (extend — P0)

**Current response:**

```json
{
  "total_points": 30,
  "pro_active": false,
  "pro_expires_at": null,
  "pro_days_remaining": 0,
  "tier": "micro",
  "tasks_this_period": {},
  "period_reset_at": "2025-02-01T00:00:00Z"
}
```

**Target response** (match mock `membership.json` → `status`):

```json
{
  "total_points": 30,
  "pro_active": false,
  "pro_expires_at": null,
  "pro_days_remaining": 0,
  "tier": "micro",
  "tasks_this_period": { "task-uuid-1": "2025-01-15" },
  "period_reset_at": "2025-02-01T00:00:00Z",
  "pending_verification": false,
  "points_to_next_milestone": 20,
  "period_label": "month",
  "period_task_limit": 3,
  "completed_this_period": 1,
  "next_milestone_label": "1 month Pro",
  "history": [
    {
      "title": "Welcome bonus",
      "date": "2024-11-01",
      "points": 30
    }
  ]
}
```

**Optional combined endpoint:**

`GET /api/membership/` → `{ "status": { ... }, "tasks": [ ... ] }`

**Screens:** `earn_membership_screen.dart`, `membership_gate.dart`, `offer_detail_screen.dart`

---

### `GET /api/membership/tasks/` — **exists** (extend — P0)

**Current `results[]`:**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440050",
  "brand_name": "Barter",
  "brand_logo_url": "https://...",
  "title": "Post a Reel or TikTok about Barter",
  "platform": "open",
  "points_value": 100,
  "brief_richtext": "Create a short-form video...",
  "required_tags": ["@barter", "#BarterCollab"],
  "is_featured": true,
  "available_to_tiers": ["nano", "micro", "mid"],
  "available_to_markets": ["IN"],
  "created_at": "2024-11-01T08:00:00Z"
}
```

**Target `results[]`** (match mock `tasks[]`; Flutter uses `points` alias):

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440050",
  "brand_name": "Barter",
  "brand_logo_url": "https://...",
  "title": "Post a Reel or TikTok about Barter",
  "platform": "open",
  "points_value": 100,
  "points": 100,
  "is_featured": true,
  "is_available": true,
  "available_again_on": null,
  "brief": {
    "what_to_create": "Create a short-form video explaining what Barter is...",
    "key_messages": ["Barter helps creators collaborate without cash fees"],
    "donts": ["Do not imply guaranteed deal acceptance"],
    "required_tags": ["@barter", "#BarterCollab"],
    "example_url": "https://barter.example/briefs/barter-reel"
  },
  "brief_richtext": "...(fallback plain text)...",
  "required_tags": ["@barter", "#BarterCollab"]
}
```

**Seed data:** All task `id` values must be **UUIDs**, not `barter-reel`.

---

### `GET /api/membership/tasks/:id/brief/` — **exists**

Returns `MembershipTaskBriefSerializer` — align `brief` object as above.

---

### `POST /api/membership/submissions/` — **exists**

**Request:**

```json
{
  "task": "550e8400-e29b-41d4-a716-446655440050",
  "post_url": "https://www.instagram.com/reel/DDxyz123/",
  "note": "Posted as part of morning routine reel"
}
```

**Response `201`:**

```json
{
  "id": "...",
  "task": "...",
  "task_title": "Post a Reel or TikTok about Barter",
  "task_brand": "Barter",
  "task_points": 100,
  "post_url": "https://...",
  "note": "...",
  "status": "pending",
  "rejection_reason": "",
  "points_awarded": 0,
  "submitted_at": "2025-01-20T12:00:00Z",
  "reviewed_at": null
}
```

**Screen:** `submit_task_screen.dart`

---

## 9. Drops

Maps to **Drops campaigns** (not the same as mock `drops_campaign_data.json` marketing campaigns — UI conflates names; API `DropsCampaign` links to an `offer`).

### `GET /api/drops/` — **exists**

**`results[]`:**

```json
{
  "id": "990e8400-e29b-41d4-a716-446655440060",
  "brand": "...",
  "brand_username": "glow_lab",
  "brand_name": "Glow Lab",
  "offer": "550e8400-e29b-41d4-a716-446655440010",
  "name": "Summer Glow Drops",
  "goal": "Acquire 50 micro-creators for serum trial",
  "total_slots": 50,
  "filled_slots": 12,
  "approval_mode": "manual",
  "application_deadline": "2025-08-31T23:59:59Z",
  "status": "live",
  "application_count": 28,
  "created_at": "2025-06-01T08:00:00Z"
}
```

**Screen:** `drops_dashboard_screen.dart`

---

### `POST /api/drops/` — **exists**

**Request:**

```json
{
  "offer": "550e8400-e29b-41d4-a716-446655440010",
  "name": "Summer Glow Drops",
  "goal": "50 creators for product trial",
  "total_slots": 50,
  "approval_mode": "manual",
  "application_deadline": "2025-08-31T23:59:59Z"
}
```

**Screen:** `create_drops_campaign_screen.dart`

---

### `POST /api/drops/:id/apply/` — **exists** (creator)

**Request:**

```json
{
  "campaign": "990e8400-e29b-41d4-a716-446655440060",
  "pitch": "I'd love to join — my audience matches skincare 25-34."
}
```

---

### `GET /api/drops/:id/applications/` — **exists** (extend)

**Query:** `status=pending`

**`results[]` — add for review UI:**

```json
{
  "id": "...",
  "campaign": "...",
  "campaign_name": "Summer Glow Drops",
  "creator": "...",
  "creator_username": "priya_lifestyle",
  "creator_name": "Priya Sharma",
  "creator_profile_photo_url": "https://...",
  "pitch": "...",
  "status": "pending",
  "deal": null,
  "applied_at": "2025-06-10T10:00:00Z",
  "reviewed_at": null
}
```

**Screen:** `review_applications_screen.dart`

---

## 10. Brand dashboard, discovery, inbox, pipeline

### `GET /api/brands/dashboard/` — **NEW (P1)**

**Response** (match `brand_dashboard_data.json`):

```json
{
  "dashboard": {
    "greeting": "Welcome back, Riya",
    "kpis": {
      "active_campaigns": 4,
      "pending_proposals": 12,
      "deals_in_progress": 5,
      "total_reach_this_month": 3200000,
      "avg_engagement_rate": 5.2,
      "barter_value_delivered": 142000
    },
    "recent_activity": [
      {
        "id": "act_001",
        "type": "proposal",
        "title": "New proposal received",
        "subtitle": "Priya Sharma applied to Spring Glow Collection Launch",
        "timestamp": "2025-01-20T14:02:00Z",
        "route": "/brand/review/proposal",
        "avatar_url": "https://...",
        "urgent": true,
        "entity_id": "660e8400-e29b-41d4-a716-446655440020"
      }
    ]
  }
}
```

Use ISO timestamps in API; Flutter formats as `"2 min ago"`.

**Screen:** `brand_dashboard_screen.dart`

---

### `GET /api/brands/inbox/` — **NEW (P1)**

**Response** (match `brand_discovery_data.json` → `inbox`):

```json
{
  "conversations": [
    {
      "id": "conv_001",
      "creator_id": "550e8400-e29b-41d4-a716-446655440000",
      "creator_name": "Priya Sharma",
      "creator_avatar": "https://...",
      "campaign_title": "Spring Glow Collection Launch",
      "last_message": "Hi! I had a quick question about deliverable format...",
      "last_message_time": "2025-01-20T14:18:00Z",
      "unread": true,
      "deal_id": "770e8400-e29b-41d4-a716-446655440030",
      "messages": [
        {
          "id": "m1",
          "sender": "creator",
          "body": "Hey! So excited to work on this campaign.",
          "created_at": "2025-01-20T10:02:00Z"
        }
      ]
    }
  ]
}
```

**Screen:** `brand_inbox_screen.dart`

---

### `GET /api/brands/pipeline/` — **NEW (P1, optional)**

**Response** (match `pipeline.json` column structure):

```json
{
  "columns": [
    {
      "id": "applied",
      "title": "Applied",
      "accent_hex": "#b3193d",
      "cards": [
        {
          "id": "card_001",
          "proposal_id": "660e8400-e29b-41d4-a716-446655440020",
          "deal_id": null,
          "creator_name": "Priya Sharma",
          "creator_username": "priya_lifestyle",
          "offer_title": "Aura Collective — Spring Glow Reel",
          "tags": ["Beauty", "Instagram"],
          "brand_initial": "A",
          "barter_value": "12000.00",
          "currency": "INR",
          "applied_at": "2025-01-18T10:00:00Z"
        }
      ]
    },
    {
      "id": "shortlisted",
      "title": "Shortlisted",
      "accent_hex": "#3e5d8b",
      "cards": []
    },
    {
      "id": "negotiating",
      "title": "Negotiating",
      "accent_hex": "#c47800",
      "cards": []
    },
    {
      "id": "active",
      "title": "Active Deals",
      "accent_hex": "#1a5e3a",
      "cards": []
    },
    {
      "id": "completed",
      "title": "Completed",
      "accent_hex": "#4b5563",
      "cards": []
    }
  ],
  "status_mapping": {
    "proposal_pending": "applied",
    "proposal_countered": "negotiating",
    "deal_active": "active",
    "deal_complete": "completed"
  }
}
```

**Screen:** `deal_pipeline_screen.dart`

---

### `GET /api/users/me/` + brand profile aggregate — **alternative to dashboard**

For `brand_profile_data.json`, compose:

| Mock field | API source |
|------------|------------|
| `brand.name` | `brand_profile.company_name` or `user.name` |
| `brand.stats.activeCampaigns` | Count `offers` where `status=live` |
| `brand.activeCampaignPreviews[]` | `GET /api/offers/my/` mapped to previews |
| `brand.recentCollaborations[]` | Completed deals + ratings |

**Target `GET /api/brands/profile/` (optional NEW):

```json
{
  "brand": {
    "id": "...",
    "name": "Aura Collective",
    "tagline": "From user.bio",
    "logo_url": "...",
    "cover_url": "...",
    "website": "...",
    "industry": "...",
    "location": "Mumbai, India",
    "founded": "",
    "verified": true,
    "description": "...",
    "niches": [],
    "stats": {
      "active_campaigns": 4,
      "total_collaborations": 87,
      "avg_barter_value": 8500,
      "creators_worked_with": 63,
      "total_reach": 12400000,
      "avg_engagement_rate": 5.2
    },
    "barter_score": {
      "overall": 94,
      "payment_reliability": 98,
      "communication": 92,
      "brief_clarity": 91,
      "repeat_rate": 76,
      "label": "Elite Partner"
    },
    "badges": [],
    "active_campaign_previews": [],
    "recent_collaborations": [],
    "team": []
  }
}
```

---

## 11. Analytics

### `GET /api/analytics/deals/` — **exists** (brand)

**Current response:**

```json
{
  "total_deals": 142,
  "active_deals": 44,
  "completed_deals": 98,
  "disputed_deals": 2,
  "completion_rate": 69.01,
  "avg_deal_value": 12500.5,
  "deals_by_status": [
    { "status": "active", "count": 44 },
    { "status": "complete", "count": 98 }
  ],
  "recent_deals_30_days": 12,
  "deals_over_time": [
    { "month": "2025-01-01T00:00:00Z", "count": 8 }
  ]
}
```

**Target extension** (match `analytics.json` KPI strip — Flutter `AnalyticsPayload` minimum):

```json
{
  "kpis": [
    { "id": "deals", "label": "Total Deals", "value": "142", "trend_label": "+12%", "trend_up": true },
    { "id": "completed", "label": "Completed", "value": "98", "trend_label": "44 Active", "trend_up": null },
    { "id": "value", "label": "Est. Barter Value", "value": "1240000", "value_suffix": null, "trend_label": null, "trend_up": null, "progress": null }
  ],
  "reach_chart_title": "Monthly Reach",
  "reach_chart": [
    { "month": "2025-01", "reach": 3200000 }
  ],
  "engagement_chart": [
    { "month": "2025-01", "rate": 5.2 }
  ],
  "platform_breakdown": [
    { "platform": "instagram", "share": 0.54, "reach": 1728000, "deals": 76 }
  ],
  "content_performance_title": "Content Performance",
  "content_performance": [
    {
      "id": "cp_001",
      "creator_name": "Priya Sharma",
      "creator_avatar": "https://...",
      "campaign_title": "Spring Glow Collection",
      "platform": "instagram",
      "content_type": "reel",
      "reach": 420000,
      "engagement_rate": 6.1,
      "clicks": 3200,
      "conversions": 148,
      "barter_value": "12000.00",
      "currency": "INR",
      "posted_date": "2024-11-10"
    }
  ],
  "top_creators": [
    { "rank": 1, "name": "Priya Sharma", "deals": 8, "total_reach": 1240000, "avg_rating": 5.0 }
  ]
}
```

**Screens:** `analytics_dashboard_screen.dart`

---

### `GET /api/analytics/creators/` · `GET /api/analytics/content/` — **exist**

Extend similarly if brand analytics UI uses creator/content tabs (see admin_panel views).

---

## 12. Notifications, ratings, contracts

### `GET /api/notifications/` — **exists**

**`results[]`:**

```json
{
  "id": "aa0e8400-e29b-41d4-a716-446655440070",
  "type": "proposal_received",
  "title": "New Proposal Received",
  "body": "Priya Sharma sent a proposal for Glow Lab Serum Review",
  "deep_link": "/offers/550e8400-e29b-41d4-a716-446655440010/proposals/660e8400-e29b-41d4-a716-446655440020",
  "read": false,
  "created_at": "2025-01-20T14:02:00Z"
}
```

**Target:** Add `unread_count` on list response wrapper or `GET /api/notifications/unread-count/`.

**deep_link conventions for Flutter router:**

| Event | deep_link |
|-------|-----------|
| Proposal | `/brand/review/proposal?proposalId=<uuid>` |
| Deal | `/deal/<deal_id>` |
| Membership | `/creator/membership/earn` |

**Screen:** `notifications_center_screen.dart`

---

### `POST /api/ratings/:deal_id/rate/` — **exists**

**Request:**

```json
{
  "stars": 5,
  "review_text": "Excellent collaboration, clear brief and fast approvals."
}
```

**Requires:** deal `status` = `complete`.

**Screen:** `rate_close_deal_screen.dart`, `rate_colleague_screen.dart`

---

### `GET /api/contracts/:deal_id/contract/` — **exists**

**Response:** PDF file or `{ "contract_url": "https://..." }`  
**Screen:** `deal_room_screen.dart`, `deal_brief_screen.dart`

---

## 13. P0 behaviour changes (no new routes)

### Deal activation without payments

When proposal accepted:

- If `creator.membership.pro_active === true` → deal `status: "active"`
- Else → `"pending_membership"` until Pro earned → then bulk update to `"active"`

On `membership.check_pro_eligibility()` when `pro_active` becomes true:

```python
Deal.objects.filter(creator=user, status='pending_membership').update(status='active')
```

**403 when deal not active:**

```json
{
  "detail": "Deal is pending membership. Earn Pro to activate."
}
```

### Accept proposal response (unchanged shape)

```json
{
  "message": "Proposal accepted successfully",
  "deal_id": "770e8400-e29b-41d4-a716-446655440030"
}
```

---

## 14. Out of scope

| Area | Reason |
|------|--------|
| `POST /api/payments/create-deal-fee/` | No payment gateway |
| `gateway` on any payment body | N/A |
| Wallet / transfers | Not in UI |
| Brand SaaS subscription billing | Future; membership points = creator Pro |

---

## 15. Implementation order & files

| Priority | Item | JSON section |
|----------|------|----------------|
| P0 | Deal activation vs Pro | §13 |
| P0 | Membership status + task `brief` | §8 |
| P1 | `GET /api/config/onboarding/` | §4 (new) |
| P1 | Offer list enrichment | §5 |
| P1 | Proposal inbox expand | §6 |
| P1 | Brand dashboard / inbox / pipeline | §10 |
| P1 | Creator list computed fields | §4 |
| P2 | Analytics full mock shape | §11 |
| P2 | Notifications unread + deep_links | §12 |
| P2 | Deal room extras (assets) | §7 |

| App | Files |
|-----|--------|
| `membership` | `models.py`, `serializers.py`, migrations |
| `deals` | `models.py`, `views.py` |
| `offers` | `serializers.py` |
| `proposals` | `serializers.py`, `views.py` |
| `users` | `views.py`, `serializers.py` |
| new `brands` or `config` | `urls.py`, `views.py`, `serializers.py` |
| `barter/urls.py` | include new routes |

---

## Appendix: Mock file field naming

| Mock (camelCase) | API (snake_case) |
|------------------|-------------------|
| `brandName` | `brand_name` |
| `brandLogoUrl` | `brand_logo_url` |
| `estimatedValueLabel` | Computed client-side from `estimated_value` + `currency` |
| `pro_active` | `pro_active` (same) |
| `points_value` / `points` | `points_value` (expose both for compatibility) |
| `dealId` | `id` on deal resources |
| `creatorAvatarUrl` | `creator_profile_photo_url` on deal room composite |

Flutter repositories/mappers perform this mapping; backend should stay snake_case per DRF convention.

---

*Last updated: full JSON contracts cross-checked against `barter_app/assets/mock/*` and feature screens.*
