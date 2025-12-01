# Mail Scanner Business - Cost Analysis & Scaling Model (2025)

## Executive Summary

This document provides a comprehensive cost analysis for the Mail Scanner application based on current API pricing (as of 2025). The application uses three primary paid services:
- **Gemini 2.5 Flash API** (image analysis)
- **Smarty API** (address verification)
- **Supabase** (database + authentication)

---

## Cost Components Breakdown

### 1. Gemini 2.5 Flash API (Image Analysis)

**Current Pricing:**
- Input: $0.30 per million tokens
- Output: $2.50 per million tokens
- **Free Tier:** 500 requests/day (15,000/month)

**Estimated Usage Per Mail Scan:**
- Average image: ~1,000-2,000 input tokens (depending on image size/resolution)
- Average response: ~200-400 output tokens (JSON structured output)
- **Cost per scan:** ~$0.0006 - $0.0012

**Conservative Estimate:** $0.001 per mail scan

---

### 2. Smarty Address Verification API

**Current Pricing:**
- Free tier: 250 lookups/month
- 500 lookups/month: $20
- 1,000 lookups/month: $40
- 5,000 lookups/month: $150
- 10,000 lookups/month: $250
- 25,000 lookups/month: $500
- 50,000 lookups/month: $900
- 100,000+ lookups/month: Custom pricing (~$0.008/lookup at scale)

**Cost Structure:**
- 0-250 scans: FREE
- 251-500 scans: $20/month = $0.040 per additional lookup
- 501-1,000 scans: $40/month = $0.040 per lookup
- 1,001-5,000 scans: $150/month = $0.030 per lookup
- 5,001-10,000 scans: $250/month = $0.025 per lookup
- 10,001-25,000 scans: $500/month = $0.020 per lookup
- 25,001-50,000 scans: $900/month = $0.018 per lookup
- 50,001-100,000 scans: Custom (~$0.010 per lookup)
- 100,000+ scans: Custom (~$0.008 per lookup)

---

### 3. Supabase (Database + Authentication)

**Plan Tiers:**

| Tier | Base Cost | Database | Storage | MAUs | Egress |
|------|-----------|----------|---------|------|--------|
| **Free** | $0/mo | 500 MB | 1 GB | 50,000 | 2 GB |
| **Pro** | $25/mo | 8 GB | 100 GB | 100,000 | 250 GB |

**Usage-Based Overage Costs (Pro Plan):**
- Database storage: $0.021/GB/month
- Storage egress: $0.09/GB (after 250 GB)
- Additional MAUs: $0.00325 per MAU (after 100,000)

**Database Storage Estimates:**
- Average record size: ~500 bytes (sender name, address, verification data)
- 1,000 scans = 0.5 MB
- 10,000 scans = 5 MB
- 100,000 scans = 50 MB
- 1,000,000 scans = 500 MB

**Monthly Active Users (MAUs):**
- Assumes 1 MAU can perform multiple scans
- If 100 users scan 500 items each = 50,000 scans

---

## Total Cost Per Mail Scan (By Volume)

### Scenario Analysis

| Monthly Volume | Gemini Cost | Smarty Cost | Supabase Cost | Total Monthly Cost | Cost Per Scan |
|----------------|-------------|-------------|---------------|-------------------|---------------|
| **100** | $0.10 | $0 (free) | $0 (free tier) | $0.10 | $0.0010 |
| **250** | $0.25 | $0 (free) | $0 (free tier) | $0.25 | $0.0010 |
| **500** | $0.50 | $20 | $0 (free tier) | $20.50 | $0.0410 |
| **1,000** | $1.00 | $40 | $0 (free tier) | $41.00 | $0.0410 |
| **2,500** | $2.50 | $150 | $0 (free tier) | $152.50 | $0.0610 |
| **5,000** | $5.00 | $150 | $25 (Pro) | $180.00 | $0.0360 |
| **10,000** | $10.00 | $250 | $25 (Pro) | $285.00 | $0.0285 |
| **25,000** | $25.00 | $500 | $25 (Pro) | $550.00 | $0.0220 |
| **50,000** | $50.00 | $900 | $25 (Pro) | $975.00 | $0.0195 |
| **100,000** | $100.00 | ~$1,000 | $25 (Pro) | $1,125.00 | $0.0113 |
| **250,000** | $250.00 | ~$2,000 | $25 (Pro) | $2,275.00 | $0.0091 |
| **500,000** | $500.00 | ~$4,000 | $25 (Pro) | $4,525.00 | $0.0091 |
| **1,000,000** | $1,000.00 | ~$8,000 | $36* | $9,036.00 | $0.0090 |

*Supabase cost increases slightly due to database storage overage (500 MB used, 8 GB included, no overage)

---

## Cost Curve Analysis

### Cost Per Scan by Volume

```
$0.045 |  •
       |
$0.040 |     •  •
       |
$0.030 |              •
       |
$0.020 |                    •     •
       |
$0.010 |                               •    •    •    •
       |
$0.000 +----+----+----+----+----+----+----+----+----+----+
       0   100  500  1K  2.5K  5K  10K  25K  50K 100K 500K 1M
                    Monthly Scans
```

**Key Insights:**
1. **Break-even sweet spot:** 25,000-50,000 scans/month (~$0.020 per scan)
2. **Economies of scale:** Cost per scan drops 90% from 500 to 100,000 scans
3. **Free tier advantage:** Up to 250 scans/month costs only $0.001 per scan
4. **Smarty dominates costs:** At low-medium volumes, Smarty is 95%+ of total cost

---

## Monthly Total Cost Curve

| Volume | Total Monthly Cost |
|--------|-------------------|
| 100 | $0.10 |
| 250 | $0.25 |
| 500 | $20.50 |
| 1,000 | $41.00 |
| 2,500 | $152.50 |
| 5,000 | $180.00 |
| 10,000 | $285.00 |
| 25,000 | $550.00 |
| 50,000 | $975.00 |
| 100,000 | $1,125.00 |
| 250,000 | $2,275.00 |
| 500,000 | $4,525.00 |
| 1,000,000 | $9,036.00 |

---

## Revenue & Pricing Scenarios

### Option 1: Subscription Model

**Pricing Tiers:**

| Plan | Monthly Fee | Included Scans | Overage Rate | Target Margin |
|------|-------------|----------------|--------------|---------------|
| **Starter** | $49/mo | 500 scans | $0.10/scan | 139% |
| **Professional** | $149/mo | 2,500 scans | $0.08/scan | 2% |
| **Business** | $349/mo | 10,000 scans | $0.06/scan | 22% |
| **Enterprise** | $999/mo | 50,000 scans | $0.04/scan | 2% |

**Break-Even Analysis:**
- Starter: Profitable at full usage (500 scans)
- Professional: Profitable at full usage (2,500 scans)
- Business: Profitable at 80%+ usage (8,000+ scans)
- Enterprise: Profitable at 95%+ usage (47,500+ scans)

---

### Option 2: Pay-Per-Scan Model

| Pricing Tier | Price Per Scan | Cost Per Scan | Margin | Min Monthly Revenue |
|--------------|----------------|---------------|--------|---------------------|
| **Retail** | $0.15/scan | $0.0410 | 73% | - |
| **Volume** (5K+) | $0.10/scan | $0.0360 | 64% | $500 |
| **Enterprise** (50K+) | $0.05/scan | $0.0195 | 61% | $2,500 |

---

### Option 3: Freemium Model

- **Free Tier:** 50 scans/month (cost: $2.05/user)
- **Pro Tier:** $19/mo for 500 scans (profit: -$1.50 at full usage)
- **Business Tier:** $99/mo for 5,000 scans (profit: -$81 at full usage)

**Note:** Freemium model requires higher-volume tiers or additional features to be profitable.

---

## Cost Optimization Strategies

### 1. Reduce Gemini Costs (Low Priority)
- **Switch to Gemini 2.5 Flash-Lite:** Saves ~67% ($0.0003 vs $0.001 per scan)
- **Trade-off:** Lower accuracy for mail analysis
- **Recommendation:** NOT recommended - Gemini cost is minimal

### 2. Reduce Smarty Costs (HIGH PRIORITY)
- **Option A - Make Verification Optional:**
  - Basic tier: No verification (save $0.040/scan at low volumes)
  - Premium tier: With verification
  - Potential savings: 90%+ at low volumes

- **Option B - Negotiate Custom Pricing:**
  - Contact Smarty for volume discounts at 100K+ lookups/month
  - Potential cost: $0.005-$0.008 per lookup (vs current $0.008-$0.010)

- **Option C - Alternative Verification APIs:**
  - USPS API: Free but limited functionality
  - Geocodio: $0.50 per 1,000 lookups ($0.0005/lookup) - 94% cheaper!
  - Trade-off: May have lower accuracy than Smarty

### 3. Optimize Supabase Usage
- **Stay on Free tier** until 50K MAUs or 500 MB database (500K+ scans)
- **Database cleanup:** Archive or delete old scans periodically
- **Estimated savings:** $25/month until scale

### 4. Batch Processing
- Process images in batches to optimize API calls
- Current implementation already optimized (in-memory processing)

---

## Recommended Strategy

### Phase 1: Launch (0-1,000 users/month)
- **Pricing:** $49/mo for 500 scans, $0.10 per additional scan
- **Infrastructure:** Free tier Gemini + Smarty + Supabase
- **Target Margin:** 60-70%
- **Monthly Revenue Target:** $2,500 (50 customers)
- **Monthly Costs:** ~$200 (25,000 total scans)
- **Net Profit:** ~$2,300/month

### Phase 2: Growth (1,000-10,000 users/month)
- **Pricing:** $99/mo for 2,500 scans, $0.08 per additional scan
- **Infrastructure:** Pro tier Supabase, negotiate Smarty rates
- **Target Margin:** 50-60%
- **Monthly Revenue Target:** $25,000 (250 customers)
- **Monthly Costs:** ~$9,000 (100,000 total scans)
- **Net Profit:** ~$16,000/month

### Phase 3: Scale (10,000+ users/month)
- **Pricing:** Custom enterprise pricing
- **Infrastructure:** Optimized APIs, potential Geocodio switch, custom Smarty contract
- **Target Margin:** 60-70%
- **Monthly Revenue Target:** $100,000+ (1,000+ customers)
- **Monthly Costs:** ~$30,000 (1M total scans with optimizations)
- **Net Profit:** ~$70,000/month

---

## Risk Analysis

### High-Risk Cost Drivers
1. **Smarty API:** Makes up 80-95% of costs at low-medium volumes
   - **Mitigation:** Offer non-verified tier, negotiate volume discounts, or switch to Geocodio

2. **Unexpected Scaling:** Costs increase linearly with usage
   - **Mitigation:** Implement rate limiting, usage caps, prepaid credits

3. **Free Tier Abuse:** Users staying on free tier
   - **Mitigation:** Strict limits (50-100 scans/month free tier)

### Medium-Risk Cost Drivers
1. **Supabase MAU costs:** If many users with low scan volumes
   - **Mitigation:** Stay on free tier until 50K MAUs

2. **Image storage:** Currently not storing images (good!)
   - **Mitigation:** Continue in-memory processing only

---

## Appendix: Detailed Calculation Formulas

### Cost Per Scan Formula
```
Total Cost Per Scan = Gemini Cost + Smarty Cost + (Supabase Monthly Cost / Total Scans)

Where:
- Gemini Cost = (Avg Input Tokens × $0.30/1M) + (Avg Output Tokens × $2.50/1M)
- Smarty Cost = Tiered based on volume (see pricing table)
- Supabase Cost = $0 (free tier) or $25/mo + overages (Pro tier)
```

### Break-Even Price Formula
```
Break-Even Price = (Total Monthly Costs / Expected Monthly Scans) × (1 + Desired Margin %)

Example for 5,000 scans/month:
- Total Cost = $180
- Desired Margin = 60%
- Break-Even Price = ($180 / 5,000) × 1.60 = $0.0576 per scan
```

### Minimum Customer Formula
```
Min Customers = Fixed Costs / (Price Per Customer - Variable Cost Per Customer)

Example for $49/mo plan (500 scans):
- Fixed Costs = $0 (infrastructure scales with usage)
- Price Per Customer = $49
- Variable Cost Per Customer = $20.50 (for 500 scans)
- Min Customers = 0 / (49 - 20.50) = 0 (no fixed costs!)
```

---

## Conclusion

The Mail Scanner business has **favorable unit economics** with the ability to be profitable from Day 1:

**Key Takeaways:**
1. **Low initial costs:** Can start with $0-$200/month on free tiers
2. **Healthy margins:** 60-70% margins achievable at all scales
3. **Main cost driver:** Smarty API verification (consider alternatives)
4. **Scalability:** Costs scale linearly and predictably
5. **Optimization potential:** Can reduce costs by 50%+ by switching address verification providers

**Recommended Next Steps:**
1. Launch with $49/mo tier (500 scans) to validate market
2. Monitor actual usage patterns vs. estimates
3. Negotiate Smarty volume discounts or test Geocodio alternative
4. Consider offering non-verified tier at lower price point
5. Add premium features (bulk exports, integrations) to increase ARPU
