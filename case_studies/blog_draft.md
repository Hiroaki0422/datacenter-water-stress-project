# What 1,575 data centers are doing to US water

*A first estimate, with all assumptions published. A Water Stress Watch v0 blog post.*

**Last updated:** 2026-07-04
**Reading time:** ~6 minutes
**Author:** Hiroaki Oshima (project), with assistance from Hermes Agent (writing/editing)

---

When a data center moves into a county, the local press usually covers the **electricity** story: how much power it will draw, who's selling it, what the ratepayer impact is. The **water** story is rarer, even though hyperscale data centers can use millions of liters per day.

The reason isn't that the data is private. It's that **the data doesn't exist publicly** in the first place. There is no federal requirement for US data centers to report per-facility water use. Operators disclose at their discretion, in sustainability reports, in non-comparable units. State-level reporting is patchy. Local utilities publish system-wide consumption but not by customer class.

This is the transparency gap that [Water Stress Watch v0](https://github.com/...) (this project) is a first attempt to close. Below is what the v0 estimate says, with all assumptions published, and what it means for the next decade of data center growth in the United States.

## The headline number

**US data centers use an estimated 237 billion liters of water per year** (0.65 B L/day), based on a single physics formula applied to 1,575 known facilities.

That number has a published ±50% uncertainty band, dominated by the cooling-type unknown. Real cooling choices range from air-cooled (WUE ~0.2 L/kWh) to water-cooled evaporative (WUE ~2.7 L/kWh) — a 13× spread. Our estimate assumes the industry-average midpoint of 0.7×.

The implied average WUE works out to **~1.2 L/kWh** — a sanity check that lines up with Google and Microsoft's 2024 disclosed averages.

## Where the data centers are

The v0 map ([`assets/map_v0.html`](../assets/map_v0.html)) shows the 1,575 facilities overlaid on a WRI Aqueduct state-level water-stress choropleth. The pattern is unmistakable.

Three things stand out:

**1. Loudoun County, Virginia is the data center capital of the world.** 134 of our 1,575 facilities (8.5%) are within an hour of Washington, DC. The fiber build-out, federal contracts, and Virginia's tax incentives created a 25-year head start. Its water stress is Low-Medium (WRI BWS 1.94) — not a "double jeopardy" state, but the absolute volume is unmatched.

**2. Texas is the second cluster.** 192 facilities, mostly in the Dallas-Fort Worth area. Texas offers cheap power, low regulation, and aggressive tax breaks. Water stress is Medium-High (BWS 2.68).

**3. California and Arizona are the stress case.** California has 226 facilities (BWS 3.72, High). Arizona has 70 (BWS 3.49, High). These are the states where water use is competing with the basin's renewable supply.

If you sort states by **stress-weighted demand** (BWS × total est. L/day), Arizona jumps from 4th by absolute volume to **#1**. The 22.4 B L/year we estimate for AZ is small in the state's overall water budget, but it's concentrated in a single metro area that's already under federal Colorado River cuts.

## The Phoenix story, briefly

Phoenix has 70 known data centers with an estimated 2,896 MW of total nameplate. Our model estimates they use **22.4 billion liters of water per year** — about 1% of Arizona's total water demand, all concentrated in the Phoenix metro.

The biggest single facility in our dataset is **NFINIT's Van Buren campus** in Phoenix: 781 MW nameplate, estimated **16.5 million liters per day**. That's the daily water use of a town of 100,000.

Phoenix's water comes from a shrinking Colorado River, a regulated Salt/Verde system, and increasingly depleted groundwater. The 2022 tier-1 shortage on the Colorado River required Arizona to cut its allocation by 18%, then 21%, with more cuts projected. Agricultural users have taken the largest cuts so far. Data centers — most of which use municipal water, not Colorado River water directly — have not.

The full Phoenix case study is at [`case_studies/phoenix_az.md`](../case_studies/phoenix_az.md). It includes a list of the 70 facilities, the 10 biggest, and the operators dominating the market.

## What's NOT in this estimate

Three things we are not claiming:

**1. We are not claiming the 237 B L/year number is precise.** It's a transparent first estimate. The ±50% band is published. The dominant uncertainty is the cooling-type unknown. If all new Phoenix builds are air-cooled, the growth scenario looks very different than if they're water-cooled evaporative.

**2. We are not claiming we know cooling type.** None of the operators disclose it. We assume the industry average. A v1 upgrade with disclosed cooling type would replace the ±50% band with a narrower range.

**3. We are not claiming our climate data is the right climate metric.** Open-Meteo's annual mean of daily wet-bulb temperature understates cooling stress because cool nights drag the mean down. Phoenix's annual mean is 12.5°C; the cooling-relevant design-day wet-bulb in summer is 24-26°C. The v0 climate adjustment is therefore ~1.0 for almost everywhere, including Arizona. v1 will use the 99th-percentile wet-bulb instead.

## What we'd need to do better

If I had three wishes for the data, they would be:

**1. Mandatory per-facility water-use disclosure.** Federal or state-level. Not a sustainability report — a public database, like the Toxics Release Inventory or the EIA's electricity generators. Without this, every estimate in the field is a model, including mine.

**2. Mandatory cooling-type disclosure.** Air vs. evaporative vs. water-cooled vs. immersion. The single biggest unknown in every WUE estimate is the cooling technology, and nobody publishes it.

**3. Open access to municipal utility data.** Phoenix Water Services publishes system-wide consumption, but not by customer class. If we knew what fraction of municipal water went to data centers, our 22.4 B L/year estimate could be replaced with a measurement.

The first two are policy choices. The third is a transparency choice that local utilities can make.

## Why this matters

I'm a data scientist who works in AI infrastructure. I see the asymmetry: operators have precise per-facility data on power and water; the public has nothing. I am not anti-AI, and I am not anti-data-center. I am pro-transparency.

The next decade of data center growth is a real policy question. The US is projected to add 30-50 GW of data center load by 2030, with a disproportionate share landing in already-stressed water regions. The people who have to live next to these facilities — in Phoenix, in Loudoun, in West Texas — deserve to know what their new neighbors are taking from the same aquifer.

The v0 release is one step. The map, the case study, and the underlying data are reusable with attribution. If you're a journalist, an advocate, a researcher, or a policymaker: the data is yours. Use it, scrutinize it, and tell us what we got wrong.

The methodology, citations, and reproducibility instructions are all in [`methodology.md`](../methodology.md). Every number in this post can be reproduced from the data and code in this repository.

— Hiroaki

---

*If you use this work, please cite the project. See `methodology.md` Section 14 for the citation format. Comments, corrections, and follow-up leads welcome.*
