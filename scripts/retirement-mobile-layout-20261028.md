# Retirement calculator responsive overflow correction

Owner reports intermittent page-wide horizontal panning, displaced header and clipped chart/table on mobile. Review found intrinsic grid tracks (`1fr`) and no shrink constraints on cards containing a five-column table and fixed 800-unit SVG. Content width could determine the track minimum rather than fitting the viewport. This is a layout correction; financial formulas are unchanged.

- Constrain outer tracks with minmax(0,...) and grid children with min-width:0.
- Keep table containers within card width rather than masking page overflow globally.
- In result panels <=600px wide display scenarios as labeled cards, retain table header/row associations in markup and keep yearly balances as a two-column table.
- Draw the SVG at the actual chart container width and observe width changes, including rotation. Label text remains readable instead of scaling an 800-unit chart down to phone width.
- Use one-column inputs and 44px / 16px input controls on phones.
- Bump both page-local asset URLs so CSS/JS are refreshed together. Shared header, aggregator, consent and financial formulas untouched.

Validation: existing independent cash-flow/formula/edge-case checks pass. Site integrity passes. Dedicated CI regression checks 320, 360, 390, 430, 600, 768, 850, 851, 1080 and 1440px in light/dark themes; initial load, changed values, input errors/reset, open navigation and rotation. Stores original-code 390px baseline and fixed screenshots for review. Live verification follows deployment. No claim of physical iPhone/Safari testing.

Initial CI reproduced the original 390px mobile layout expanding to 513 CSS px. Fixed widths 320 through 850 passed in both themes. CI additionally caught a five-column table at the 851px two-column breakpoint; switched scenario reflow to the actual result-panel width using a container query, covering narrow desktop columns as well as phones.
