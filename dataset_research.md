# Scheme catalogue research

## Data strategy

The application uses a locally stored catalogue checked against official Government of India and Karnataka portals, rather than a live web-search response for every query. A live search does not provide a complete official eligibility API and could mix unofficial, stale, or contradictory pages into a government-benefit answer.

Each catalogue record stores the official source links and the date it was researched. Scheme details that depend on the current Karnataka notification, annual guidelines, application window, or funding are intentionally not encoded as fixed rules.

## Stored programmes

1. **PM-KISAN** — existing central income-support programme entry.
2. **PMFBY / Karnataka Samrakshane** — existing crop insurance entry; crop/area notification and enrollment remain subject to official current confirmation.
3. **PMKSY — Per Drop More Crop** — real micro-irrigation programme. The official portal describes improving on-farm water-use efficiency through drip and sprinkler technology. No current Karnataka percentage/cap is asserted.
4. **Sub-Mission on Agricultural Mechanization (SMAM)** — real farm-machinery assistance programme. Official farm-mechanization portals describe support for machinery procurement; no universal current Karnataka rate, cap, list, or allocation is asserted.
5. **Soil Health Card Programme** — real soil testing and nutrient/fertilizer advisory service. It is not represented as a cash grant.

## Sources checked on 2026-10-30

- [PM-KISAN](https://pmkisan.gov.in/)
- [PMFBY](https://pmfby.gov.in/)
- [Karnataka Samrakshane](https://samrakshane.karnataka.gov.in/)
- [PMKSY Per Drop More Crop](https://pmksy.gov.in/microirrigation/index.aspx)
- [PMKSY Micro Irrigation guidelines](https://pmksy.gov.in/microirrigation/Guideline.aspx)
- [Government of India Farm Machinery DBT](https://agrimachinery.nic.in/)
- [Farm Mechanization DBT](https://farmech.dac.gov.in/)
- [Soil Health Card portal](https://soilhealth.dac.gov.in/)
- [Karnataka Raitha Mitra](https://raitamitra.karnataka.gov.in/)

## Scope and verification limitations

The catalogue is not a live check of application availability, beneficiary status, official land records, district crop notifications, current subsidies, or allocations. Before applying, farmers should follow the linked official portal or contact their district Agriculture/Horticulture Department or soil-testing facility. All frontend/backend statuses are informational and cannot be treated as official approval.
